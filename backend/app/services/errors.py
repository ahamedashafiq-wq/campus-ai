class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str = "error"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


class NotFound(AppError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, 404, "not_found")


class Forbidden(AppError):
    def __init__(self, message: str = "Not authorized"):
        super().__init__(message, 403, "forbidden")


class Conflict(AppError):
    def __init__(self, message: str = "Conflict"):
        super().__init__(message, 409, "conflict")


class Unauthorized(AppError):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, 401, "unauthorized")
