import chromadb

paths = {
    'chromaDB': r'C:\Users\BHAKTI\OneDrive\Desktop\ReCircle\EPR ChatBot\chromaDB',
    'chromaDB1': r'C:\Users\BHAKTI\OneDrive\Desktop\ReCircle\EPR ChatBot\chromaDB1',
    'DB1': r'C:\Users\BHAKTI\OneDrive\Desktop\ReCircle\EPR ChatBot\DB1',
}

for name, path in paths.items():
    try:
        client = chromadb.PersistentClient(path=path)
        collections = client.list_collections()
        print(f"\n{name} ({path}):")
        for c in collections:
            print(f"  {c.name}: {c.count()} docs")
            # Check for timeline data
            try:
                results = c.query(query_texts=["2024-25 timeline"], n_results=1)
                if results['documents'][0]:
                    print(f"    ✅ Has 2024-25 data")
            except:
                pass
    except Exception as e:
        print(f"\n{name}: Error - {e}")
