# IAPMEI Chatbot

A Portuguese-language chatbot for SMEs that uses web-scraped policy content, cleaning and chunking pipelines, FAISS vector retrieval, and OpenAI-powered response generation.

## ✅ What this repository contains
- `botscraper/`: Scrapy project that crawls configured sites and writes JSON records per site
- `preprocessing/01_cleaning.py`: text cleaning, filtering, and Portuguese language validation
- `preprocessing/02_chunk.py`: chunk creation, deduplication, and metadata assembly
- `preprocessing/03_vectorize.py`: embedding generation and FAISS index building
- `chatbot/chatbot.py`: retrieval, reranking, and answer generation logic
- `website/gradio_website.py`: Gradio chatbot interface for local use
- `evaluation/evaluation.py`: evaluation harness for dataset-based model comparison
- `data/`: pipeline outputs and generated artifacts
- `conversation_history/`, `chat_history/`: persistent session storage
- `models/`: language detection and model reference files

## 🔧 Prerequisites
- Python 3.10 or newer
- Run from repo root for all commands unless otherwise noted
- Install dependencies:
  ```bash
  source env/bin/activate
  pip install -r requirements.txt
  ```
- Required environment variables in a `.env` file at repo root:
  ```bash
  OPENAI_API_KEY=your_api_key_here
  ```

## 📂 Important directories
- `botscraper/`: Scrapy project and spider
- `data/01_extracted`: raw scraper output
- `data/02_clean`: cleaned documents ready for chunking
- `data/03_chunked`: chunked document output
- `data/04_vectorized`: FAISS index + metadata for retrieval
- `evaluation/`: evaluation datasets and results
- `models/`: FastText language model and optional model resources

## 1) Scraping with `botscraper`
### What it does
The scraper reads `botscraper/sites.json` and crawls the configured start URLs. Extracted pages are filtered, cleaned, and saved as line-delimited JSON files by site.

### Run it
From the repo root:
```bash
cd botscraper
scrapy crawl botscraper
```

### Output location
- `data/01_extracted/<site>.json`

### Notes
- Scrapy obeys `robots.txt`
- Output path is configured in `botscraper/botscraper/settings.py` via `DATA_BASE_PATH`
- If you want to change crawl depth, update `DEPTH_LIMIT` in `botscraper/botscraper/settings.py`
- The spider will skip pages containing `arquivo`, login/cookies/legal pages, and other unwanted URLs.

## 2) Cleaning and filtering
### What it does
`preprocessing/01_cleaning.py` loads scraped JSON files, removes boilerplate, normalizes whitespace, drops navigation-heavy paragraphs, detects Portuguese with FastText, and saves cleaned JSON.

### Run it
From the repo root:
```bash
python preprocessing/01_cleaning.py
```

### Optional: clean selected files only
```bash
python preprocessing/01_cleaning.py file1 file2
```

### Output location
- `data/02_clean/<filename>.json`

### Notes
- `preprocessing/01_cleaning.py` supports both JSON arrays and JSONL scraped output
- It uses `models/lid.176.bin` for Portuguese detection

## 3) Chunking text
### What it does
`preprocessing/02_chunk.py` converts cleaned documents into chunks with overlap, removes duplicate chunks, and stores chunk metadata.

### Run it
From the repo root:
```bash
python preprocessing/02_chunk.py
```

### Output location
- `data/03_chunked/c<chunk_size>_<chunk_overlap>/<filename>.json`

### Default settings
- chunk size: `600`
- chunk overlap: `60`

### Notes
- Website pages are split into text chunks
- Q&A-style documents are preserved as single entries
- Chunk content is annotated with a human-readable source title

## 4) Vectorizing and building FAISS index
### What it does
`preprocessing/03_vectorize.py` embeds every chunk using OpenAI embeddings, normalizes vectors, stores them in FAISS, and saves metadata.

### Run it
From the repo root:
```bash
python preprocessing/03_vectorize.py
```

### Output location
- `data/04_vectorized/small/c600_60/db.index`
- `data/04_vectorized/small/c600_60/db.json`

### Notes
- Default embedding model: `text-embedding-3-small`
- Dimensionality is set to `1536` for the `small` embedding type
- If you need a different embedding model, update `embeddings_type` in `preprocessing/03_vectorize.py`

## 5) Running the chatbot
### CLI chatbot
From the repo root:
```bash
python chatbot/chatbot.py
```

### Web UI chatbot
From the repo root:
```bash
python website/gradio_website.py
```
Open the Gradio interface at:
- `http://localhost:7860`

### What the chatbot uses
- `chatbot/chatbot.py` loads the FAISS index and metadata
- It combines dense vector search, BM25 sparse retrieval, and optional reranking
- It calls the OpenAI `chat.completions` API to generate answers

### Notes
- The website script resolves repo-relative paths so it works when executed from `website/`
- The default vector directory in the web UI is loaded from `data/04_vectorized/small/c400_40`

## 6) Evaluation
### What it does
`evaluation/evaluation.py` loads an evaluation dataset, retrieves context from the index, and measures model responses using `ragas`.

### Run it
From the repo root:
```bash
python evaluation/evaluation.py
```

### Output location
- `evaluation/results/evaluation_results_*.csv`

### Notes
- The script loads `evaluation/evaluation_dataset_v2.json`
- It uses OpenAI embeddings and `gpt-4o-mini` by default
- Results are saved as a CSV file under `evaluation/results/`

## 7) Optional full pipeline orchestration
`preprocessing/00_master.py` is intended to run the cleaning, chunking, and vectorization scripts in sequence. If it is not working, use the commands above manually.

### Run it
From the repo root:
```bash
python preprocessing/00_master.py
```

## Configuration and customization
### `.env` variables
- `OPENAI_API_KEY`: required for embeddings and chat completions
- Add any other OpenAI-related variables your environment requires

### Scraper configuration
- Edit `botscraper/sites.json` to add or remove start URLs and allowed domains
- `botscraper/botscraper/settings.py` contains `DATA_BASE_PATH`, `DEPTH_LIMIT`, and Scrapy crawl settings

### Preprocessing tuning
- Change `chunk_size` and `chunk_overlap` in `preprocessing/02_chunk.py`
- Change embedding size and model in `preprocessing/03_vectorize.py`
- Change retrieval weights in `chatbot/chatbot.py`

## Troubleshooting
- `ModuleNotFoundError: No module named 'chatbot'`: run from repo root or add repo root to `sys.path`
- `could not open data/04_vectorized/.../db.index`: ensure `VECTOR_DIR` is repo-relative and the index exists
- Scrapy outputs are written to `data/01_extracted`; verify crawler completed successfully
- If FastText fails, confirm `models/lid.176.bin` is present and accessible

## Recommended command sequence
```bash
source env/bin/activate
pip install -r requirements.txt
cd botscraper
scrapy crawl botscraper
cd ..
python preprocessing/01_cleaning.py
python preprocessing/02_chunk.py
python preprocessing/03_vectorize.py
python website/gradio_website.py
```

## File overview
- `botscraper/`: Scrapy spider, items, pipelines, and settings
- `preprocessing/01_cleaning.py`: cleaning pipeline for raw text
- `preprocessing/02_chunk.py`: chunk generation and deduplication
- `preprocessing/03_vectorize.py`: embedding + FAISS index creation
- `chatbot/chatbot.py`: retrieval and chat response loop
- `website/gradio_website.py`: Gradio interface
- `evaluation/evaluation.py`: metrics evaluation workflow

---

Maintained by António Oliveira