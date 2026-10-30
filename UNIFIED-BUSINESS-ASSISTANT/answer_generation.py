import os
import sys
import requests
from dotenv import load_dotenv

from retrieval_pipeline import retrieve

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()
parent_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
if os.path.exists(parent_env):
    load_dotenv(parent_env)


def build_rag_context(results: list) -> str:
    context_blocks = []
    for idx, item in enumerate(results, 1):
        block = (
            f"[Passage {idx}]\n"
            f"Source: {item['source_file']} (Page {item['page']})\n"
            f"Company: {item['company']}\n"
            f"Chunk ID: {item['chunk_id']}\n"
            f"Content:\n{item['text'].strip()}"
        )
        context_blocks.append(block)
    return "\n\n".join(context_blocks)


def call_gemini(prompt: str, api_key: str, model_name: str = "gemini-2.0-flash") -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 800},
    }
    resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=20)
    if resp.status_code == 200:
        data = resp.json()
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                return parts[0].get("text", "").strip()
    elif model_name != "gemini-1.5-flash":
        return call_gemini(prompt, api_key, model_name="gemini-1.5-flash")
    raise RuntimeError(f"Gemini API error ({resp.status_code}): {resp.text}")


def call_groq(system_prompt: str, user_prompt: str, api_key: str, model_name: str = "llama-3.3-70b-versatile") -> str:
    from openai import OpenAI

    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key)
    resp = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=800,
    )
    return resp.choices[0].message.content.strip()


def generate_answer(question: str, top_k: int = 4, score_threshold: float = 0.35) -> dict:
    search_response = retrieve(question, top_k=top_k, score_threshold=score_threshold)

    if search_response.get("no_match") or not search_response.get("results"):
        return {
            "question": question,
            "answer": "Insufficient information in the policy documents to answer this question.",
            "citations": [],
            "status": "no_match",
            "model_used": "none",
        }

    results = search_response["results"]
    rag_context = build_rag_context(results)

    citations = [
        {
            "source": item["source_file"],
            "page": item["page"],
            "chunk_id": item["chunk_id"],
            "company": item["company"],
            "confidence_score": item["score"],
        }
        for item in results
    ]

    system_prompt = (
        "Answer the user's question using only the provided policy passages. "
        "Cite the source document name and page number for every rule or policy fact."
    )
    user_prompt = f"Question: {question}\n\nDocument Passages:\n{rag_context}\n\nAnswer:"
    full_prompt = f"{system_prompt}\n\n{user_prompt}"

    generated_text = None
    model_used = None

    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if gemini_key and gemini_key.strip():
        try:
            generated_text = call_gemini(full_prompt, gemini_key.strip())
            model_used = "gemini-2.0-flash"
        except Exception:
            pass

    if not generated_text:
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key and groq_key.strip():
            try:
                generated_text = call_groq(system_prompt, user_prompt, groq_key.strip())
                model_used = "llama-3.3-70b-versatile"
            except Exception:
                pass

    if not generated_text:
        model_used = "local_extractive"
        answer_parts = ["Relevant policy excerpts:\n"]
        for idx, item in enumerate(results, 1):
            cleaned_excerpt = item["text"][:350].replace("\n", " ").strip()
            answer_parts.append(
                f"[{idx}] {item['company']} - {item['title']} ({item['source_file']}, p. {item['page']})\n"
                f'    "{cleaned_excerpt}..."'
            )
        generated_text = "\n\n".join(answer_parts)

    return {
        "question": question,
        "answer": generated_text,
        "citations": citations,
        "model_used": model_used,
        "status": "success",
        "results_count": len(results),
    }


def print_rag_result(result_dict: dict):
    print(f"\nQuestion: {result_dict['question']}")
    print(f"Model: {result_dict.get('model_used')} | Status: {result_dict['status']}")
    print(f"\nAnswer:\n{result_dict['answer']}")
    print("\nCitations:")
    for idx, c in enumerate(result_dict["citations"], 1):
        print(f"  [{idx}] {c['source']} (p. {c['page']}) | Score: {c['confidence_score']:.4f} | {c['chunk_id']}")


def main():
    if len(sys.argv) > 1:
        user_query = " ".join(sys.argv[1:])
        res = generate_answer(user_query)
        print_rag_result(res)
        return

    query = "What is the policy and grievance procedure for Prevention of Sexual Harassment (POSH)?"
    res = generate_answer(query)
    print_rag_result(res)


if __name__ == "__main__":
    main()
