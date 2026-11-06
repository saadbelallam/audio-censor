from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse


class CensurException(Exception):
    status_code = status.HTTP_400_BAD_REQUEST
    default_message = "Censor error"

    def __init__(self, message: str | None = None):
        self.message = message or self.default_message
        super().__init__(self.message)

class AudioNotFound(CensurException):
    status_code = status.HTTP_404_NOT_FOUND
    default_message = "Audio not found"

class InvalidFileFormat(CensurException):
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    default_message = "Invalid file format"


class APIException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


class AudioFileTooLarge(APIException):
    def __init__(self, max_size_mb: int):
        super().__init__(
            status.HTTP_413_CONTENT_TOO_LARGE,
            f"The audio file must not exceed {max_size_mb} MB.",
        )


class AudioDurationTooLong(APIException):
    def __init__(self, max_duration_seconds: int):
        super().__init__(
            status.HTTP_413_CONTENT_TOO_LARGE,
            f"The audio file duration must not exceed {max_duration_seconds} seconds.",
        )


class InvalidAudioFile(APIException):
    def __init__(self):
        super().__init__(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "Invalid file type. Please upload a valid audio file.",
        )


class UndecodableAudioFile(APIException):
    def __init__(self):
        super().__init__(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Invalid file type. Please upload a valid audio file.",
        )


class AudioNotFoundError(APIException):
    def __init__(self, detail: str = "Audio not found"):
        super().__init__(status.HTTP_404_NOT_FOUND, detail)


class AudioProcessingError(APIException):
    def __init__(self):
        super().__init__(
            status.HTTP_409_CONFLICT,
            "Audio is currently being processed. Please wait until processing is complete.",
        )


class SoundEffectNotFoundError(APIException):
    def __init__(self):
        super().__init__(status.HTTP_404_NOT_FOUND, "Sound effect not found")


class InsufficientCredits(APIException):
    def __init__(self):
        super().__init__(status.HTTP_402_PAYMENT_REQUIRED, "Insufficient credits")


class UserNotFoundError(APIException):
    def __init__(self):
        super().__init__(status.HTTP_404_NOT_FOUND, "User not found")


class CheckoutCreationError(APIException):
    def __init__(self, detail: str):
        super().__init__(status.HTTP_500_INTERNAL_SERVER_ERROR, detail)


class InvalidWebhookSignature(APIException):
    def __init__(self):
        super().__init__(status.HTTP_400_BAD_REQUEST, "Invalid webhook signature")


class ForbiddenWebhookSignature(APIException):
    def __init__(self):
        super().__init__(status.HTTP_403_FORBIDDEN, "Invalid webhook signature")

def add_exception_handlers(app: FastAPI):
    def exception_handler(request: Request, exc: CensurException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": exc.message},
        )

    @app.exception_handler(status.HTTP_500_INTERNAL_SERVER_ERROR)
    def internal_server_error_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Internal server error"},
        )

    app.add_exception_handler(CensurException, exception_handler)