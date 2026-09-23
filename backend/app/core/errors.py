"""Application error types.

Services raise these; `app.main` converts them into friendly JSON responses.
Technical detail goes to the logs, never to the client.
"""

from __future__ import annotations


class AppError(Exception):
    status_code = 400
    code = "bad_request"
    default_message = "The request could not be completed."

    def __init__(self, message: str | None = None, *, code: str | None = None):
        self.message = message or self.default_message
        if code:
            self.code = code
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"
    default_message = "We couldn't find what you were looking for."


class ConflictError(AppError):
    status_code = 409
    code = "conflict"
    default_message = "This action conflicts with the current state."


class UnauthorizedError(AppError):
    status_code = 401
    code = "unauthorized"
    default_message = "Please sign in again."


class RateLimitError(AppError):
    status_code = 429
    code = "rate_limited"
    default_message = "You're doing that too quickly. Please wait a moment and try again."


class FileTooLargeError(AppError):
    status_code = 413
    code = "file_too_large"
    default_message = "That file is too large."


class UnsupportedFileError(AppError):
    status_code = 415
    code = "unsupported_file"
    default_message = "That file type isn't supported."


class NoContentError(ConflictError):
    """The subject has no usable indexed content yet."""

    code = "no_content"
    default_message = "Upload a document to this subject first."


class DocumentsNotReadyError(ConflictError):
    code = "documents_not_ready"
    default_message = "Your documents haven't finished processing yet."


class AIServiceError(AppError):
    status_code = 502
    code = "ai_generation_failed"
    default_message = "The AI couldn't complete that request. Please try again."


class AINotConfiguredError(AppError):
    status_code = 503
    code = "ai_not_configured"
    default_message = "The AI service isn't configured on the server."
