"""Manual MVP test pass against a running backend.

Usage:
  1. Start the backend:  uvicorn app.main:app --reload --port 8000
  2. Run from backend/:
       python -m scripts.test_mvp --pdf data/pdfs/eliquis.pdf

It uploads the PDF, asks several questions, and reports whether every answer
carries a citation and whether at least one question triggers a refusal.
"""

import argparse
import sys
from pathlib import Path

import httpx

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

QUESTIONS = [
    "What is the recommended starting dose for this drug?",
    "Does this drug carry a boxed warning?",
    "What are the common adverse reactions reported?",
    "How should this drug be stored?",
    "What is the population pharmacokinetics section about?",
    "What is the capital of France?",
    "Which foods should be avoided while taking this drug?",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="MVP test pass.")
    parser.add_argument("--pdf", required=True, help="Path to the sample PDF.")
    parser.add_argument("--base", default=BASE_URL, help="Backend base URL.")
    args = parser.parse_args()

    pdfPath = Path(args.pdf)
    if not pdfPath.exists():
        print(f"PDF not found: {pdfPath}")
        sys.exit(1)

    client = httpx.Client(timeout=180)
    uploadUrl = f"{args.base}/api/v1/uploadDocument"
    with pdfPath.open("rb") as handle:
        response = client.post(
            uploadUrl,
            files={"file": (pdfPath.name, handle, "application/pdf")},
        )
    if response.status_code != 200:
        print(f"UPLOAD FAILED: {response.status_code} {response.text}")
        sys.exit(1)
    upload = response.json()
    print(f"Uploaded: {upload}")

    sessionResponse = client.post(f"{args.base}/api/v1/createSession")
    sessionId = sessionResponse.json()["sessionId"]
    print(f"Session: {sessionId}\n")

    answerCount = 0
    refusalCount = 0
    missingCitationCount = 0

    for question in QUESTIONS:
        payload = {"sessionId": sessionId, "question": question}
        response = client.post(f"{args.base}/api/v1/queryChat", json=payload)
        if response.status_code != 200:
            print(f"[ERROR] {response.status_code}: {response.text}\n")
            continue
        result = response.json()
        print(f"Q: {question}")
        print(f"A: {result['answer']}")
        print(f"Confidence: {result['confidence']:.3f} | Refused: {result['refused']}")
        print(f"Citations: {len(result['citations'])}")
        for citation in result["citations"]:
            print(f"  - [{citation['docName']}, page {citation['pageNum']}]")
        if result["refused"]:
            refusalCount += 1
        else:
            answerCount += 1
            if not result["citations"]:
                missingCitationCount += 1
        print()

    print("=" * 60)
    print(f"Answered questions: {answerCount}")
    print(f"Refusals: {refusalCount}")
    print(f"Answers missing citations: {missingCitationCount}")

    passed = answerCount > 0 and refusalCount > 0 and missingCitationCount == 0
    print("PASS" if passed else "FAIL")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
