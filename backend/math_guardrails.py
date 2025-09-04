
import re
def contains_pii(text: str) -> bool:
    email_re = r"[\w\.-]+@[\w\.-]+\.\w+"
    phone_re = r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}"
    if re.search(email_re, text) or re.search(phone_re, text):
        return True
    return False

def sanitize_text(text: str) -> str:
    return text.replace("\x00", "").strip()

def build_prompt_with_docs(docs, question: str, grade: str = "intermediate") -> str:
    ctx = ""
    for i, d in enumerate(docs):
        src = d.get('source_id', d.get('source','unknown'))
        snippet = d.get('snippet') or d.get('content') or ""
        ctx += f"Context {i+1} (source:{src}):\n{snippet}\n\n"
    prompt = f"""You are a math professor. Target grade: {grade}.
Context:
{ctx}
Question:
{question}
Provide numbered steps, 1-..., a 1-line summary, and final answer in LaTeX if applicable. Mark steps as [sourced] if from context and [derived] otherwise."""
    return prompt
