import os
import time
import httpx
import json
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

LINQ_API_BASE = "https://api.linqapp.com/api/partner/v3"
LINQ_TOKEN = os.getenv("LINQ_API_TOKEN")
LINQ_FROM = os.getenv("LINQ_FROM_NUMBER")
LINQ_TO = os.getenv("LINQ_TO_NUMBER")


@dataclass
class Message:
    to: str
    body: str
    preferred_service: Optional[str] = None
    message_id: str = field(
        default_factory=lambda: f"msg-{int(time.time())}"
    )


@dataclass
class DeliveryResult:
    message_id: str
    success: bool
    status_code: int
    response_body: dict
    latency_ms: float
    protocol_requested: Optional[str]


def send_message(message: Message) -> DeliveryResult:
    headers = {
        "Authorization": f"Bearer {LINQ_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {
        "from": LINQ_FROM,
        "to": [message.to],
        "message": {
            "parts": [
                {
                    "type": "text",
                    "value": message.body,
                }
            ]
        }
    }

    if message.preferred_service:
        payload["preferred_service"] = message.preferred_service

    start = time.time()

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"{LINQ_API_BASE}/chats",
                headers=headers,
                json=payload
            )

        latency = (time.time() - start) * 1000

        try:
            body = response.json()
        except Exception:
            body = {"raw": response.text}

        success = response.status_code in (200, 201)

        return DeliveryResult(
            message_id=message.message_id,
            success=success,
            status_code=response.status_code,
            response_body=body,
            latency_ms=round(latency, 2),
            protocol_requested=message.preferred_service or "auto"
        )

    except Exception as e:
        latency = (time.time() - start) * 1000
        return DeliveryResult(
            message_id=message.message_id,
            success=False,
            status_code=0,
            response_body={"error": str(e)},
            latency_ms=round(latency, 2),
            protocol_requested=message.preferred_service or "auto"
        )


def print_result(result: DeliveryResult):
    status = "OK" if result.success else "FAIL"
    print(f"\n  [{status}] {result.message_id}")
    print(f"    Status code:  {result.status_code}")
    print(f"    Latency:      {result.latency_ms}ms")
    print(f"    Protocol:     {result.protocol_requested}")
    print(f"    Response:     {json.dumps(result.response_body, indent=2)}")


if __name__ == "__main__":
    print("\n========================================")
    print("LINQ API — LIVE SEND TEST")
    print(f"From: {LINQ_FROM}")
    print(f"To:   {LINQ_TO}")
    print("========================================")

    print("\n--- Test 1: Auto protocol (let Linq decide) ---")
    result = send_message(Message(
        to=LINQ_TO,
        body="Linq technical challenge — dispatcher test 1. Auto protocol."
    ))
    print_result(result)
    time.sleep(2)

    print("\n--- Test 2: Force iMessage ---")
    result = send_message(Message(
        to=LINQ_TO,
        body="Linq technical challenge — dispatcher test 2. Forced iMessage.",
        preferred_service="iMessage"
    ))
    print_result(result)
    time.sleep(2)

    print("\n--- Test 3: Force SMS ---")
    result = send_message(Message(
        to=LINQ_TO,
        body="Linq technical challenge — dispatcher test 3. Forced SMS.",
        preferred_service="SMS"
    ))
    print_result(result)
    time.sleep(2)

    print("\n--- Test 4: Malformed recipient ---")
    result = send_message(Message(
        to="not-a-phone-number",
        body="This should fail with a validation error."
    ))
    print_result(result)
