# Linq Technical Challenge — Joshua Teel

## What I Built

A messaging reliability and observability platform that demonstrates end-to-end message dispatch across Linq's SMS API, 
with real-time delivery metrics, load testing, and fallback handling.

## Why I Built It This Way

The job description asks for someone who thinks about reliability at scale — not just making things work once, 
but understanding rate limits, failure modes, and building systems that degrade gracefully. 
Rather than building a simple demo app, I built the kind of tooling an infrastructure engineer would actually use to 
understand and operate a messaging pipeline.

## What's In This Repo

- `dispatcher/` — Message dispatch client with error handling, retry logic, and exponential backoff
- `load_test/` — Load testing suite that characterizes rate limit behavior and delivery degradation under volume
- `monitoring/` — Prometheus metrics exporter and Grafana dashboard config for live observability
- `docs/` — Findings, analysis, and what I'd do next in production

## Key Findings

*(To be filled in after sandbox testing)*

## How To Run It

*(To be filled in after sandbox testing)*

## What I'd Do Next In Production

- Replace mock endpoints with connection pooling across multiple Linq sandbox numbers
- Add a dead letter queue with webhook callbacks to the sending application
- Set up PagerDuty integration on delivery rate threshold breaches
- Implement token registry with Redis caching for high-volume dispatch
- Run capacity planning projections based on load test data

## Stack

- Python 3.12
- Docker + Docker Compose
- Prometheus + Grafana
- httpx for HTTP client# linq-technical-challenge
Linq Technical Challenge
