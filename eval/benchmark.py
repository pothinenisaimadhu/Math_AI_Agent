
import requests, time, json
API = "http://localhost:8000/solve"
def run(questions):
    results = []
    for q in questions:
        t0 = time.time()
        r = requests.post(API, json={"user_id":"bench","question": q['text']}, timeout=60)
        t1 = time.time()
        data = r.json()
        results.append({"id": q['id'], "time": t1-t0, "source": data.get('source'), "answer_snippet": str(data.get('answer',''))[:400]})
    print(json.dumps(results, indent=2))
if __name__ == '__main__':
    sample = [{"id":"q1","text":"Evaluate the integral ∫_0^∞ x^2 e^{-x^2} dx."}]
    run(sample)
