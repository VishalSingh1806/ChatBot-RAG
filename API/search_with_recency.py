"""
Enhanced search module with recency-based filtering and scoring
This is a Phase 1 implementation - collection prioritization
"""
import chromadb
import google.generativeai as genai
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from config import CHROMA_DB_PATHS, COLLECTIONS

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# Collection priority (newest to oldest)
# Updated_DB and UDB are newest, chromaDB is oldest
COLLECTION_PRIORITY = {
    "Updated_DB": 1.5,      # Newest - 50% boost
    "updated_db": 1.5,      # Newest - 50% boost
    "UDB": 1.3,             # Recent - 30% boost
    "FinalDB": 1.1,         # Medium - 10% boost
    "EPRChatbot-1": 1.0,    # Baseline
    "EPR-chatbot": 0.9,     # Older - 10% penalty
}

def get_collection_priority_multiplier(collection_name: str) -> float:
    """Get priority multiplier based on collection age"""
    for key, multiplier in COLLECTION_PRIORITY.items():
        if key.lower() in collection_name.lower():
            return multiplier
    return 1.0  # Default no boost/penalty


def find_best_answer_with_priority(user_query: str, intent_result=None, previous_suggestions: list = None) -> dict:
    """
    Enhanced search that prioritizes newer collections

    Algorithm:
    1. Query all collections
    2. Apply collection priority multiplier to similarity scores
    3. Return highest scoring result
    """
    logger.info(f"🔍 Searching with collection priority for: {user_query[:100]}...")

    # Initialize ChromaDB clients
    clients = {}
    for db_path in CHROMA_DB_PATHS:
        clients[db_path] = chromadb.PersistentClient(path=db_path)

    # Get all collections
    all_collections = {}
    for db_path, client in clients.items():
        for collection_name in COLLECTIONS.get(db_path, []):
            try:
                collection = client.get_collection(name=collection_name)
                all_collections[f"{collection_name}@{db_path}"] = {
                    'collection': collection,
                    'priority': get_collection_priority_multiplier(collection_name)
                }
                logger.info(f"✅ Collection '{collection_name}' priority: {all_collections[f'{collection_name}@{db_path}']['priority']}")
            except Exception as e:
                logger.warning(f"Collection '{collection_name}' not found in {db_path}: {e}")

    if not all_collections:
        logger.error("No collections available")
        return {
            "answer": "Database not ready.",
            "suggestions": [],
            "source_info": {}
        }

    # Generate query embedding
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=user_query,
            task_type="retrieval_query"
        )
        query_embedding = result['embedding']
    except Exception as e:
        logger.error(f"Error generating query embedding: {e}")
        return {
            "answer": "Error processing your query.",
            "suggestions": [],
            "source_info": {}
        }

    all_results = []

    # Query all collections
    for coll_key, coll_data in all_collections.items():
        collection = coll_data['collection']
        priority_multiplier = coll_data['priority']

        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=10
            )

            if results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    distance = results['distances'][0][i] if results['distances'] else 0

                    # Calculate semantic similarity (1 - distance, higher is better)
                    semantic_score = max(0, 1 - distance)

                    # Apply collection priority multiplier
                    final_score = semantic_score * priority_multiplier

                    all_results.append({
                        'document': doc,
                        'distance': distance,
                        'semantic_score': semantic_score,
                        'priority_multiplier': priority_multiplier,
                        'final_score': final_score,
                        'collection': coll_key,
                        'metadata': metadata,
                        'chunk_id': metadata.get('chunk_id', i),
                        'source': metadata.get('source', 'unknown')
                    })

                logger.info(f"📚 Found {len(results['documents'][0])} results from '{coll_key}' (priority: {priority_multiplier}x)")

        except Exception as e:
            logger.error(f"Error querying collection '{coll_key}': {e}")

    if not all_results:
        logger.warning("No results found")
        return {
            "answer": "I don't have information about that topic.",
            "suggestions": [],
            "source_info": {}
        }

    # Sort by final score (highest first)
    all_results.sort(key=lambda x: x['final_score'], reverse=True)

    # Get best result
    best_result = all_results[0]

    # Log scoring details for debugging
    logger.info(f"🏆 Best result from '{best_result['collection']}':")
    logger.info(f"   Semantic score: {best_result['semantic_score']:.4f}")
    logger.info(f"   Priority multiplier: {best_result['priority_multiplier']:.2f}x")
    logger.info(f"   Final score: {best_result['final_score']:.4f}")

    # Combine top 3 results for comprehensive answer
    combined_text = ""
    for result in all_results[:3]:
        doc = result['document']
        if len(doc) > 30:
            if combined_text:
                combined_text += "\n\n"
            combined_text += doc.strip()

    answer = combined_text if combined_text else best_result['document']

    # Generate suggestions (reuse existing function)
    from search import generate_related_questions
    suggestions = generate_related_questions(user_query, all_results[:3], intent_result, previous_suggestions)

    return {
        "answer": answer,
        "suggestions": suggestions,
        "source_info": {
            "collection_name": best_result['collection'],
            "chunk_id": best_result['chunk_id'],
            "source_document": best_result['source'],
            "semantic_score": round(best_result['semantic_score'], 4),
            "priority_multiplier": best_result['priority_multiplier'],
            "final_score": round(best_result['final_score'], 4)
        }
    }


def compare_search_methods(query: str):
    """
    Debug function to compare old vs new search
    Run this to see the difference in results
    """
    print(f"\n{'='*80}")
    print(f"COMPARING SEARCH METHODS FOR: {query}")
    print(f"{'='*80}\n")

    # Old method (no priority)
    from search import find_best_answer
    old_result = find_best_answer(query)

    print("OLD METHOD (No Priority):")
    print(f"  Source: {old_result['source_info'].get('source_document', 'N/A')}")
    print(f"  Collection: {old_result['source_info'].get('collection_name', 'N/A')}")
    print(f"  Confidence: {old_result['source_info'].get('confidence_score', 'N/A')}")
    print(f"  Answer: {old_result['answer'][:200]}...\n")

    # New method (with priority)
    new_result = find_best_answer_with_priority(query)

    print("NEW METHOD (With Collection Priority):")
    print(f"  Source: {new_result['source_info'].get('source_document', 'N/A')}")
    print(f"  Collection: {new_result['source_info'].get('collection_name', 'N/A')}")
    print(f"  Semantic Score: {new_result['source_info'].get('semantic_score', 'N/A')}")
    print(f"  Priority Multiplier: {new_result['source_info'].get('priority_multiplier', 'N/A')}x")
    print(f"  Final Score: {new_result['source_info'].get('final_score', 'N/A')}")
    print(f"  Answer: {new_result['answer'][:200]}...\n")

    print(f"{'='*80}\n")


if __name__ == "__main__":
    # Test the enhanced search
    test_queries = [
        "What is the annual report filing deadline for 2024-25?",
        "What are EPR compliance requirements?",
        "How to register for EPR?"
    ]

    for query in test_queries:
        result = find_best_answer_with_priority(query)
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print(f"Collection: {result['source_info']['collection_name']}")
        print(f"Final Score: {result['source_info']['final_score']:.4f}")
        print(f"Answer: {result['answer'][:300]}...")
        print(f"{'='*80}\n")
