import chromadb
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# UDB path
UDB_PATH = r"c:\Users\BHAKTI\OneDrive\Desktop\ReCircle\EPR ChatBot\ChatBot-RAG\UDB\UDB"

# Connect to UDB
client = chromadb.PersistentClient(path=UDB_PATH)

# Delete existing collection and recreate
try:
    client.delete_collection(name="Updated_DB")
    print("Deleted old Updated_DB collection")
except:
    pass

collection = client.get_or_create_collection(name="Updated_DB")

print(f"Current documents in UDB: {collection.count()}")

# Updated timeline data for 2024-25 and 2025-26
timeline_data = [
    {
        "text": "For the financial year 2024-25 (April 1, 2024 – March 31, 2025), the deadline for filing the Plastic EPR Annual Return has been extended by the Central Pollution Control Board (CPCB) to November 30, 2025.",
        "metadata": {"source": "CPCB_2024-25_Update", "year": "2024-25", "type": "annual_return_deadline"}
    },
    {
        "text": "The annual report filing deadline for FY 2024-25 is November 30, 2025 as per CPCB notification.",
        "metadata": {"source": "CPCB_2024-25_Update", "year": "2024-25", "type": "annual_return_deadline"}
    },
    {
        "text": "For the financial year 2025-26, the deadline for filing the Plastic EPR Annual Return is January 31, 2026.",
        "metadata": {"source": "CPCB_2025-26_Update", "year": "2025-26", "type": "annual_return_deadline"}
    },
    {
        "text": "The annual report filing deadline for FY 2025-26 is January 31, 2026.",
        "metadata": {"source": "CPCB_2025-26_Update", "year": "2025-26", "type": "annual_return_deadline"}
    },
    {
        "text": "EPR certificates for plastic waste collected and recycled must be obtained quarterly throughout 2025-26. Q1 (April-June 2025): July 31, 2025. Q2 (July-September 2025): October 31, 2025. Q3 (October-December 2025): January 31, 2026. Q4 (January-March 2026): April 30, 2026. Upload them to the portal within the quarterly return deadlines to avoid Environmental Compensation.",
        "metadata": {"source": "CPCB_2025-26_Quarterly", "year": "2025-26", "type": "quarterly_obligations"}
    }
]

# Generate embeddings and add to collection
print("\nAdding updated timeline data to UDB...")
for i, item in enumerate(timeline_data):
    # Generate embedding
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=item["text"],
        task_type="retrieval_document"
    )
    embedding = result['embedding']
    
    # Add to collection
    collection.add(
        documents=[item["text"]],
        embeddings=[embedding],
        metadatas=[item["metadata"]],
        ids=[f"timeline_update_{i}"]
    )
    print(f"[OK] Added: {item['metadata']['year']} - {item['metadata']['type']}")

print(f"\n[OK] UDB updated! Total documents: {collection.count()}")
