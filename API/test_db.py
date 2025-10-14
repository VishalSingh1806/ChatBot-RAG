import chromadb

client = chromadb.PersistentClient(path='./chroma_db')
collection = client.get_collection('EPR-chatbot')
results = collection.query(query_texts=['What is EPR'], n_results=3)

print('Query results:')
for i, doc in enumerate(results['documents'][0]):
    distance = results['distances'][0][i] if results['distances'] else 0
    print(f'Distance: {distance:.4f}')
    print(f'Text: {doc[:200]}...')
    print('---')