import threading
import uuid
from collections import OrderedDict
from typing import Optional

from ..config import settings
from ..models.schemas import ChatTurn


class ChatSessionManager:
    def __init__(self):
        self._sessions: "OrderedDict[str, list[ChatTurn]]" = OrderedDict()
        self._lock = threading.Lock()

    def createSession(self) -> str:
        sessionId = str(uuid.uuid4())
        with self._lock:
            self._sessions[sessionId] = []
        return sessionId

    def getSessionHistory(self, sessionId: str) -> list[ChatTurn]:
        with self._lock:
            return list(self._sessions.get(sessionId, []))

    def appendTurn(self, sessionId: str, turn: ChatTurn) -> None:
        with self._lock:
            turns = self._sessions.setdefault(sessionId, [])
            turns.append(turn)
            if len(turns) > settings.maxHistoryTurns:
                del turns[: len(turns) - settings.maxHistoryTurns]

    def exists(self, sessionId: str) -> bool:
        with self._lock:
            return sessionId in self._sessions
