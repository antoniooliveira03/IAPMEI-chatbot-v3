import os

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import chatbot
import utils

import numpy as np
import pandas as pd
import json
from dotenv import load_dotenv
import nest_asyncio
from pathlib import Path

from openai import OpenAI
from langchain_openai import OpenAIEmbeddings

from datasets import Dataset

from ragas.llms import llm_factory
from ragas import evaluate
import os

import torch

torch.set_num_threads(1)
torch.set_num_interop_threads(1)

load_dotenv()
client = OpenAI()
nest_asyncio.apply()


# ---- Parameters ----
chunk_size = 400
chunk_overlap = 80
embeddings_type = "small"
k = 10
top_k = 10
weight_dense = 0.5
weight_sparse = 0.5
rerank = False

# ---- Load evaluation dataset ----
with open("evaluation/evaluation_dataset_v2.json", "r", encoding="utf-8") as f:
    data = json.load(f)

eval_dataset = utils.json_to_documents(data)

# ---- Load FAISS index and metadata ----
chatbot.set_vector_dir(f"data/05_vectorized/{embeddings_type}/c{chunk_size}_{chunk_overlap}")
index, metadata = chatbot.load_faiss_index(chatbot.VECTOR_DIR)
bm25=chatbot.build_bm25(metadata)
print(f"Index and metadata loaded at {chatbot.VECTOR_DIR}")


# ---- Populate evaluation dataset with retrieved contexts ----
filename = f"eval_dataset_filled_{embeddings_type}_c{chunk_size}_{chunk_overlap}__{k}_{top_k}_{weight_dense}_{weight_sparse}_{rerank}.json"
filepath = Path("evaluation") / filename

if not filepath.exists():

    print(f"Populating evaluation dataset with retrieved contexts and saving to {filepath}...")
    
    eval_dataset = utils.populate_eval_dataset(
        eval_dataset, index, metadata, bm25,
        model="gpt-4o-mini",
        k=k,
        top_k=top_k,
        weight_dense=weight_dense,
        weight_sparse=weight_sparse,
        rerank=rerank
    )
    
    with open(filepath, "w") as f:
        json.dump(eval_dataset, f)

    
else:
    print(f"Loading already populated evaluation dataset from {filepath}...")

    with open(filepath, "r") as f:
        eval_dataset = json.load(f)


# ---- Instantiate metrics ----
from ragas.metrics import (
    AnswerRelevancy,
    Faithfulness,
    ContextPrecision,
    ContextRecall,
    AnswerSimilarity
)

metrics_to_compute = [
    AnswerRelevancy(),
    Faithfulness(),
    ContextPrecision(),
    ContextRecall(),
    AnswerSimilarity()
]

# ---- Evaluate ----

print("Starting evaluation...")

# Prepare your dataset
dataset = Dataset.from_list(eval_dataset)
dataset = dataset.rename_columns({
    "question": "user_input",
    "bot_answer": "response",
    "answer": "reference"
})

# Create evaluator LLM
llm = llm_factory("gpt-3.5-turbo", provider="openai", 
                  client=client)

# Create embeddings via langchain_openai
embeddings = OpenAIEmbeddings(model=f"text-embedding-3-{embeddings_type}")

# Evaluate
result = evaluate(dataset, embeddings=embeddings, 
                  llm=llm, allow_nest_asyncio=True) # , metrics=metrics_to_compute


print(f"{filename}: \n\n{result}")