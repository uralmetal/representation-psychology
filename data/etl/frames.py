from __future__ import annotations

import re
from pathlib import Path

from etl.normalize import clean

ROOT = Path(__file__).resolve().parents[2]
FRAMES_DIR = ROOT / "materials" / "new_materials" / "Кадры из фильмов"
OUT_DIR = ROOT / "public" / "frames"
MAX_SIDE = 1280


def _norm(text: str) -> str:
    t = clean(text).casefold()
    for ch in "«»\"'’":
        t = t.replace(ch, "")
    for ch in "‑–—":
        t = t.replace(ch, "-")
    return re.sub(r"\s+", " ", t).strip()


def _frame_number(name: str) -> int:
    match = re.search(r"кадр\D*(\d+)", name, flags=re.IGNORECASE)
    return int(match.group(1)) if match else 0


def _save_webp(src: Path, dst: Path) -> None:
    from PIL import Image

    img = Image.open(src).convert("RGB")
    width, height = img.size
    scale = min(1.0, MAX_SIDE / max(width, height))
    if scale < 1.0:
        img = img.resize((round(width * scale), round(height * scale)), Image.LANCZOS)
    img.save(dst, "WEBP", quality=80)


def collect_frames(works_meta: list[dict]) -> dict[str, list[str]]:
    """work_id -> ['frames/<work>-<n>.webp', ...] относительно public/."""
    result: dict[str, list[str]] = {item["id"]: [] for item in works_meta}
    if not FRAMES_DIR.is_dir():
        return result
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("*.webp"):
        old.unlink()

    mapping = [(item["id"], _norm(item["match"])) for item in works_meta]
    files = [
        path
        for path in FRAMES_DIR.iterdir()
        if path.is_file() and not path.name.endswith("Zone.Identifier")
    ]
    files.sort(key=lambda p: (_frame_number(p.stem), p.name))
    for path in files:
        name = _norm(path.stem)
        work_id = next((wid for wid, match in mapping if match and match in name), None)
        if work_id is None:
            raise SystemExit(f"Кадр не привязан к произведению: {path.name}")
        index = _frame_number(path.stem) or len(result[work_id]) + 1
        out_name = f"{work_id}-{index}.webp"
        if out_name in result[work_id]:
            continue
        _save_webp(path, OUT_DIR / out_name)
        result[work_id].append(f"frames/{out_name}")
    return {wid: sorted(urls) for wid, urls in result.items()}
