#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
if [ -x .venv/bin/python ]; then
  PY=.venv/bin/python
else
  PY=python
fi
PYTHONPATH=data "$PY" -m etl
