from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from etl.extract import ROOT, SOURCE, VERSION

README = """Датасет «Репрезентация психологии в кино»

Файлы:
- works.json — произведения корпуса: название, формат, годы, страны, жанры, описание, кадры (frames — пути к изображениям на сайте, в архив не входят).
- scenes.json — единицы анализа (строки таблицы кодирования): таймкод, описание, коды категорий, note (неизвестные токены вне словаря) и field_notes (пояснения кодирования по полям).
- codebook.json — словарь категорий: категории, значения, определения и примеры.
- meta.json — версия датасета и лицензия.
- validation-report.json — отчёт валидатора ETL: число записей, ошибки и предупреждения прогона.

Категории кодирования: space_type, therapist_archetype, ethical_violation, stigma_level, utterance_type, visual_trope. scene_function — свободные формулировки вне словаря. analysis_unit: scene — отдельная сцена с таймкодом, work_overall — строка описывает произведение целиком.
"""


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

    with zipfile.ZipFile(public / "dataset.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for name in ("works.json", "scenes.json", "codebook.json", "meta.json", "validation-report.json"):
            archive.write(public / name, name)
        archive.writestr("README.txt", README)


def _dump(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
