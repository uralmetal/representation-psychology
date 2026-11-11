from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from etl.extract import ROOT, SOURCE, VERSION


def write(dataset: dict, errors: list[str]) -> None:
    public = ROOT / "public" / "data"
    private = ROOT / "data" / "out"
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    envelope = {"version": VERSION, "generated_at": generated_at}

    _dump(public / "works.json", {**envelope, "works": dataset["works"]})
    _dump(public / "scenes.json", {**envelope, "scenes": dataset["scenes"]})
    _dump(public / "codebook.json", {**envelope, "entries": dataset["codebook"]})
    report = {
        **envelope,
        "source": str(SOURCE.relative_to(ROOT)),
        "works": len(dataset["works"]),
        "scenes": len(dataset["scenes"]),
        "codebook": len(dataset["codebook"]),
        "errors": errors,
        "warnings": dataset["warnings"],
        "checks": [
            "уникальные id",
            "ссылки work_id",
            "коды входят в словарь",
            "мультиполя — массивы",
            "пустые строки не опубликованы",
            "в публичных файлах нет имён кодеров",
            "семь глав ссылаются минимум на две единицы",
        ],
    }
    _dump(public / "validation-report.json", report)
    _dump(public / "meta.json", {**envelope, "title": "Репрезентация психологии в кино", "license": "CC0-1.0"})
    _dump(private / "withheld.json", {"version": VERSION, "rows": dataset["withheld"]})


def _dump(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
