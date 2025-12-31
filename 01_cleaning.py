import re
import json
from pathlib import Path
import fasttext
from file_patterns import FILE_PATTERNS, BOILERPLATE_FTJ, BOILERPLATE_FAMI_IGFV

FASTTEXT_MODEL = fasttext.load_model("models/lid.176.bin")



# =========================
# Cleaning functions
# =========================

def base_clean_text(text: str) -> str:
    """Standard cleaning: remove excessive dots, whitespace, and line breaks."""
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


def clean_text_with_boilerplate(text: str, file_stem: str) -> str:
    """
    Apply base cleaning + remove site-specific boilerplate
    based on the JSON filename (file_stem).
    """
    # Step 1: base cleaning
    cleaned = base_clean_text(text)

    # Step 2: boilerplate removal
    for pattern in FILE_PATTERNS.get(file_stem, []):
        cleaned = re.sub(
            pattern,
            "",
            cleaned,
            flags=re.DOTALL | re.IGNORECASE
        )

    if file_stem == "FTJ":
        cleaned = cleaned.replace(BOILERPLATE_FTJ, "")

    if file_stem == "FAMI" or file_stem == "IGFV":
        cleaned = cleaned.replace(BOILERPLATE_FAMI_IGFV,"")

        cleaned = re.sub(r"Skip.*?Display", "", text, flags=re.DOTALL | re.IGNORECASE)


    # Step 3: final normalization
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    return cleaned

def keep_only_portuguese_paragraphs_fasttext(
    text: str,
    min_words: int = 30,
    min_pt_ratio: float = 0.6,
    min_confidence: float = 0.75
) -> str:
    """
    Keeps Portuguese paragraphs using FastText.
    Designed for legal / institutional text (EUR-Lex).
    """
    if not text:
        return ""

    # Split by paragraph or strong separators
    paragraphs = re.split(r'\n{2,}|(?<=:) ', text)

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
# Main pipeline
# =========================

def main():
    SCRAPED_DIR = Path("data/01_extracted")
    OUTPUT_DIR = Path("data/02_clean")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for json_file in SCRAPED_DIR.glob("*.json"):
        file_stem = json_file.stem
        print(f"Cleaning: {json_file.name}")

        with open(json_file, "r", encoding="utf-8") as f:
            records = json.load(f)

        cleaned_records = []

        for record in records:
            # 1️Boilerplate + base cleaning
            cleaned = clean_text_with_boilerplate(
                record.get("text", ""),
                file_stem
            )

            # Keep only PT sentences (FastText)
            pt_only = keep_only_portuguese_paragraphs_fasttext(cleaned)

            # Drop empty / very small pages
            if len(pt_only.split()) < 50:
                continue

            record["text"] = pt_only
            cleaned_records.append(record)

        # Save cleaned file
        out_path = OUTPUT_DIR / json_file.name
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(cleaned_records, f, ensure_ascii=False, indent=2)

    print("Cleaning pipeline finished successfully.")


# =========================
# Entry point
# =========================

if __name__ == "__main__":
    main()
