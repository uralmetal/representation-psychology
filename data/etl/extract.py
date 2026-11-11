from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from etl.normalize import (
    analysis_unit,
    clean,
    key,
    parse_title,
    parse_years,
    split_list,
    take_codes,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data" / "source" / "coding.xlsx"
CODEBOOK_YML = ROOT / "data" / "source" / "codebook.yml"
WORKS_YML = ROOT / "data" / "source" / "works.yml"
CHAPTERS = ROOT / "src" / "content" / "chapters"
VERSION = "1.0.0"

FIELD_MAP = {
    "space_type": "space_type",
    "therapist_archetype": "therapist_archetype",
    "ethical_violation": "ethical_violation",
    "stigma_level": "stigma_level",
    "utterance_type": "utterance_types",
    "visual_trope": "visual_tropes",
}

SINGLE = {"space_type", "ethical_violation", "stigma_level"}


def load_codebook() -> list[dict]:
    document = yaml.safe_load(CODEBOOK_YML.read_text(encoding="utf-8"))
    entries: list[dict] = []
    for category in document["categories"]:
        for value in category["values"]:
            entries.append(
                {
                    "id": f"{category['id']}.{value['id']}",
                    "category": category["id"],
                    "category_label": category["label"],
                    "category_definition": category["definition"],
                    "value": value["id"],
                    "label": value["label"],
                    "definition": value["definition"],
                    "example": value["example"],
                }
            )
    return entries


def load_works_meta() -> list[dict]:
    return yaml.safe_load(WORKS_YML.read_text(encoding="utf-8"))["works"]


def _labels(entries: list[dict], category: str) -> dict[str, str]:
    return {key(entry["label"]): entry["value"] for entry in entries if entry["category"] == category}


def build() -> dict:
    frame = pd.read_excel(SOURCE, header=None)
    headers = [clean(value) for value in frame.iloc[0].tolist()]
    if "Категория анализа" in headers:
        raise SystemExit("В data/source/coding.xlsx остался столбец с именами кодеров")
    column = {name: index for index, name in enumerate(headers)}
    entries = load_codebook()
    meta = load_works_meta()
    by_match = {key(item["match"]): item for item in meta}
    warnings: list[str] = []
    withheld: list[dict] = []
    works: list[dict] = []
    scenes: list[dict] = []

    for row_number, row in frame.iloc[1:].iterrows():
        title_raw = clean(row.iloc[column["title"]])
        if not title_raw or title_raw.startswith("("):
            continue
        description = clean(row.iloc[column["scene_description"]])
        coded = any(clean(row.iloc[column[name]]) for name in ("space_type", "therapist_archetype", "stigma_level"))
        if not description and not coded:
            warnings.append(f"Пустая запись исключена: {title_raw} (строка {row_number + 1})")
            continue
        title, original = parse_title(title_raw)
        profile = by_match.get(key(title))
        if profile is None:
            raise SystemExit(f"Нет описания в works.yml для «{title}»")
        work_id = profile["id"]
        year_start, year_end = parse_years(row.iloc[column["year"]])
        timecode = clean(row.iloc[column["timecode"]])
        unit = analysis_unit(timecode)
        if unit == "work_overall" and clean(row.iloc[column["movie_or_TV series"]]) == "movie":
            warnings.append(f"{title}: фильм закодирован формулировкой «в целом»")
        if timecode.count("~") > 1:
            warnings.append(f"{title}: несколько таймкодов оставлены одной единицей анализа")

        note_parts: list[str] = []
        codes: dict[str, object] = {}
        for source_name, target_name in FIELD_MAP.items():
            raw = clean(row.iloc[column[source_name]])
            found, unknown = take_codes(raw, _labels(entries, source_name))
            if unknown:
                warnings.append(f"{title}: вне словаря {source_name}: {', '.join(unknown)}")
                note_parts.append(f"{source_name}: «{'», «'.join(unknown)}»")
            if source_name in SINGLE:
                codes[target_name] = found[0] if found else None
            else:
                codes[target_name] = found

        for note_column in (
            "scene_description_note",
            "space_type_note",
            "therapist_archetype_note",
            "ethical_violation_note",
            "stigma_level_note",
            "utterance_type_note",
            "visual_trope_note",
            "scene_function_note",
            "general_note",
        ):
            text = clean(row.iloc[column[note_column]])
            if text:
                note_parts.append(f"{note_column}: {text}")
        tools = clean(row.iloc[column["the_use_of_DH_tools"]])
        if tools:
            withheld.append({"work_id": work_id, "the_use_of_DH_tools": tools})

        format_raw = clean(row.iloc[column["movie_or_TV series"]])
        if format_raw not in {"movie", "TV series"}:
            raise SystemExit(f"{title}: неизвестный формат {format_raw!r}")
        works.append(
            {
                "id": work_id,
                "title": title,
                "original_title": original,
                "format": "movie" if format_raw == "movie" else "tv_series",
                "year_start": year_start,
                "year_end": year_end,
                "country": split_list(row.iloc[column["country"]]),
                "genres": split_list(row.iloc[column["film genre"]]),
                "description": profile["description"].strip(),
            }
        )
        scenes.append(
            {
                "id": f"{work_id}-unit",
                "work_id": work_id,
                "analysis_unit": unit,
                "timecode": timecode,
                "description": description,
                "space_type": codes["space_type"],
                "therapist_archetype": codes["therapist_archetype"],
                "ethical_violation": codes["ethical_violation"],
                "stigma_level": codes["stigma_level"],
                "utterance_types": codes["utterance_types"],
                "visual_tropes": codes["visual_tropes"],
                "scene_function": split_list(row.iloc[column["scene_function"]]),
                "note": "\n\n".join(note_parts),
            }
        )

    return {
        "version": VERSION,
        "works": works,
        "scenes": scenes,
        "codebook": entries,
        "warnings": warnings,
        "withheld": withheld,
    }
