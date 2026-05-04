import os
import time
import httpx
import threading
import json
from dataclasses import dataclass, field
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

LINQ_API_BASE = "https://api.linqapp.com/api/partner/v3"
LINQ_TOKEN = os.getenv("LINQ_API_TOKEN")
LINQ_FROM = os.getenv("LINQ_FROM_NUMBER")
LINQ_TO = os.getenv("LINQ_TO_NUMBER")

NATURAL_DELAY = 1.5


@dataclass
class LoadTestStats:
    delivered: int = 0
    failed: int = 0
    errors: int = 0
    total_sent: int = 0
    total_latency: float = 0.0
    status_codes: dict = field(default_factory=lambda: defaultdict(int))
    lock: threading.Lock = field(default_factory=threading.Lock)

    def record(self, status_code: int, latency: float):
        with self.lock:
            self.total_sent += 1
            self.total_latency += latency
            self.status_codes[status_code] += 1
            if status_code in (200, 201):
                self.delivered += 1
            elif status_code == 0:
                self.errors += 1
            else:
                self.failed += 1

    def avg_latency(self) -> float:
        if self.total_sent == 0:
            return 0.0
        return self.total_latency / self.total_sent

    def print_results(self, duration: float, test_name: str):
        print(f"\n========================================")
        print(f"RESULTS — {test_name}")
        print(f"========================================")
        print(f"  Duration:         {duration:.2f}s")
        print(f"  Total sent:       {self.total_sent}")
        print(f"  Delivered:        {self.delivered}")
        print(f"  Failed:           {self.failed}")
        print(f"  Errors:           {self.errors}")
        if duration > 0:
            print(f"  Throughput:       {self.total_sent / duration:.2f} msg/sec")
        print(f"  Avg latency:      {self.avg_latency() * 1000:.1f}ms")
        if self.total_sent > 0:
            print(f"  Delivery rate:    {self.delivered / self.total_sent * 100:.1f}%")
        print(f"  Status breakdown:")
        for code, count in sorted(self.status_codes.items()):
            label = "OK" if code in (200, 201) else "FAIL" if code else "ERR"
            print(f"    {code} [{label}]: {count} messages")


def send_one(stats: LoadTestStats, body: str, preferred_service: str = None):
    headers = {
        "Authorization": f"Bearer {LINQ_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {
        "from": LINQ_FROM,
        "to": [LINQ_TO],
        "message": {
            "parts": [{"type": "text", "value": body}]
        }
    }

    if preferred_service:
        payload["preferred_service"] = preferred_service

    start = time.time()
    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.post(
                f"{LINQ_API_BASE}/chats",
                headers=headers,
                json=payload
            )
        latency = time.time() - start
        stats.record(response.status_code, latency)

        status = "OK" if response.status_code in (200, 201) else "FAIL"
        print(f"    [{status}] {response.status_code} | {latency*1000:.0f}ms")

    except Exception as e:
        latency = time.time() - start
        stats.record(0, latency)
        print(f"    [ERR] {str(e)[:50]} | {latency*1000:.0f}ms")


def run_sequential(count: int, test_name: str, preferred_service: str = None):
    print(f"\n========================================")
    print(f"TEST: {test_name}")
    print(f"Sending {count} messages with {NATURAL_DELAY}s delay between each")
    print(f"========================================")

    stats = LoadTestStats()
    start = time.time()

    for i in range(count):
        body = f"Load test {test_name} — message {i+1} of {count}"
        print(f"  Sending {i+1}/{count}...")
        send_one(stats, body, preferred_service)
        if i < count - 1:
            time.sleep(NATURAL_DELAY)

    duration = time.time() - start
    stats.print_results(duration, test_name)
    return stats


def run_burst(count: int, test_name: str):
    print(f"\n========================================")
    print(f"TEST: {test_name}")
    print(f"Sending {count} messages as fast as possible")
    print(f"WARNING: This will intentionally stress rate limits")
    print(f"========================================")

    stats = LoadTestStats()
    start = time.time()

    for i in range(count):
        body = f"Burst test — message {i+1} of {count}"
        send_one(stats, body)

    duration = time.time() - start
    stats.print_results(duration, test_name)
    return stats


def run_protocol_comparison(test_name: str):
    print(f"\n========================================")
    print(f"TEST: {test_name}")
    print(f"Comparing latency across protocols")
    print(f"========================================")

    results = {}
    protocols = ["iMessage", "SMS", None]
    labels = ["iMessage (forced)", "SMS (forced)", "Auto (Linq decides)"]

    for protocol, label in zip(protocols, labels):
        print(f"\n  Testing {label}...")
        stats = LoadTestStats()
        body = f"Protocol comparison — {label}"
        send_one(stats, body, protocol)
        results[label] = stats
        time.sleep(NATURAL_DELAY)

    print(f"\n========================================")
    print(f"PROTOCOL COMPARISON RESULTS")
    print(f"========================================")
    for label, stats in results.items():
        status = "OK" if stats.delivered > 0 else "FAIL"
        print(f"  [{status}] {label}: {stats.avg_latency()*1000:.0f}ms avg latency")

    return results


if __name__ == "__main__":
    print("\n========================================")
    print("LINQ API LOAD TEST")
    print(f"From: {LINQ_FROM}")
    print(f"To:   {LINQ_TO}")
    print(f"Natural delay between messages: {NATURAL_DELAY}s")
    print("========================================")

    print("\n\n--- Stage 1: Protocol Comparison ---")
    run_protocol_comparison("Protocol latency comparison")

    print("\n\n--- Stage 2: Sustained Sequential (5 messages) ---")
    run_sequential(
        count=5,
        test_name="Sustained sequential delivery"
    )

    print("\n\n--- Stage 3: Burst Test (characterize rate limits) ---")
    print("Sending 8 messages rapidly to observe rate limit behavior...")
    run_burst(
        count=8,
        test_name="Burst rate limit characterization"
    )

    print("\n\n========================================")
    print("LOAD TEST COMPLETE")
    print("========================================")
    print("Key findings to note:")
    print("  1. Protocol latency differences (iMessage vs SMS vs Auto)")
    print("  2. Sustained delivery rate under natural pacing")
    print("  3. Rate limit behavior under burst conditions")
    print("  4. These findings inform dispatcher design decisions")
