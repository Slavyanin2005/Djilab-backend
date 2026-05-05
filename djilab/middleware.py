import logging
import time

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration = time.time() - start_time

        # Уровень: WARN для 4xx/5xx, иначе INFO
        level = logging.WARNING if response.status_code >= 400 else logging.INFO

        logger.log(level, f"{request.method} {request.path} | {response.status_code} | {duration:.3f}s")
        return response
