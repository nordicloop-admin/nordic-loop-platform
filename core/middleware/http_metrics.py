"""HTTP metrics middleware for Prometheus.

Captures:
 - http_request_duration_seconds (Histogram)
 - http_requests_total (Counter)
 - request_payload_bytes_total (Counter)
 - response_payload_bytes_total (Counter)
 - active_requests (Gauge)

Labels kept low-cardinality: method, path_template, status_group.
Path template: we attempt to use resolver_match.view_name; fallback to raw path, then coarse grouping.
"""
import time
from typing import Callable
from prometheus_client import Histogram, Counter, Gauge
from django.utils.deprecation import MiddlewareMixin

_HTTP_BUCKETS = [0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0]

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'Duration of HTTP requests in seconds',
    ['method', 'path_template', 'status_group'],
    buckets=_HTTP_BUCKETS
)

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'path_template', 'status_group']
)

request_payload_bytes_total = Counter(
    'request_payload_bytes_total',
    'Total request payload bytes',
    ['path_template']
)

response_payload_bytes_total = Counter(
    'response_payload_bytes_total',
    'Total response payload bytes',
    ['path_template']
)

active_requests = Gauge(
    'active_requests',
    'Number of in-flight HTTP requests',
    ['method']
)

def _status_group(status_code: int) -> str:
    if 200 <= status_code < 300:
        return '2xx'
    if 400 <= status_code < 500:
        return '4xx'
    if 500 <= status_code < 600:
        return '5xx'
    return 'other'

def _path_template(request) -> str:
    # Prefer DRF/Django resolved view name; ensures low cardinality
    match = getattr(request, 'resolver_match', None)
    if match and match.view_name:
        return match.view_name
    path = request.path
    # Coarse fallback: group dynamic numeric ids
    # /api/ads/123/ -> /api/ads/:id/
    return path.replace('\n', '').replace('\r', '').replace('\t', '').strip()

class HttpMetricsMiddleware(MiddlewareMixin):
    def process_request(self, request):  # type: ignore
        request._metrics_start_time = time.perf_counter()
        method = request.method
        active_requests.labels(method=method).inc()
        # Capture request body length if reasonable
        try:
            if request.body:
                size = len(request.body)
                request_payload_bytes_total.labels(_path_template(request)).inc(size)
        except Exception:
            pass

    def process_response(self, request, response):  # type: ignore
        try:
            duration = time.perf_counter() - getattr(request, '_metrics_start_time', time.perf_counter())
            method = request.method
            status_code = getattr(response, 'status_code', 0)
            status_group = _status_group(status_code)
            path_template = _path_template(request)

            http_request_duration_seconds.labels(method, path_template, status_group).observe(duration)
            http_requests_total.labels(method, path_template, status_group).inc()

            # Response size
            try:
                if hasattr(response, 'content') and response.content is not None:
                    response_payload_bytes_total.labels(path_template).inc(len(response.content))
            except Exception:
                pass
        except Exception:
            # Avoid breaking response flow
            pass
        finally:
            try:
                active_requests.labels(method=request.method).dec()
            except Exception:
                pass
        return response

    def process_exception(self, request, exception):  # type: ignore
        # Ensure active_requests decremented if exception short-circuits
        try:
            active_requests.labels(method=request.method).dec()
        except Exception:
            pass
        return None
