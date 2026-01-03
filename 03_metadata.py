import json
from pathlib import Path
from pydantic import BaseModel, Field
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ---------------- Setup ----------------

client = OpenAI()

# ---------------- Semantic Model ----------------

class SemanticMetadata(BaseModel):
    summary: str = Field(..., description="One sentence summary")
    topics: list[str] = Field(..., description="Up to 5 keywords")

SEMANTIC_PROMPT = """
You are analyzing a web document.
Return ONLY a strict JSON object with keys "summary" and "topics" written in Portuguese.
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

def main():
    input_dir = Path("data/03_chunked")
    output_dir = Path("data/04_metadata")
    output_dir.mkdir(parents=True, exist_ok=True)

    for json_path in input_dir.glob("*.json"):
        print(f"\n[PHASE 2] Enriching: {json_path.name}")

        with open(json_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        enriched_chunks = []

        for chunk in chunks:
            semantic = extract_semantic_metadata(chunk["content"])

            # Skip cookie boilerplate
            if any(t.lower() == "cookies" for t in semantic.get("topics", [])):
                continue

            enriched_chunks.append({
                **chunk,
                "summary": semantic["summary"],
                "topics": semantic["topics"]
            })

        out_path = output_dir / json_path.name
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(enriched_chunks, f, ensure_ascii=False, indent=2)

        print(f"Saved → {out_path} ({len(enriched_chunks)} enriched chunks)")

    print("\n[PHASE 2 COMPLETE]")

if __name__ == "__main__":
    main()
