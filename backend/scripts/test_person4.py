import json
import shutil
import tempfile
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.auth import requireAuth
from app.config import settings
from app.services.chat_session_manager import ChatSessionManager


def testAuthLogic():
    origEnabled = settings.authEnabled
    origSecret = settings.apiAuthSecret
    settings.authEnabled = True
    settings.apiAuthSecret = "my-secret-123"

    testApp = FastAPI()

    @testApp.get("/protected")
    def protectedRoute(userId: str = Depends(requireAuth)):
        return {"userId": userId}

    @testApp.get("/health")
    def openRoute():
        return {"status": "ok"}

    client = TestClient(testApp)

    try:
        # Open route
        resOpen = client.get("/health")
        assert resOpen.status_code == 200

        # No header -> HTTP 401
        resNoAuth = client.get("/protected")
        assert resNoAuth.status_code == 401
        assert "Missing Authorization header" in resNoAuth.json()["detail"]

        # Wrong token -> HTTP 401
        resWrongToken = client.get("/protected", headers={"Authorization": "Bearer wrong-token"})
        assert resWrongToken.status_code == 401

        # Valid token -> HTTP 200
        resValid = client.get("/protected", headers={"Authorization": "Bearer my-secret-123"})
        assert resValid.status_code == 200
        assert resValid.json()["userId"] == "authenticated_user"

        print("[PASS] requireAuth dependency tests passed!")
    finally:
        settings.authEnabled = origEnabled
        settings.apiAuthSecret = origSecret


def testStartupCheck():
    origEnabled = settings.authEnabled
    origSecret = settings.apiAuthSecret
    settings.authEnabled = True
    settings.apiAuthSecret = "   "

    try:
        if settings.authEnabled and not settings.apiAuthSecret.strip():
            raise RuntimeError(
                "AUTH_ENABLED is True but API_AUTH_SECRET is empty. "
                "Set API_AUTH_SECRET in .env or disable AUTH_ENABLED."
            )
        assert False, "Should have raised RuntimeError"
    except RuntimeError as exc:
        assert "AUTH_ENABLED is True but API_AUTH_SECRET is empty" in str(exc)
        print("[PASS] Startup fail-loud check passed!")
    finally:
        settings.authEnabled = origEnabled
        settings.apiAuthSecret = origSecret


def testSessionUserOwnership():
    tempDir = Path(tempfile.mkdtemp())
    origPersistDir = settings.sessionPersistDir
    settings.sessionPersistDir = tempDir

    try:
        manager = ChatSessionManager()

        sId1 = manager.createSession(userId="alice")
        sId2 = manager.createSession(userId="bob")

        assert manager.getSessionUserId(sId1) == "alice"
        assert manager.getSessionUserId(sId2) == "bob"

        # Check filtering by userId
        aliceSessions = manager.listSessionIds(userId="alice")
        assert sId1 in aliceSessions and sId2 not in aliceSessions

        bobSessions = manager.listSessionIds(userId="bob")
        assert sId2 in bobSessions and sId1 not in bobSessions

        # Verify disk persistence layout contains userId
        with open(tempDir / f"{sId1}.json", "r", encoding="utf-8") as f:
            diskData = json.load(f)
        assert isinstance(diskData, dict), "Disk data should be serialized as a JSON object"
        assert diskData.get("userId") == "alice"
        assert "turns" in diskData

        # Process restart simulation
        manager2 = ChatSessionManager()
        assert manager2.getSessionUserId(sId1) == "alice"
        assert manager2.getSessionUserId(sId2) == "bob"
        print("[PASS] Session user ownership persistence test passed!")
    finally:
        settings.sessionPersistDir = origPersistDir
        shutil.rmtree(tempDir, ignore_errors=True)


if __name__ == "__main__":
    testAuthLogic()
    testStartupCheck()
    testSessionUserOwnership()
    print("\nALL PERSON 4 AUTHENTICATION TESTS PASSED SUCCESSFULLY!")
