from schemas.common import APIResponse


def success_response(data=None, message: str | None = None) -> APIResponse:
    return APIResponse(
        success=True,
        success_message=message,
        data=data,
    )


def error_response(message: str) -> APIResponse:
    return APIResponse(
        success=False,
        error_message=message,
    )
