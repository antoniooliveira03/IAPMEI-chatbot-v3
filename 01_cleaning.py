import re
import json
from pathlib import Path

# =========================
# Boilerplate patterns
# =========================

FILE_PATTERNS = {
    "compete2030": [
        r"Saltar para o conteúdo principal.*?Início",
        r"Esta página foi útil para si\?.*?A carregar",
        r"© COMPETE 2030.*$"
    ],
    "centro2030": [
        r"Programas do Portugal 2030.*?Avisos de concurso",
        r"© 2023 Centro 2030.*$"
    ],
    "alentejo_portugal2030": [
        r"Programas do Portugal 2030.*?Regras de Comunicação",
        r"Este site utiliza cookies.*$"
    ],
    "algarve_portugal2030": [
        r"Programas do Portugal 2030.*?Área Reservada",
        r"Este site utiliza cookies.*$"
    ],
    "lisboa_portugal2030": [
        r"Programas do Portugal 2030.*?Plano Anual de Avisos",
        r"Este site utiliza cookies.*$"
    ],
    "norte2030": [
        r"Ir para o conteúdo principal.*?Pesquisar",
        r"© 2024 NORTE 2030.*$"
    ],
    "portugal2030": [
        r"Saltar para o conteúdo principal.*?Plano Anual de Avisos",
        r"Este site utiliza cookies.*$"
    ]
}

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

    # Step 3: final normalization
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    return cleaned

# =========================
# Main pipeline
# =========================

def main():
    SCRAPED_DIR = Path("data/01_extracted")
    OUTPUT_DIR = Path("data/02_clean")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for json_file in SCRAPED_DIR.glob("*.json"):
        file_stem = json_file.stem  # e.g. "algarve_portugal2030"
        print(f"Cleaning: {json_file.name}")

        with open(json_file, "r", encoding="utf-8") as f:
            records = json.load(f)

        # Clean each page
        for record in records:
            record["text"] = clean_text_with_boilerplate(
                record.get("text", ""),
                file_stem
            )

        # Drop empty / very small pages
        records = [
            r for r in records
            if len(r.get("text", "").split()) >= 50
        ]

        # Save cleaned file
        out_path = OUTPUT_DIR / json_file.name
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

    print("Cleaning pipeline finished successfully.")

# =========================
# Entry point
# =========================

if __name__ == "__main__":
    main()
