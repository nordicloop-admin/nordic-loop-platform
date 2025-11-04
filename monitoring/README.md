# Monitoring Setup

This folder contains configuration for Prometheus and Grafana.

## Files
- `prometheus/prometheus.yml` - Prometheus scrape config (scrapes Django at /metrics)
- `grafana/datasources/datasource.yml` - Provisioned Prometheus datasource
- `grafana/dashboards/dashboard.yml` - Grafana dashboard provider
- `grafana/dashboards/business-overview.json` - Starter dashboard with business counters

## Usage
Bring up services (assuming existing app + db services):

```
docker compose -f "docker-compose prod.yaml" up -d prometheus grafana
```

Prometheus: http://localhost:9090
Grafana: http://localhost:3000 (anonymous viewer enabled)

## Extend
Add latency, error rate metrics and custom panels as you expand instrumentation.
