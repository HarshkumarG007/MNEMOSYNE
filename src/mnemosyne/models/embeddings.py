from typing import List

from .llm_router import router


async def embed(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of texts using the BGE-M3 model via the LLM Router.
    Processes in batches of 32 texts max to manage memory usage.
    
    Args:
        texts: A list of string texts to embed.
        
    Returns:
        A list of embedding vectors, one for each input text.
    """
    batch_size = 32
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        # In a real batched inference, the model would take a list of strings.
        # But llama_cpp doesn't support batch embeddings cleanly without custom low-level loops.
        # So we process them individually but grouped to simulate batch flow control.
        # Future optimization: utilize Llama(..., embedding=True).create_embedding(batch) if supported.
        for text in batch:
            emb = await router.embed(text)
            all_embeddings.append(emb)
            
    return all_embeddings
