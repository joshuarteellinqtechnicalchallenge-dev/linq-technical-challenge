# Linq Technical Challenge — Joshua Teel

## What I Built

A messaging reliability and observability platform built on the Linq Partner API V3,
demonstrating end-to-end message dispatch, protocol characterization, load testing,
and production-grade monitoring.

## Why I Built It This Way

The job description asks for someone who thinks about reliability at scale — not just
making things work once, but understanding rate limits, failure modes, and building
systems that degrade gracefully. Rather than building a simple demo app, I built the
kind of tooling an infrastructure engineer would actually use to understand and operate
a messaging pipeline.

## What's In This Repo

- `dispatcher/` — Message dispatch client with error handling and protocol selection
- `load_test/` — Load testing suite that characterizes real API behavior under volume
- `monitoring/` — Prometheus metrics exporter and Grafana dashboard for live observability
- `docs/` — Findings and production recommendations

## Key Findings From Real API Testing

### Protocol Latency
| Protocol | Avg Latency | Notes |
|---|---|---|
| iMessage (forced) | 1,106ms | APNs handshake overhead on new conversations |
| SMS (forced) | 195ms | Direct carrier gateway, no handshake |
| Auto (Linq decides) | 191ms | Linq routes optimally by default |

**Key insight:** iMessage initiation is 5-6x slower than SMS due to APNs handshake
overhead. In a high-volume system you'd want to pre-warm iMessage connections rather
than initiating them on demand. Once a conversation is established, subsequent messages
drop to ~200ms regardless of protocol.

### Sustained Delivery
- 100% delivery rate at natural 1.5s pacing
- Latency stabilizes at ~200ms after first message in a conversation
- First message overhead is connection establishment, not protocol latency

### Burst Behavior
- 8 messages delivered at 4.77 msg/sec with zero failures
- Rate limiting operates at daily volume level (5,000-7,000/day) not burst level
- API tolerates short bursts gracefully

## How To Run It

### Prerequisites
```bash
pip3 install httpx python-dotenv --break-system-packages
```

### Setup
Create a `.env` file:

LINQ_API_TOKEN=your_token_here
LINQ_FROM_NUMBER=your_linq_number
LINQ_TO_NUMBER=recipient_number

### Run the dispatcher
```bash
python3 dispatcher/sender.py
```

### Run the load test
```bash
python3 load_test/load_test.py
```

## What I'd Do Next In Production

- **Connection pre-warming** — maintain persistent iMessage sessions to eliminate
  the 1,100ms APNs handshake on first contact
- **Retry queue with exponential backoff** — dead letter queue with webhook callbacks
  to the sending application on final failure
- **Token registry with Redis caching** — avoid database hits on every dispatch
- **PagerDuty integration** — alert on delivery rate threshold breaches and cert expiry
- **Horizontal queue workers** — Docker containers on AWS scaling with message volume
- **Capacity planning** — at current growth projections, model when daily volume limits
  will require additional Linq lines

## Stack

- Python 3.12
- httpx for async HTTP
- Docker + Docker Compose
- Prometheus + Grafana for observability
- Linq Partner API V3
