import pandas as pd
from pathlib import Path
import re

excel_path = "data/00_summaries/dados.xlsx"
output_dir = Path("data/01_extracted")
output_dir.mkdir(exist_ok=True)

def safe_filename(name):
    """Convert a string into a safe filename by replacing invalid characters with underscores."""
    return re.sub(r'[\\/*?:"<>|]', "_", name)

xls = pd.ExcelFile(excel_path)

for sheet_name in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name)

    json_path = output_dir / f"{safe_filename(sheet_name)}.json"
    df.to_json(
        json_path,
        orient="records", 
        force_ascii=False, 
        indent=2
    )

    print(f"Saved: {json_path}")
