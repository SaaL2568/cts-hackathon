export interface Citation {
  docName: string;
  pageNum: number;
  snippet: string;
}

export interface ChatTurn {
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  refused: boolean;
  timestamp: string;
}

export interface QueryResponse {
  sessionId: string;
  answer: string;
  citations: Citation[];
  confidence: number;
  refused: boolean;
  refusalReason: string | null;
}

export interface UploadDocumentResponse {
  docName: string;
  chunksIndexed: number;
  pagesProcessed: number;
}

export interface CreateSessionResponse {
  sessionId: string;
}

export interface SessionHistoryResponse {
  sessionId: string;
  turns: ChatTurn[];
}

export interface ListDocumentsResponse {
  documents: string[];
}
