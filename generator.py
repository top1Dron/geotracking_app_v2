import argparse
import asyncio
import random
from datetime import datetime, timezone

import httpx


def parse_args() -> argparse.Namespace:
    """Parse command line options for the load generator."""
    parser = argparse.ArgumentParser(description="Generate geotracking location load.")
    parser.add_argument("--url", default="http://localhost:8000/api/v1/locations")
    parser.add_argument("--devices", type=int, default=10_000)
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--ticks", type=int, default=0)
    parser.add_argument(
        "--one-by-one",
        action="store_true",
        help="Send each location as its own HTTP request (ignores --batch-size).",
    )
    return parser.parse_args()


def init_devices(count: int) -> dict[str, tuple[float, float]]:
    """Create initial random positions for the device fleet."""
    devices: dict[str, tuple[float, float]] = {}
    for idx in range(count):
        devices[f"device-{idx:05d}"] = (
            random.uniform(50.2, 50.8),
            random.uniform(30.2, 30.9),
        )
    return devices


def next_point(lat: float, lon: float) -> tuple[float, float]:
    """Apply a small random delta to simulate device drift."""
    return (
        max(-90.0, min(90.0, lat + random.uniform(-0.0008, 0.0008))),
        max(-180.0, min(180.0, lon + random.uniform(-0.0008, 0.0008))),
    )


def build_location(
    device_id: str, lat: float, lon: float, timestamp: str
) -> dict:
    """Build one location payload for the ingest endpoint."""
    return {
        "device_id": device_id,
        "latitude": lat,
        "longitude": lon,
        "timestamp": timestamp,
    }


async def send_payload(
    client: httpx.AsyncClient, url: str, payload: dict | list[dict]
) -> None:
    """Send one location or a batch of locations to the ingest endpoint."""
    response = await client.post(url, json=payload)
    response.raise_for_status()


async def run() -> None:
    """Run the high-load location generation loop."""
    args = parse_args()
    devices = init_devices(args.devices)
    total_ticks = args.ticks if args.ticks > 0 else None

    limits = httpx.Limits(max_connections=500, max_keepalive_connections=200)
    async with httpx.AsyncClient(timeout=30.0, limits=limits) as client:
        tick = 0
        while total_ticks is None or tick < total_ticks:
            now = datetime.now(timezone.utc).isoformat()
            if args.one_by_one:
                for device_id, (lat, lon) in devices.items():
                    new_lat, new_lon = next_point(lat, lon)
                    devices[device_id] = (new_lat, new_lon)
                    await send_payload(
                        client,
                        args.url,
                        build_location(device_id, new_lat, new_lon, now),
                    )
            else:
                batch: list[dict] = []
                for device_id, (lat, lon) in devices.items():
                    new_lat, new_lon = next_point(lat, lon)
                    devices[device_id] = (new_lat, new_lon)
                    batch.append(build_location(device_id, new_lat, new_lon, now))
                    if len(batch) >= args.batch_size:
                        await send_payload(client, args.url, batch)
                        batch.clear()

                if batch:
                    await send_payload(client, args.url, batch)
            tick += 1
            if total_ticks is None or tick < total_ticks:
                await asyncio.sleep(args.interval)


if __name__ == "__main__":
    asyncio.run(run())
