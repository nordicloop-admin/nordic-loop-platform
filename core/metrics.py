"""Prometheus metrics definitions for simple business counters.

This keeps implementation minimal: just define counters and expose a /metrics endpoint.
Increment counters in signals or service functions when entities are created.
"""
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
from django.http import HttpResponse

# Business event counters
ads_created_total = Counter(
    'ads_created_total',
    'Total number of ads (material listings) created'
)

auctions_activated_total = Counter(
    'auctions_activated_total',
    'Total number of auctions activated (ads moved to active status)'
)

bids_created_total = Counter(
    'bids_created_total',
    'Total number of bids placed on ads'
)

companies_registered_total = Counter(
    'companies_registered_total',
    'Total number of companies registered (since instrumentation start)'
)

# Snapshot gauge of current total companies in DB (updated on each /metrics scrape)
companies_existing_total = Gauge(
    'companies_existing_total',
    'Current total number of companies in database'
)


def metrics_view(_request):
    """Return latest Prometheus metrics.

    Before exporting, update gauges that reflect current state.
    """
    try:
        from company.models import Company
        companies_existing_total.set(Company.objects.count())
    except Exception:
        # Fail silently to avoid breaking metrics endpoint
        pass
    return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)
