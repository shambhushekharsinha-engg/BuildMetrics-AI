# 📊 BuildMetrics AI — Observability & Monitoring Stack

This directory contains configuration files for the production observability stack, consisting of **Prometheus** (metrics collection & time-series database) and **Grafana** (real-time dashboards & alerting).

---

## 🏗️ Architecture

```
                 Scrape every 10s
┌──────────────┐ ───────────────> ┌────────────────┐ ───────────────> ┌─────────────┐
│ FastAPI :8000│                  │Prometheus :9090│                  │Grafana :3000│
│   /metrics   │                  │  TSDB Storage  │                  │ Dashboards  │
└──────────────┘                  └────────────────┘                  └─────────────┘
```

The FastAPI application uses `prometheus_fastapi_instrumentator` to automatically track HTTP request counts, response latency histograms, error rates, and endpoint saturation.

---

## ⚙️ Configuration Files

- [`prometheus.yml`](prometheus.yml): Prometheus scrape job definition targeting the `api:8000` service on `/metrics` with 10s intervals.

---

## 📈 Key Metrics Exposed

| Metric Name | Type | Description |
| :--- | :---: | :--- |
| `http_requests_total` | Counter | Total HTTP requests categorized by `method`, `handler`, and `status`. |
| `http_request_duration_seconds` | Histogram | Request latency distribution across all API endpoints. |
| `http_requests_in_progress` | Gauge | Active requests currently being processed. |

---

## 🚀 Running the Monitoring Services

The monitoring stack is fully orchestrated via `docker-compose.yml`:

```bash
# Start API, Redis, Postgres, Prometheus, and Grafana
docker compose up -d

# Check Prometheus target status
curl http://localhost:9090/api/v1/targets

# Open Grafana Web UI
# URL: http://localhost:3000
# User: admin | Password: buildmetrics
```

---

## 🔍 Useful Prometheus Queries (PromQL)

```promql
# 1. Total Requests per minute by status code
sum(rate(http_requests_total[1m])) by (status)

# 2. 95th Percentile API Latency (p95)
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))

# 3. 5xx Server Error Rate
sum(rate(http_requests_total{status=~"5.."}[1m])) / sum(rate(http_requests_total[1m])) * 100
```
