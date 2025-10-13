import chromadb

def find_embedding_model():
    """Try different models to find the one that matches Langflow"""
    
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_collection("EPR-chatbot")
    
    # Test query
    test_query = "what is EPR"
    
    models_to_try = [
        'sentence-transformers/all-MiniLM-L6-v2',  # 384 dim
        'sentence-transformers/all-mpnet-base-v2',  # 768 dim
        'sentence-transformers/all-MiniLM-L12-v2',  # 384 dim
        'sentence-transformers/paraphrase-MiniLM-L6-v2',  # 384 dim
    ]
    
    for model_name in models_to_try:
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(model_name)
            
            # Generate embedding
            embedding = model.encode(test_query).tolist()
            
            # Try to query
            results = collection.query(
                query_embeddings=[embedding],
                n_results=3
            )
            
            if results['documents'][0]:
                best_distance = results['distances'][0][0]
                print(f"\n{model_name}:")
                print(f"  Dimensions: {len(embedding)}")
                print(f"  Best distance: {best_distance:.4f}")
                print(f"  Sample result: {results['documents'][0][0][:100]}...")
                
                if best_distance < 1.0:  # Good match
                    print(f"  *** GOOD MATCH! ***")
                    
        except Exception as e:
            print(f"{model_name}: ERROR - {e}")

if __name__ == "__main__":
    find_embedding_model()