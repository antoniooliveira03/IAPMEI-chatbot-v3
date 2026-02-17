from tqdm import tqdm
import chatbot

def json_to_documents(data: dict):
    """Convert the JSON data into a list of documents for evaluation."""
    documents = []

    for source, content in data.items():
        qa_list = content.get("perguntas_respostas", [])

        for item in qa_list:
            documents.append({
                "question": item.get("pergunta", ""),
                "answer": item.get("resposta", ""),
                "source": source
            })

    return documents


def populate_eval_dataset(eval_dataset, index, metadata, bm25, 
                          model="gpt-4o-mini", k=20, top_k=5, 
                          weight_dense=0.6, weight_sparse=0.4, rerank=False):
    """
    Fill the 'answer' and 'contexts' fields in the evaluation dataset
    by calling your bot function.

    Args:
        eval_dataset (list ofuti dicts): each dict must have 'question' and optionally 'source'
        index, metadata, bm25: your RAG components
        model, k, top_k, weight_dense, weight_sparse, rerank: bot settings

    Returns:
        list of dicts: same dataset with 'answer' and 'contexts' populated
    """
    updated_dataset = []

    for sample in tqdm(eval_dataset, desc="Generating bot answers"):
        question = sample["question"]
        # Optional: use sample['source'] if needed by retriever
        source = sample.get("source", "")

        # Call your existing bot
        generated_answer, context_chunks = chatbot.answer(
            user_query=question,
            index=index,
            metadata=metadata,
            bm25=bm25,
            model=model,
            k=k,
            top_k=top_k,
            weight_dense=weight_dense,
            weight_sparse=weight_sparse,
            rerank=rerank
        )

        # Save results back into sample
        sample["bot_answer"] = generated_answer
        sample["contexts"] = [c["content"] for c in context_chunks]

        updated_dataset.append(sample)

    return updated_dataset
