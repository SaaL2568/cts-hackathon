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
        self._sessionUsers: dict[str, str] = {}
        self._lock = threading.Lock()

    def _sessionFilePath(self, sessionId: str) -> Path:
        return settings.sessionPersistDir / f"{sessionId}.json"

    def _loadFromDisk(self, sessionId: str) -> tuple[str, list[ChatTurn]]:
        filePath = self._sessionFilePath(sessionId)
        if not filePath.exists():
            return "default_user", []
        try:
            with open(filePath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                userId = data.get("userId", "default_user")
                rawTurns = data.get("turns", [])
            elif isinstance(data, list):
                userId = "default_user"
                rawTurns = data
            else:
                userId = "default_user"
                rawTurns = []
            turns = [ChatTurn.model_validate(turn) for turn in rawTurns]
            return userId, turns
        except Exception as exc:
            logger.error("Failed to load session %s from disk: %s", sessionId, exc)
            return "default_user", []

    def createSession(self, userId: str = "default_user") -> str:
        sessionId = str(uuid.uuid4())
        filePath = self._sessionFilePath(sessionId)
        filePath.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            self._sessions[sessionId] = []
            self._sessionUsers[sessionId] = userId
            try:
                with open(filePath, "w", encoding="utf-8") as f:
                    json.dump({"userId": userId, "turns": []}, f, indent=2)
            except Exception as exc:
                logger.error("Failed to initialize session file %s: %s", filePath, exc)
        return sessionId

    def getSessionHistory(self, sessionId: str) -> list[ChatTurn]:
        with self._lock:
            if sessionId not in self._sessions:
                userId, turns = self._loadFromDisk(sessionId)
                self._sessions[sessionId] = turns
                self._sessionUsers[sessionId] = userId
            return list(self._sessions[sessionId])

    def getSessionUserId(self, sessionId: str) -> str:
        with self._lock:
            if sessionId not in self._sessionUsers:
                userId, turns = self._loadFromDisk(sessionId)
                self._sessions[sessionId] = turns
                self._sessionUsers[sessionId] = userId
            return self._sessionUsers.get(sessionId, "default_user")

    def appendTurn(self, sessionId: str, turn: ChatTurn) -> None:
        with self._lock:
            if sessionId not in self._sessions:
                userId, turns = self._loadFromDisk(sessionId)
                self._sessions[sessionId] = turns
                self._sessionUsers[sessionId] = userId

            turns = self._sessions[sessionId]
            turns.append(turn)
            userId = self._sessionUsers.get(sessionId, "default_user")

            filePath = self._sessionFilePath(sessionId)
            filePath.parent.mkdir(parents=True, exist_ok=True)
            try:
                serializedTurns = [t.model_dump(mode="json") for t in turns]
                payload = {"userId": userId, "turns": serializedTurns}
                with open(filePath, "w", encoding="utf-8") as f:
                    json.dump(payload, f, indent=2)
            except Exception as exc:
                logger.error("Failed to persist turn for session %s: %s", sessionId, exc)

    def exists(self, sessionId: str) -> bool:
        with self._lock:
            if sessionId in self._sessions:
                return True
            return self._sessionFilePath(sessionId).exists()

    def listSessionIds(self, userId: Optional[str] = None) -> list[str]:
        with self._lock:
            allIds = set(self._sessions.keys())
            if settings.sessionPersistDir.exists():
                for p in settings.sessionPersistDir.glob("*.json"):
                    allIds.add(p.stem)

            if userId is None:
                return sorted(list(allIds))

            matchingIds = []
            for sId in sorted(list(allIds)):
                owner = self.getSessionUserId(sId)
                if owner == userId:
                    matchingIds.append(sId)
            return matchingIds
