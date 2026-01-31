import json
from pathlib import Path
from pydantic import BaseModel, Field
from openai import OpenAI
from dotenv import load_dotenv
from file_patterns import FORBIDDEN_TOPICS
import argparse

load_dotenv()


# ---------------- Setup ----------------

client = OpenAI()


# ---------------- Helpers ----------------
def should_skip_chunk(topics: list[str]) -> bool:
    normalized = {t.strip().lower() for t in topics}
    return not normalized.isdisjoint(FORBIDDEN_TOPICS)

# ---------------- Semantic Model ----------------

class SemanticMetadata(BaseModel):
    summary: str = Field(..., description="One sentence summary")
    topics: list[str] = Field(..., description="Up to 5 keywords")

SEMANTIC_PROMPT = """
You are analyzing a web document.
Return ONLY a strict JSON object with keys "summary" and "topics" written in Portuguese.
- "summary": A concise one-sentence summary of the document. It must be shorter than the original text.
- "topics": A list of up to 5 relevant keywords or topics from the document.
Do not include any other text.

Text:
"""

def extract_semantic_metadata(text: str) -> dict:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": SEMANTIC_PROMPT + text[:3000]}],
        temperature=0
    )

    raw = response.choices[0].message.content.strip()

    try:
        parsed = json.loads(raw)
        return SemanticMetadata(**parsed).model_dump()
    except Exception:
        return {"summary": "", "topics": []}

# ---------------- Phase 2 ----------------

def resolve_input_files(input_dir: Path, selected_files: list[str] | None):
    all_files = list(input_dir.glob("*.json"))

    if not selected_files:
        return all_files

    resolved = []
    for selector in selected_files:
        # Exact stem match
        exact = [f for f in all_files if f.stem.lower() == selector.lower()]
        if exact:
            resolved.extend(exact)
            continue

        # Partial match fallback
        partial = [f for f in all_files if selector.lower() in f.stem.lower()]
        if partial:
            resolved.extend(partial)
            continue

        raise FileNotFoundError(f"No files match selector: '{selector}'")

    # Remove duplicates while preserving order
    return list(dict.fromkeys(resolved))


def main(selected_files: list[str] | None = None):
    input_dir = Path("data/03_chunked")
    output_dir = Path("data/04_metadata")
    output_dir.mkdir(parents=True, exist_ok=True)

    json_files = resolve_input_files(input_dir, selected_files)

    for json_path in json_files:
        out_path = output_dir / json_path.name

        # Skip if already processed
        if out_path.exists():
            print(f"[SKIP] Already exists: {out_path.name}")
            continue
    
        print(f"\n[PHASE 2] Enriching: {json_path.name}")

        with open(json_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        enriched_chunks = []

        for chunk in chunks:
            semantic = extract_semantic_metadata(chunk["content"])

            # Skip forbidden topics
            if should_skip_chunk(semantic.get("topics", [])):
                continue

            enriched_chunks.append({
                **chunk,
                "summary": semantic["summary"],
                "topics": semantic["topics"]
            })

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(enriched_chunks, f, ensure_ascii=False, indent=2)

        print(f"Saved → {out_path} ({len(enriched_chunks)} enriched chunks)")

    print("\n[PHASE 2 COMPLETE]")


# ---------------- Entry Point ----------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enrich chunks with semantic metadata")
    parser.add_argument(
        "files",
        nargs="*",
        help="Optional JSON filenames or stems to process (e.g., FTJ or FTJ.json)"
    )
    args = parser.parse_args()
    main(args.files)
