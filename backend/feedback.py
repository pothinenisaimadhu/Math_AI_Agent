
import os, json, datetime
FEEDBACK_STORE = os.getenv("FEEDBACK_STORE", "feedback_store.json")

def store_feedback(payload: dict):
    payload['_received_at'] = datetime.datetime.utcnow().isoformat() + "Z"
    try:
        with open(FEEDBACK_STORE, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception as e:
        print("Failed to store feedback:", e)
