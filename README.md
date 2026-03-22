# IAPMEI Chatbot

A Portuguese-language chatbot designed to help SMEs find information about PT2030 investment incentives, using a vector-based knowledge base and web-scraped policy documents.

## ✅ Features
- Web-scraping pipeline via Scrapy in `botscraper/`
- Text cleaning and preprocessing pipeline (`01_cleaning.py`, `02_chunk.py`, etc.)
- Embeddings + FAISS vector index construction (`03_vectorize.py`)
- Portuguese detection with FastText model in `models/`
- Web UI for chat interaction (`gradio_website.py`)
- Offline evaluation suite under `evaluation/`

## 📁 Repository Structure
- `00_master.py`: orchestrates execution of end-to-end data pipeline
- `01_cleaning.py`: cleaning and normalization of raw extracted text
- `02_chunk.py`: chunking, filtering and metadata tagging
- `03_vectorize.py`: embedding and indexing (FAISS)
- `chatbot.py`: query / response orchestration logic
- `gradio_website.py`: Gradio-based chatbot interface
- `evaluation.py`: evaluation metrics and test harness
- `file_patterns.py`: text patterns for cleanup
- `botscraper/`: Scrapy project for document extraction
- `data/`: generated artifacts by stage (`00_summaries`, `01_extracted`, etc.)
- `models/`: language filtering model and embeddings model references
- `conversation_history/`, `chat_history/`: persisted conversation logs

## 🛠️ Prerequisites
- Python 3.10+ (or compatible env)
- `pip install -r requirements.txt`
- Optional: GPU or CPU-friendly transformer provider configured in `03_vectorize.py`

## 🚀 Quick Start
1. Activate env:
   - `source env/bin/activate`
2. Scrape content:
   - `cd botscraper`
   - `scrapy crawl botscraper`
3. Build KB pipeline:
   - `python 01_cleaning.py`
   - `python 02_chunk.py`
   - `python 03_vectorize.py`
4. Run chatbot UI:
   - `python gradio_website.py`
5. Open UI at `http://localhost:7860` (default Gradio)

## 🧪 Evaluation
- Build the query+answer evaluation dataset in `evaluation/` (JSON files provided)
- Execute:
  - `python evaluation.py`
- Metrics include precision, recall, nDCG, or custom matching (variable by implementation)

## ⚙️ Customization
- Adjust chunk size / overlap in `02_chunk.py`
- Change embedding provider in `03_vectorize.py`: OpenAI, local sentence-transformers, or other vector models
- Add postprocessors in `chatbot.py` for filtering or fact-checking

## 📝 Notes
- The project is focused on PT2030 incentive guidance; data source and domain are PG Portuguese.
- Keep `conversation_history/` and `chat_history/` for iterative training and auditing.
- `models/fasttext` model is used for language classification and to drop non-PT content.

## 💡 Helpful commands
- `python 00_master.py` to execute complete ETL flow

## 📌 Contribution
1. Fork the repo
2. Create branch (`feature/x`)
3. Add docs + tests
4. PR with clear goal and context

---

Maintained by António Oliveira.