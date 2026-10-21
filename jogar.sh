#!/bin/sh
cd "$(dirname "$0")"

if ! command -v uv >/dev/null 2>&1; then
    echo "Instalando o uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="$HOME/.local/bin:$PATH"

echo "Iniciando o Rock Blaster (a primeira vez pode levar alguns minutos)..."
if ! uv run --python 3.12 --with-requirements requirements.txt rock_blaster.py; then
    echo
    echo "Ocorreu um erro. Veja a secao 'Solucao de problemas' no README."
fi
