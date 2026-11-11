"""Pruebas de la conexión con Claude, sin red: la API se simula."""

import json
from datetime import datetime

import pytest

anthropic = pytest.importorskip("anthropic")
httpx = pytest.importorskip("httpx2")

from jarvis import Jarvis  # noqa: E402
from jarvis.brain import ClaudeBrain  # noqa: E402
from jarvis.expenses import ExpenseBook  # noqa: E402


def _msg(content, stop_reason="end_turn"):
    return {"id": "msg_1", "type": "message", "role": "assistant", "model": "claude-opus-5-5",
            "content": content, "stop_reason": stop_reason, "stop_sequence": None,
            "usage": {"input_tokens": 10, "output_tokens": 5}}


class FakeAPI:
    """Transporte HTTP que responde con una secuencia de mensajes predefinidos."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.requests = []

    def __call__(self, request):
        self.requests.append(json.loads(request.content))
        return httpx.Response(200, json=self.replies.pop(0))


def make_jarvis(tmp_path, replies):
    api = FakeAPI(replies)
    client = anthropic.Anthropic(api_key="test", max_retries=0,
                                 http_client=anthropic.DefaultHttpxClient(transport=httpx.MockTransport(api)))
    j = Jarvis(data_dir=tmp_path, clock=lambda: datetime(2026, 10, 15, 13, 0), brain=False)
    j.brain = ClaudeBrain(j.ctx, j.run_command, client=client)
    j.ctx.extras["brain"] = j.brain
    return j, api


def test_fixed_commands_do_not_call_claude(tmp_path):
    j, api = make_jarvis(tmp_path, [])
    assert "Comida" in j.handle("gasté 20 en pizza")
    assert api.requests == []


def test_claude_registers_free_form_expenses(tmp_path):
    j, api = make_jarvis(tmp_path, [
        _msg([{"type": "thinking", "thinking": "", "signature": "sig"},
              {"type": "tool_use", "id": "tu_1", "name": "registrar_gasto",
               "input": {"monto": 300, "descripcion": "almuerzo con ana", "categoria": "Comida"}},
              {"type": "tool_use", "id": "tu_2", "name": "registrar_gasto",
               "input": {"monto": 200, "descripcion": "uber", "categoria": "Transporte"}}],
             stop_reason="tool_use"),
        _msg([{"type": "text", "text": "Anoté 300 de almuerzo y 200 de uber."}]),
    ])
    out = j.handle("ayer almorcé con Ana, pagué la mitad de 600, y luego 200 de uber")
    assert out == "Anoté 300 de almuerzo y 200 de uber."

    gastos = ExpenseBook(tmp_path).all()
    assert [(g.monto, g.categoria) for g in gastos] == [(300, "Comida"), (200, "Transporte")]

    first, second = api.requests
    assert first["model"] == "claude-opus-5-5"
    assert first["fallbacks"] == "default"
    assert first["output_config"] == {"effort": "low"}
    assert {t["name"] for t in first["tools"]} == {"registrar_gasto", "ejecutar_comando"}
    # el segundo turno reenvía el razonamiento y devuelve ambos resultados juntos
    assert second["messages"][1]["content"][0]["type"] == "thinking"
    results = second["messages"][2]["content"]
    assert [r["tool_use_id"] for r in results] == ["tu_1", "tu_2"]
    assert all(r["is_error"] is False for r in results)


def test_multi_amount_phrase_goes_to_claude(tmp_path):
    j, api = make_jarvis(tmp_path, [_msg([{"type": "text", "text": "Hecho."}])])
    assert j.handle("gasté 300 en comida y 200 en uber") == "Hecho."
    assert len(api.requests) == 1


def test_claude_can_run_any_command(tmp_path):
    j, api = make_jarvis(tmp_path, [
        _msg([{"type": "tool_use", "id": "tu_1", "name": "ejecutar_comando",
               "input": {"frase": "qué hora es"}}], stop_reason="tool_use"),
        _msg([{"type": "text", "text": "Es la una de la tarde."}]),
    ])
    assert j.handle("¿me dices si ya es hora de almorzar?") == "Es la una de la tarde."
    tool_result = api.requests[1]["messages"][-1]["content"][0]
    assert tool_result["content"] == "Son las 13:00."
    # los comandos registrados aparecen en la descripción de la herramienta
    desc = next(t for t in api.requests[0]["tools"] if t["name"] == "ejecutar_comando")["description"]
    assert "reporte mensual" in desc and "señal de trading" in desc


def test_conversation_memory_and_reset(tmp_path):
    j, api = make_jarvis(tmp_path, [_msg([{"type": "text", "text": "Hola Fermín."}]),
                                    _msg([{"type": "text", "text": "Te llamas Fermín."}])])
    j.handle("me llamo Fermín")
    j.handle("¿cómo me llamo?")
    assert len(api.requests[1]["messages"]) == 3
    assert j.handle("nueva conversación") == "Listo, empezamos de cero."
    assert j.brain.messages == []


def test_refusal_and_api_errors(tmp_path):
    j, api = make_jarvis(tmp_path, [_msg([], stop_reason="refusal")])
    assert "no puedo" in j.handle("algo raro")

    def boom(request):
        return httpx.Response(500, json={"type": "error", "error": {"type": "api_error", "message": "x"}})
    j.brain.client = anthropic.Anthropic(api_key="t", max_retries=0, http_client=anthropic.DefaultHttpxClient(
        transport=httpx.MockTransport(boom)))
    assert "No pude hablar con Claude" in j.handle("otra cosa")
