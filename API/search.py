import pandas as pd
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("all-MiniLM-L6-v2")

# Load and clean CSV
df = pd.read_csv("data/knowledge.csv")

# Drop rows with missing questions or answers
df = df.dropna(subset=["question", "answer"])

# Ensure all questions are strings
df["question"] = df["question"].astype(str)

# Compute embeddings
df["embedding"] = df["question"].apply(lambda x: model.encode(x, convert_to_tensor=True))

def find_best_answer(user_query: str) -> dict:
    query_vec = model.encode(user_query, convert_to_tensor=True)
    scores = [util.cos_sim(query_vec, row)[0][0].item() for row in df["embedding"]]

    # Get top 4 most relevant indices (1 main answer + 3 suggestions)
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:4]
    top_matches = df.iloc[top_indices]

    answer = top_matches.iloc[0]["answer"]
    similar_questions = list(top_matches.iloc[1:]["question"])

    return {
        "answer": answer,
        "suggestions": similar_questions
    }
