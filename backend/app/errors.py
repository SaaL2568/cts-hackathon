class IngestionError(Exception):
    """Raised when a document cannot be parsed or indexed."""


class RetrievalError(Exception):
    """Raised when the vector store cannot be queried."""


class AnswerGenerationError(Exception):
    """Raised when the LLM cannot be reached or produced no answer."""


class SummarizationError(Exception):
    """Raised when summarization fails or is misconfigured."""
