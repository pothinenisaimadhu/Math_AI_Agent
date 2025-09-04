import argparse, json, os
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from config import QDRANT_URL, QDRANT_COLLECTION

def ensure_collection(client, name, dim=384):
    try:
        client.get_collection(name)
        print("Collection exists:", name)
    except Exception:
        if client.collection_exists(name):
            client.delete_collection(name)
        client.create_collection(
            collection_name=name,
            vectors_config=rest.VectorParams(size=dim, distance=rest.Distance.COSINE),
        )
        print("Created collection:", name)

def create_hash_vector(text, dim=384):
    """Create a deterministic vector from text hash"""
    h = abs(hash(text))
    return [((h >> (i % 32)) & 0xFF)/255.0 for i in range(dim)]

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument("--data-file", default="math_dataset.json", help="JSON file containing math problems")
    p.add_argument("--enhanced", action="store_true", help="Use enhanced math dataset")
    args = p.parse_args()
    
    client = QdrantClient(url=QDRANT_URL)
    ensure_collection(client, QDRANT_COLLECTION)
    
    with open(args.data_file, "r", encoding="utf-8") as f:
        docs = json.load(f)
    
    for d in docs:
        qtext = d.get("question")
        vec = create_hash_vector(qtext)
        
        # Enhanced document structure
        content = f"""Question: {qtext}

Topic: {d.get('topic', 'mathematics')}
Grade Level: {d.get('grade_level', 'intermediate')}

Solution Steps:
""" + "\n".join([f"{i+1}. {step}" for i, step in enumerate(d.get('solution_steps', []))]) + f"\n\nFinal Answer: {d.get('final_answer', '')}\n\nEducational Notes: {d.get('educational_notes', '')}"
        
        payload = {
            "page_content": content,
            "metadata": {
                "topic": d.get("topic", "mathematics"),
                "grade_level": d.get("grade_level", "intermediate"),
                "source_id": d.get("id"),
                "educational_notes": d.get("educational_notes", "")
            }
        }
        
        point_id = abs(hash(d.get("id"))) % (2**63 - 1)
        client.upsert(collection_name=QDRANT_COLLECTION, points=[rest.PointStruct(id=point_id, vector=vec, payload=payload)])
        print("Upserted", d.get("id"))
