from fastapi import FastAPI
from contracts import SearchRequest, PassageResult, SearchResponse

app = FastAPI(title="Knowledge Service (Mock)", version="0.1.0")

MOCK_PASSAGES = [
    PassageResult(
        text="Primary caregivers are entitled to 26 weeks of paid parental leave, and secondary caregivers receive 4 weeks of paid leave under the Global Parental Leave Policy.",
        source_file="reckitt_global_parental_leave_policy.pdf",
        page=1,
        score=0.8912,
        chunk_id="doc_036_p1_c01",
        title="Global Parental Leave Policy",
        company="Reckitt",
    ),
    PassageResult(
        text="Any aggrieved employee may submit a written complaint of sexual harassment to the Internal Complaints Committee within three months from the date of the incident.",
        source_file="susan_electricals_posh_anti_sexual_harassment_policy.pdf",
        page=4,
        score=0.8425,
        chunk_id="doc_046_p4_c01",
        title="Posh Anti Sexual Harassment Policy",
        company="Susan Electricals India Limited",
    ),
    PassageResult(
        text="Protected disclosures under the Vigil Mechanism / Whistleblower Policy should be addressed in writing to the Vigilance and Ethics Officer or the Audit Committee Chairman.",
        source_file="susan_electricals_vigil_mechanism_whistleblower_policy.pdf",
        page=2,
        score=0.8104,
        chunk_id="doc_050_p2_c01",
        title="Vigil Mechanism Whistleblower Policy",
        company="Susan Electricals India Limited",
    ),
]


@app.post("/search", response_model=SearchResponse)
def mock_search(payload: SearchRequest) -> SearchResponse:
    if "no_match" in payload.question.lower():
        return SearchResponse(results=[], no_match=True, embedding_model="all-MiniLM-L6-v2")

    threshold = payload.score_threshold if payload.score_threshold is not None else 0.0
    filtered = [p for p in MOCK_PASSAGES if p.score >= threshold][: (payload.top_k or 3)]
    return SearchResponse(
        results=filtered,
        no_match=len(filtered) == 0,
        embedding_model="all-MiniLM-L6-v2",
    )


@app.get("/health")
def health():
    return {"status": "healthy", "mode": "mock"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
