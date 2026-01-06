import chromadb
from google import genai
from google.genai import types
import time

def categorize_with_gemini(content, source):
    """Use Gemini to categorize content"""
    prompt = f"""
    Analyze this EPR document content and classify it into one of these categories:
    - producer: for manufacturers, production companies, MSME producers, manufacturing guidelines
    - importer: for import-related documents, importers, import regulations
    - branddonar: for brand donors, PIBOs (Producer, Importer, Brand Owner), brand responsibilities
    - general: for general EPR rules, guidelines, notices that apply to all stakeholders

    Document: {source}
    Content: {content[:500]}...

    Return only one word: producer, importer, branddonar, or general
    """
    
    try:
        client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))
        
        contents = [types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)]
        )]
        
        config = types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=10
        )
        
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",  # Use stable model with higher limits
            contents=contents,
            config=config
        )
        
        category = response.text.strip().lower()
        
        if category in ['producer', 'importer', 'branddonar', 'general']:
            return category
        else:
            return 'general'
    except Exception as e:
        print(f"Gemini error: {e}")
        return 'general'

def categorize_by_filename(source):
    """Simple filename-based categorization as fallback"""
    source_lower = source.lower()
    
    if any(word in source_lower for word in ['producer', 'manufacturing', 'msme', 'production']):
        return 'producer'
    elif any(word in source_lower for word in ['import', 'importer']):
        return 'importer'
    elif any(word in source_lower for word in ['brand', 'pibo', 'donor']):
        return 'branddonar'
    else:
        return 'general'

def divide_collections():
    client = chromadb.PersistentClient(path="./chroma_db")
    
    try:
        source_collection = client.get_collection("pdf_docs")
        print(f"📊 Source collection has {source_collection.count()} documents")
        
        results = source_collection.get(include=['documents', 'metadatas', 'embeddings'])
        print(f"📋 Retrieved {len(results['documents'])} documents to categorize")
        
    except Exception as e:
        print(f"❌ Error getting pdf_docs collection: {e}")
        return
    
    collections = {}
    for name in ['epr_producer', 'epr_importer', 'epr_branddonar', 'epr_general']:
        try:
            client.delete_collection(name)
        except:
            pass
        collections[name] = client.create_collection(name, metadata={"hnsw:space": "cosine"})
        print(f"✅ Created {name}")
    
    category_counts = {'producer': 0, 'importer': 0, 'branddonar': 0, 'general': 0}
    api_calls = 0
    
    for i, (doc, metadata, embedding) in enumerate(zip(results['documents'], results['metadatas'], results['embeddings'])):
        if i % 100 == 0:
            print(f"Progress: {i+1}/{len(results['documents'])}")
        
        source_file = metadata.get('source', 'unknown')
        
        # Use filename-based categorization first, then AI for unclear cases
        category = categorize_by_filename(source_file)
        
        # Only use AI for 'general' cases to reduce API calls
        if category == 'general' and api_calls < 50:  # Limit AI calls
            category = categorize_with_gemini(doc, source_file)
            api_calls += 1
            time.sleep(7)  # Wait 7 seconds between API calls (10/min limit)
        
        collection_name = f'epr_{category}'
        category_counts[category] += 1
        
        collections[collection_name].add(
            documents=[doc],
            metadatas=[{**metadata, 'category': category}],
            embeddings=[embedding],
            ids=[f"{category}_{i}"]
        )
    
    print("\n📊 Final Distribution:")
    for category, count in category_counts.items():
        print(f"   epr_{category}: {count} documents")
    
    total_distributed = sum(category_counts.values())
    print(f"\n✅ Successfully redistributed {total_distributed} documents into 4 categories")
    print(f"🤖 Used {api_calls} AI categorization calls")

if __name__ == "__main__":
    divide_collections()
