#!/bin/bash
# Abre Alfred en modo texto. Para voz: ./Alfred.command --voz
cd "$(dirname "$0")" || exit 1
.venv/bin/python -m alfred "$@"
