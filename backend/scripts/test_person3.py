import json
import shutil
import tempfile
from pathlib import Path

from app.config import settings
from app.models.schemas import ChatTurn, Citation
from app.services.chat_session_manager import ChatSessionManager
from app.services.retrieval_service import RetrievalService


def testSessionPersistence():
    tempDir = Path(tempfile.mkdtemp())
    origPersistDir = settings.sessionPersistDir
    settings.sessionPersistDir = tempDir

    try:
        manager1 = ChatSessionManager()
        sId = manager1.createSession()
        assert (tempDir / f"{sId}.json").exists(), "Session JSON file was not created on createSession"

        turn1 = ChatTurn(role="user", content="What's the dosage for Eliquis?")
        turn2 = ChatTurn(
            role="assistant",
            content="The recommended dose is 5 mg twice daily.",
            citations=[Citation(docName="eliquis", pageNum=1, snippet="5 mg twice daily")],
        )

        manager1.appendTurn(sId, turn1)
        manager1.appendTurn(sId, turn2)

        history1 = manager1.getSessionHistory(sId)
        assert len(history1) == 2, f"Expected 2 turns, got {len(history1)}"

        # Verify disk file content
        with open(tempDir / f"{sId}.json", "r", encoding="utf-8") as f:
            diskData = json.load(f)
        assert len(diskData) == 2, f"Expected 2 turns on disk, got {len(diskData)}"
        assert diskData[0]["role"] == "user"
        assert diskData[1]["role"] == "assistant"

        # Simulate process restart by initializing a fresh manager instance
        manager2 = ChatSessionManager()
        assert manager2.exists(sId), "Session should exist on disk after process restart"
        sIds = manager2.listSessionIds()
        assert sId in sIds, "Session ID should be in listSessionIds after process restart"

        history2 = manager2.getSessionHistory(sId)
        assert len(history2) == 2, f"Expected 2 turns after restart, got {len(history2)}"
        assert history2[0].content == "What's the dosage for Eliquis?"
        assert history2[1].content == "The recommended dose is 5 mg twice daily."
        print("[PASS] Session persistence unit test passed!")
    finally:
        settings.sessionPersistDir = origPersistDir
        shutil.rmtree(tempDir, ignore_errors=True)


def testContextualQuery():
    class DummyEmbeddingService:
        def embedText(self, text: str):
            return [0.0]

    service = RetrievalService(embeddingService=DummyEmbeddingService())

    # Case 1: No history
    q1 = "what is the dosage?"
    res1 = service._contextualizeQuery(q1, None)
    assert res1 == q1, f"Expected '{q1}', got '{res1}'"

    # Case 2: History with user turns
    history = [
        ChatTurn(role="user", content="what's the dosage for Eliquis?"),
        ChatTurn(role="assistant", content="The recommended dose is 5 mg twice daily."),
    ]
    q2 = "what about renal impairment?"
    res2 = service._contextualizeQuery(q2, history)
    assert "what's the dosage for Eliquis?" in res2, f"Expected previous context in contextualized query, got '{res2}'"
    assert res2.endswith("what about renal impairment?")
    print(f"[PASS] Contextual query test passed! Result: '{res2}'")


if __name__ == "__main__":
    testSessionPersistence()
    testContextualQuery()
    print("\nALL PERSON 3 VERIFICATION TESTS PASSED SUCCESSFULLY!")
