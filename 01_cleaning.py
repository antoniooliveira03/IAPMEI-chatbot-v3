import re
import json
from pathlib import Path
import fasttext
from file_patterns import FILE_PATTERNS, NAV_WORDS, COMMON_PT_VERBS
import argparse

# =========================
# Load FastText model
# =========================

FASTTEXT_MODEL = fasttext.load_model("models/lid.176.bin")


# =========================
# Base cleaning
# =========================

def base_clean_text(text: str) -> str:
    """Standard cleaning: normalize whitespace, punctuation, and line breaks."""
    if not text:
        return ""

    text = re.sub(r'\.{3,}', ' ', text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r'[ \t]*\n[ \t]*', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)

    return text.strip()


# =========================
# Boilerplate removal
# =========================

def clean_text_with_boilerplate(text: str, file_stem: str) -> str:
    """Apply base cleaning + site-specific boilerplate removal."""
    cleaned = base_clean_text(text)

    for pattern in FILE_PATTERNS.get(file_stem, []):
        cleaned = re.sub(pattern, "", cleaned, flags=re.DOTALL | re.IGNORECASE)

    # Generic skip/display junk
    cleaned = re.sub(
        r"Skip.*?Display",
        "",
        cleaned,
        flags=re.DOTALL | re.IGNORECASE
    )

    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


# =========================
# Heuristic paragraph filters
# =========================

def deduplicate_paragraphs(text: str) -> str:
    seen = set()
    out = []

    for p in re.split(r'\n{2,}', text):
        key = re.sub(r'\s+', ' ', p.lower()).strip()
        if key and key not in seen:
            seen.add(key)
            out.append(p)

    return "\n\n".join(out)


def drop_navigation_paragraphs(text: str, max_ratio: float = 0.4) -> str:
    paras = re.split(r'\n{2,}', text)
    keep = []

    for p in paras:
        words = re.findall(r'\w+', p.lower())
        if not words:
            continue

        nav_hits = sum(w in NAV_WORDS for w in words)
        if nav_hits / len(words) <= max_ratio:
            keep.append(p)

    return "\n\n".join(keep)


def drop_caps_heavy_paragraphs(text: str, max_ratio: float = 0.5) -> str:
    paras = re.split(r'\n{2,}', text)
    keep = []

    for p in paras:
        words = p.split()
        if not words:
            continue

        caps = sum(w.isupper() for w in words if len(w) > 2)
        if caps / len(words) < max_ratio:
            keep.append(p)

    return "\n\n".join(keep)


def drop_url_heavy_paragraphs(text: str, max_ratio: float = 0.25) -> str:
    paras = re.split(r'\n{2,}', text)
    keep = []

    for p in paras:
        words = p.split()
        if not words:
            continue

        url_count = len(re.findall(r'https?://|www\.', p))
        if url_count / len(words) <= max_ratio:
            keep.append(p)

    return "\n\n".join(keep)


def drop_verb_less_paragraphs(text: str) -> str:
    paras = re.split(r'\n{2,}', text)
    keep = []

    for p in paras:
        words = set(re.findall(r'\w+', p.lower()))
        if words & COMMON_PT_VERBS:
            keep.append(p)

    return "\n\n".join(keep)


# =========================
# Language filtering
# =========================

def keep_only_portuguese_paragraphs_fasttext(
    text: str,
    min_words: int = 30,
    min_pt_ratio: float = 0.6,
    min_confidence: float = 0.75
) -> str:
    if not text:
        return ""

    paragraphs = re.split(r'\n{2,}', text)

    pt_paragraphs = []
    valid = 0

    for p in paragraphs:
        p = p.strip()
        if len(p.split()) < min_words:
            continue

        labels, probs = FASTTEXT_MODEL.predict(
            p.replace("\n", " "),
            k=1
        )

        lang = labels[0].replace("__label__", "")
        confidence = probs[0]

        valid += 1
        if lang == "pt" and confidence >= min_confidence:
            pt_paragraphs.append(p)

    if valid == 0:
        return ""

    if len(pt_paragraphs) / valid < min_pt_ratio:
        return ""

    return "\n\n".join(pt_paragraphs)


# =========================
# Helpers
# =========================

def is_scraped_page(record: dict) -> bool:
    required_keys = {"url", "type", "depth", "text"}
    return required_keys.issubset(record.keys())


def resolve_input_files(scraped_dir: Path, selected_files: list[str]):
    if not selected_files:
        return list(scraped_dir.glob("*.json"))

    all_files = list(scraped_dir.glob("*.json"))
    resolved = []

    for selector in selected_files:
        exact = [f for f in all_files if f.stem.lower() == selector.lower()]
        if exact:
            resolved.extend(exact)
            continue

        partial = [f for f in all_files if selector.lower() in f.stem.lower()]
        if not partial:
            raise FileNotFoundError(f"No files match selector: '{selector}'")

        resolved.extend(partial)

    return list(dict.fromkeys(resolved))


# =========================
# Main pipeline
# =========================

def main(selected_files: list[str] | None = None):
    SCRAPED_DIR = Path("data/01_extracted")
    OUTPUT_DIR = Path("data/02_clean")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    json_files = resolve_input_files(SCRAPED_DIR, selected_files or [])

    for json_file in json_files:
        print(f"Cleaning: {json_file.name}")
        file_stem = json_file.stem

        with open(json_file, "r", encoding="utf-8") as f:
            records = json.load(f)

        cleaned_records = []

        for record in records:
            if not is_scraped_page(record):
                cleaned_records.append(record)
                continue

            cleaned = clean_text_with_boilerplate(
                record.get("text", ""),
                file_stem
            )

            # Heuristic cleaning
            cleaned = deduplicate_paragraphs(cleaned)
            cleaned = drop_navigation_paragraphs(cleaned)
            cleaned = drop_caps_heavy_paragraphs(cleaned)
            cleaned = drop_url_heavy_paragraphs(cleaned)
            cleaned = drop_verb_less_paragraphs(cleaned)

            # Language filtering
            pt_only = keep_only_portuguese_paragraphs_fasttext(cleaned)

            if len(pt_only.split()) < 50:
                continue

            record["text"] = pt_only
            cleaned_records.append(record)

        out_path = OUTPUT_DIR / json_file.name
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(cleaned_records, f, ensure_ascii=False, indent=2)

    print("Cleaning pipeline finished successfully.")


# =========================
# Entry point
# =========================

if __name__ == "__main__":
    print("Starting cleaning pipeline...")
    parser = argparse.ArgumentParser(description="Clean scraped JSON files")
    parser.add_argument(
        "files",
        nargs="*",
        help="Optional JSON filenames or stems to process"
    )
    args = parser.parse_args()
    main(args.files)
