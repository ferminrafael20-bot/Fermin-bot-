"""Pruebas de la conexión con Claude, sin red: la API se simula."""

import json
from datetime import datetime

import pytest

anthropic = pytest.importorskip("anthropic")
httpx = pytest.importorskip("httpx2")

from alfred import Alfred  # noqa: E402
from alfred.brain import ClaudeBrain  # noqa: E402
from alfred.expenses import ExpenseBook  # noqa: E402


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


def make_alfred(tmp_path, replies):
    api = FakeAPI(replies)
    client = anthropic.Anthropic(api_key="test", max_retries=0,
                                 http_client=anthropic.DefaultHttpxClient(transport=httpx.MockTransport(api)))
    j = Alfred(data_dir=tmp_path, clock=lambda: datetime(2026, 10, 15, 13, 0), brain=False)
    j.brain = ClaudeBrain(j.ctx, j.run_command, client=client)
    j.ctx.extras["brain"] = j.brain
    return j, api


def test_fixed_commands_do_not_call_claude(tmp_path):
    j, api = make_alfred(tmp_path, [])
    assert "Comida" in j.handle("gasté 20 en pizza")
    assert api.requests == []


def test_claude_registers_free_form_expenses(tmp_path):
    j, api = make_alfred(tmp_path, [
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
    nombres = {t["name"] for t in first["tools"]}
    assert {"registrar_gasto", "ejecutar_comando", "crear_evento", "organizar_carpeta",
            "auditar_tienda_shopify", "guardar_nota", "web_search"} <= nombres
    assert "Perfil" in first["system"][1]["text"] or "perfil" in first["system"][1]["text"]
    # el segundo turno reenvía el razonamiento y devuelve ambos resultados juntos
    assert second["messages"][1]["content"][0]["type"] == "thinking"
    results = second["messages"][2]["content"]
    assert [r["tool_use_id"] for r in results] == ["tu_1", "tu_2"]
    assert all(r["is_error"] is False for r in results)


def test_multi_amount_phrase_goes_to_claude(tmp_path):
    j, api = make_alfred(tmp_path, [_msg([{"type": "text", "text": "Hecho."}])])
    assert j.handle("gasté 300 en comida y 200 en uber") == "Hecho."
    assert len(api.requests) == 1


def test_claude_can_run_any_command(tmp_path):
    j, api = make_alfred(tmp_path, [
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
    j, api = make_alfred(tmp_path, [_msg([{"type": "text", "text": "Hola Fermín."}]),
                                    _msg([{"type": "text", "text": "Te llamas Fermín."}])])
    j.handle("me llamo Fermín")
    j.handle("¿cómo me llamo?")
    assert len(api.requests[1]["messages"]) == 3
    assert j.handle("nueva conversación") == "Listo, empezamos de cero."
    assert j.brain.messages == []


def test_refusal_and_api_errors(tmp_path):
    j, api = make_alfred(tmp_path, [_msg([], stop_reason="refusal")])
    assert "no puedo" in j.handle("algo raro")

    def boom(request):
        return httpx.Response(500, json={"type": "error", "error": {"type": "api_error", "message": "x"}})
    j.brain.client = anthropic.Anthropic(api_key="t", max_retries=0, http_client=anthropic.DefaultHttpxClient(
        transport=httpx.MockTransport(boom)))
    assert "No pude hablar con Claude" in j.handle("otra cosa")


def test_claude_creates_event_and_confirmation_flow(tmp_path):
    j, api = make_alfred(tmp_path, [
        _msg([{"type": "tool_use", "id": "tu_1", "name": "crear_evento",
               "input": {"tipo": "clase", "titulo": "Clase con Ana", "fecha_hora": "2026-10-16T18:00",
                         "persona": "Ana", "lugar": "", "semanal": True}}], stop_reason="tool_use"),
        _msg([{"type": "text", "text": "Agendé tu clase con Ana todos los viernes."}]),
    ])
    j.handle("los viernes a las 6 doy clase a Ana, apúntalo")
    from alfred.agenda import Agenda
    ev = Agenda(tmp_path).all()[0]
    assert (ev.persona, ev.semanal, ev.fecha) == ("Ana", True, "2026-10-16T18:00")


def test_pause_turn_is_resumed(tmp_path):
    j, api = make_alfred(tmp_path, [_msg([], stop_reason="pause_turn"),
                                    _msg([{"type": "text", "text": "BTC está en 100k."}])])
    assert j.handle("¿a cuánto está el bitcoin?") == "BTC está en 100k."
    assert len(api.requests) == 2


def test_news_digest_collects_sources(tmp_path):
    from alfred import news
    j, api = make_alfred(tmp_path, [_msg([
        {"type": "text", "text": "Resumen: BTC sube.",
         "citations": [{"type": "web_search_result_location", "url": "https://ej.com/a", "title": "Nota A",
                        "cited_text": "x", "encrypted_index": "e"}]}])])
    texto = news.build_digest(j.brain, datetime(2026, 10, 15, 6, 0))
    assert "BTC sube" in texto and "https://ej.com/a" in texto
    assert api.requests[0]["tools"][0]["type"] == "web_search_20260209"
