"""Entrada/salida por voz (opcional).

Requiere instalar: ``pip install SpeechRecognition pyttsx3 pyaudio``.
El reconocimiento usa el servicio gratuito de Google (necesita internet);
la voz de respuesta (pyttsx3) funciona sin conexión.
"""

from __future__ import annotations


class Voice:
    def __init__(self, language: str = "es-ES"):
        try:
            import pyttsx3
            import speech_recognition as sr
        except ImportError as exc:
            raise RuntimeError(
                "Para usar la voz instala: pip install SpeechRecognition pyttsx3 pyaudio"
            ) from exc
        self.sr = sr
        self.language = language
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        voz = _voz_espanol(self.engine.getProperty("voices"))
        if voz:
            self.engine.setProperty("voice", voz)

    def listen(self) -> str | None:
        with self.sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.4)
            audio = self.recognizer.listen(source, phrase_time_limit=10)
        try:
            return self.recognizer.recognize_google(audio, language=self.language)
        except self.sr.UnknownValueError:
            return None

    def say(self, text: str) -> None:
        self.engine.say(text)
        self.engine.runAndWait()


def _voz_espanol(voces) -> str | None:
    """Elige una voz en español, prefiriendo Chile, luego Latinoamérica.

    Mac: Ajustes del Sistema → Accesibilidad → Contenido leído → Voz del sistema
    → Gestionar voces, para descargar más voces (p. ej. "Paulina" o "Francisca").
    Windows: Configuración → Hora e idioma → Voz → Agregar voces (Español).
    """
    def idiomas(v):
        out = []
        for lang in getattr(v, "languages", None) or []:
            if isinstance(lang, bytes):
                lang = lang.decode(errors="ignore")
            out.append(str(lang).lower().replace("-", "_").lstrip("\x05"))
        nombre = (v.name or "").lower()
        if "spanish" in nombre or "español" in nombre:
            out.append("es_" + ("cl" if "chile" in nombre else "mx" if "mex" in nombre else "es"))
        return out

    puntaje = {}
    for v in voces:
        for lang in idiomas(v):
            if lang.startswith("es"):
                p = 3 if lang.startswith("es_cl") else 2 if lang[3:5] not in ("es", "") else 1
                puntaje[v.id] = max(puntaje.get(v.id, 0), p)
    return max(puntaje, key=puntaje.get) if puntaje else None
