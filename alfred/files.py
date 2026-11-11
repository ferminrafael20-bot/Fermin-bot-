"""Organiza carpetas moviendo archivos a subcarpetas por tipo o por fecha.

Nunca borra nada: solo mueve, y guarda un registro para poder deshacerlo.
"""

from __future__ import annotations

import json
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path

TIPOS = {
    "Imágenes": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".bmp", ".svg", ".tiff", ".raw"},
    "Videos": {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".wmv"},
    "Música y audio": {".mp3", ".wav", ".m4a", ".flac", ".aac", ".ogg", ".opus"},
    "Documentos": {".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".md", ".epub"},
    "Hojas de cálculo": {".xls", ".xlsx", ".csv", ".ods", ".numbers"},
    "Presentaciones": {".ppt", ".pptx", ".key", ".odp"},
    "Comprimidos": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"},
    "Programas": {".exe", ".msi", ".dmg", ".pkg", ".apk", ".deb", ".appimage"},
    "Diseño": {".psd", ".ai", ".fig", ".xd", ".sketch", ".indd", ".blend", ".prproj", ".aep"},
    "Código": {".py", ".js", ".ts", ".html", ".css", ".json", ".ipynb", ".sql", ".pine"},
}
OTROS = "Otros"

ALIAS = {
    "descargas": ["Downloads", "Descargas"],
    "escritorio": ["Desktop", "Escritorio"],
    "documentos": ["Documents", "Documentos"],
    "imagenes": ["Pictures", "Imágenes", "Imagenes"],
    "fotos": ["Pictures", "Imágenes", "Imagenes"],
    "videos": ["Videos", "Movies", "Vídeos"],
    "musica": ["Music", "Música", "Musica"],
}


def resolve_folder(nombre: str, home: Path | None = None) -> Path | None:
    home = home or Path.home()
    for candidato in ALIAS.get(nombre, []):
        if (home / candidato).is_dir():
            return home / candidato
    p = Path(nombre).expanduser()
    return p if p.is_dir() else None


def _destino_tipo(f: Path) -> str:
    ext = f.suffix.lower()
    return next((t for t, exts in TIPOS.items() if ext in exts), OTROS)


def plan(folder: Path, modo: str = "tipo") -> list[tuple[Path, Path]]:
    """Lista (origen, destino) sin mover nada todavía."""
    moves = []
    for f in sorted(folder.iterdir()):
        if not f.is_file() or f.name.startswith(".") or f.suffix.lower() in (".lnk", ".ini", ".crdownload", ".part"):
            continue
        if modo == "fecha":
            sub = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m")
        else:
            sub = _destino_tipo(f)
        moves.append((f, folder / sub / f.name))
    return moves


def summary(moves) -> str:
    c = Counter(dst.parent.name for _, dst in moves)
    return ", ".join(f"{n} en {k}" for k, n in c.most_common())


def _libre(dst: Path) -> Path:
    i = 1
    while dst.exists():
        dst = dst.with_name(f"{dst.stem} ({i}){dst.suffix}")
        i += 1
    return dst


def apply(moves, log_dir: Path) -> tuple[int, Path]:
    hechos = []
    for src, dst in moves:
        if not src.exists():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst = _libre(dst)
        shutil.move(str(src), str(dst))
        hechos.append([str(src), str(dst)])
    log_dir.mkdir(parents=True, exist_ok=True)
    log = log_dir / f"organizacion_{datetime.now():%Y%m%d_%H%M%S_%f}.json"
    log.write_text(json.dumps(hechos, ensure_ascii=False, indent=1), encoding="utf-8")
    return len(hechos), log


def undo_last(log_dir: Path) -> int | None:
    logs = sorted(log_dir.glob("organizacion_*.json")) if log_dir.exists() else []
    if not logs:
        return None
    hechos = json.loads(logs[-1].read_text(encoding="utf-8"))
    n = 0
    for src, dst in reversed(hechos):
        if Path(dst).exists() and not Path(src).exists():
            shutil.move(dst, src)
            n += 1
            try:
                Path(dst).parent.rmdir()  # quita la subcarpeta si quedó vacía
            except OSError:
                pass
    logs[-1].unlink()
    return n


def large_files(folder: Path, top: int = 10) -> list[tuple[Path, int]]:
    archivos = []
    for f in folder.rglob("*"):
        try:
            if f.is_file():
                archivos.append((f, f.stat().st_size))
        except OSError:
            continue
    return sorted(archivos, key=lambda x: -x[1])[:top]
