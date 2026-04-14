"""
Request timing middleware.
Logs every request with its duration in ms.
Enabled in production via MIDDLEWARE setting.
"""
import time
import logging

logger = logging.getLogger('mesenu.timing')


class RequestTimingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        t0 = time.monotonic()
        response = self.get_response(request)
        ms = (time.monotonic() - t0) * 1000
        logger.info(
            '%s %s %s %.1fms',
            request.method,
            request.path,
            response.status_code,
            ms,
        )
        # Add timing header so Nginx logs show it too
        response['X-Response-Time'] = f'{ms:.1f}ms'
        return response
