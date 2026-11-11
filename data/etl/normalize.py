from __future__ import annotations

import re
import unicodedata

DASHES = str.maketrans(
    {
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2212": "-",
        "\u00a0": " ",
    }
)

MONTAGE = "Монтаж «флешбеки/сны/галлюцинации»"
SOUND = "Звук (гул, сердцебиение, искажение)"


def clean(value) -> str:
    if value is None:
        return ""
    try:
        import pandas as pd

        if pd.isna(value):
            return ""
    except Exception:
        pass
    text = unicodedata.normalize("NFKC", str(value)).translate(DASHES)
    text = text.replace("ё", "е").replace("Ё", "Е")
    text = text.replace("\\", "")
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(
        r"Монтаж\s*[«\"']*\s*флешбеки/сны/галлюцинации\s*[»\"']*",
        MONTAGE,
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"Звук\s*\(\s*гул\s*,\s*сердцебиение\s*,\s*искажение\s*\)",
        SOUND,
        text,
        flags=re.IGNORECASE,
    )
    return text.strip(" ,;")


def key(value) -> str:
    return clean(value).casefold()


def parse_title(raw: str) -> tuple[str, str]:
    match = re.match(r"^(.*?)\s*\((.*)\)\s*$", clean(raw))
    if not match:
        return clean(raw), ""
    return match.group(1).strip(), match.group(2).strip()


def parse_years(raw: str) -> tuple[int, int]:
    years = [int(item) for item in re.findall(r"\d{4}", clean(raw))]
    if not years:
        raise ValueError(f"не удалось разобрать год: {raw!r}")
    if len(years) == 1:
        return years[0], years[0]
    return years[0], years[1]


def split_list(raw: str) -> list[str]:
    parts = re.split(r"[;\n,]", clean(raw))
    return [part.strip(" .") for part in parts if part.strip(" .")]


def analysis_unit(timecode: str) -> str:
    if re.search(r"в целом", timecode, flags=re.IGNORECASE) or not timecode:
        return "work_overall"
    return "scene"


def take_codes(cell: str, labels: dict[str, str]) -> tuple[list[str], list[str]]:
    """Длинные подписи словаря снимаются жадно. Остаток — неизвестные токены."""
    remaining = clean(cell)
    ordered = sorted(labels, key=len, reverse=True)
    found: list[str] = []
    unknown: list[str] = []
    while remaining:
        remaining = remaining.strip(" ,;")
        if not remaining:
            break
        matched = next((label for label in ordered if remaining.casefold().startswith(label)), None)
        if matched:
            code = labels[matched]
            if code not in found:
                found.append(code)
            remaining = remaining[len(matched) :]
            continue
        chunk, _, rest = remaining.partition(",")
        unknown.append(chunk.strip(" ,;"))
        remaining = rest
    return found, [item for item in unknown if item]
