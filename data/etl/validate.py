from __future__ import annotations

from pathlib import Path

import yaml

from etl.extract import CHAPTERS, ROOT

BANNED = ("Полина", "Ира")
CONTENT_KINDS = {"content"}


def validate(dataset: dict) -> list[str]:
    errors: list[str] = []
    works = dataset["works"]
    scenes = dataset["scenes"]
    codebook = dataset["codebook"]
    work_ids = [item["id"] for item in works]
    scene_ids = [item["id"] for item in scenes]
    codes = {(item["category"], item["value"]) for item in codebook}

    if len(work_ids) != len(set(work_ids)):
        errors.append("Повторяются id произведений")
    if len(scene_ids) != len(set(scene_ids)):
        errors.append("Повторяются id единиц анализа")
    if len({item["id"] for item in codebook}) != len(codebook):
        errors.append("Повторяются id словаря")

    for scene in scenes:
        if scene["work_id"] not in work_ids:
            errors.append(f"{scene['id']}: нет произведения")
        if scene["analysis_unit"] not in {"scene", "work_overall"}:
            errors.append(f"{scene['id']}: пустой analysis_unit")
        if not scene["description"] or not scene["timecode"]:
            errors.append(f"{scene['id']}: нет описания или таймкода")
        _check(errors, scene, "space_type", scene["space_type"], codes, allow_empty=True)
        for value in scene["therapist_archetype"]:
            _check(errors, scene, "therapist_archetype", value, codes)
        _check(errors, scene, "ethical_violation", scene["ethical_violation"], codes)
        _check(errors, scene, "stigma_level", scene["stigma_level"], codes)
        for value in scene["utterance_types"]:
            _check(errors, scene, "utterance_type", value, codes)
        for value in scene["visual_tropes"]:
            _check(errors, scene, "visual_trope", value, codes)
        if not isinstance(scene["utterance_types"], list) or not isinstance(scene["visual_tropes"], list):
            errors.append(f"{scene['id']}: мультиполя должны быть массивами")

    blob = "\n".join(str(dataset[name]) for name in ("works", "scenes", "codebook"))
    for name in BANNED:
        if name in blob:
            errors.append(f"В публичных данных осталось имя «{name}»")

    source = (ROOT / "data" / "source" / "coding.xlsx").read_bytes()
    for name in BANNED:
        if name.encode("utf-8") in source:
            errors.append(f"В data/source/coding.xlsx осталось имя «{name}»")

    chapters = sorted(CHAPTERS.glob("*.md"))
    if len(chapters) != 7:
        errors.append(f"Ожидалось 7 глав, найдено {len(chapters)}")
    for path in chapters:
        text = path.read_text(encoding="utf-8")
        _, frontmatter, _ = text.split("---", 2)
        meta = yaml.safe_load(frontmatter)
        linked = meta.get("scene_ids") or []
        if len(linked) < 2:
            errors.append(f"{path.name}: меньше двух scene_id")
        missing = [item for item in linked if item not in scene_ids]
        if missing:
            errors.append(f"{path.name}: неизвестные сцены {missing}")
        if meta.get("kind") in CONTENT_KINDS and not meta.get("viz"):
            errors.append(f"{path.name}: у содержательной главы нет визуализации")
    return errors


def _check(errors, scene, category, value, codes, allow_empty=False):
    if value in (None, ""):
        if not allow_empty:
            errors.append(f"{scene['id']}: пустой код {category}")
        return
    if (category, value) not in codes:
        errors.append(f"{scene['id']}: {category}={value} нет в словаре")
