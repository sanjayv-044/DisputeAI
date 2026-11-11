
import os
import requests

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-3.8-flash:generateContent"
)

def generate_rag_answer(question, evidence, timeout=90):
    evidence_text = ""

    for item in evidence[:3]:
        evidence_text += f"""
Source: {item['source']}
Page: {item['page']}
Status: {item['status']}
Scope: {item['scope']}
Evidence: {item['text'][:1000]}
--------------------
"""

    prompt = f"""
You are DisputeAI's RBI regulatory assistant.

Answer using only the evidence provided.

Question:
{question}

Evidence:
{evidence_text}

Instructions:
- Cite source names and page numbers.
- Never present withdrawn 2017 rules as current law.
- Distinguish historical from current evidence.
- Do not invent RBI rules or bank policies.
- Identify missing current regulations.
- Recommend human review if liability cannot be determined.
"""

    response = requests.post(
        GEMINI_URL,
        params={"key": os.environ["GEMINI_API_KEY"]},
        json={
            "contents": [
                {"parts": [{"text": prompt}]}
            ]
        },
        timeout=timeout
    )

    response.raise_for_status()
    result = response.json()

    return result["candidates"][0]["content"]["parts"][0]["text"]
