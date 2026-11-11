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
        for v in self.engine.getProperty("voices"):
            if "spanish" in v.name.lower() or "es" in (getattr(v, "languages", None) or [""])[0:1]:
                self.engine.setProperty("voice", v.id)
                break

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
