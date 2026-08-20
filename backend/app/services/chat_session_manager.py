import json
import logging
import threading
import uuid
from collections import OrderedDict
from pathlib import Path
from typing import Optional

from ..config import settings
from ..models.schemas import ChatTurn

logger = logging.getLogger(__name__)


class ChatSessionManager:
    def __init__(self):
        self._sessions: "OrderedDict[str, list[ChatTurn]]" = OrderedDict()
        self._lock = threading.Lock()

    def _sessionFilePath(self, sessionId: str) -> Path:
        return settings.sessionPersistDir / f"{sessionId}.json"

    def createSession(self) -> str:
        sessionId = str(uuid.uuid4())
        filePath = self._sessionFilePath(sessionId)
        filePath.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            self._sessions[sessionId] = []
            try:
                with open(filePath, "w", encoding="utf-8") as f:
                    json.dump([], f)
            except Exception as exc:
                logger.error("Failed to initialize session file %s: %s", filePath, exc)
        return sessionId

    def getSessionHistory(self, sessionId: str) -> list[ChatTurn]:
        with self._lock:
            if sessionId not in self._sessions:
                filePath = self._sessionFilePath(sessionId)
                if filePath.exists():
                    try:
                        with open(filePath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        turns = [ChatTurn.model_validate(turn) for turn in data]
                        self._sessions[sessionId] = turns
                    except Exception as exc:
                        logger.error("Failed to load session %s from disk: %s", sessionId, exc)
                        return []
                else:
                    return []
            return list(self._sessions[sessionId])

    def appendTurn(self, sessionId: str, turn: ChatTurn) -> None:
        with self._lock:
            if sessionId not in self._sessions:
                filePath = self._sessionFilePath(sessionId)
                if filePath.exists():
                    try:
                        with open(filePath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        self._sessions[sessionId] = [ChatTurn.model_validate(t) for t in data]
                    except Exception:
                        self._sessions[sessionId] = []
                else:
                    self._sessions[sessionId] = []

            turns = self._sessions[sessionId]
            turns.append(turn)

            filePath = self._sessionFilePath(sessionId)
            filePath.parent.mkdir(parents=True, exist_ok=True)
            try:
                serialized = [t.model_dump(mode="json") for t in turns]
                with open(filePath, "w", encoding="utf-8") as f:
                    json.dump(serialized, f, indent=2)
            except Exception as exc:
                logger.error("Failed to persist turn for session %s: %s", sessionId, exc)

    def exists(self, sessionId: str) -> bool:
        with self._lock:
            if sessionId in self._sessions:
                return True
            return self._sessionFilePath(sessionId).exists()

    def listSessionIds(self) -> list[str]:
        with self._lock:
            sessionFiles = []
            if settings.sessionPersistDir.exists():
                for p in settings.sessionPersistDir.glob("*.json"):
                    sessionFiles.append((p.stem, p.stat().st_mtime))
            
            # Sort by modification time, newest first
            sessionFiles.sort(key=lambda x: x[1], reverse=True)
            return [stem for stem, _mtime in sessionFiles]
