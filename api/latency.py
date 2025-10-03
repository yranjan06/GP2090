from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import numpy as np

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load telemetry data
with open("q-vercel-latency.json", "r") as f:
    telemetry_data = json.load(f)

@app.post("/api/latency")
async def get_latency(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold = body.get("threshold_ms", 99999)

    response = {}

    for region in regions:
        # Filter records by region
        records = [r for r in telemetry_data if r["region"] == region]
        if not records:
            continue

        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime_pct"] for r in records]

        avg_latency = np.mean(latencies)
        p95_latency = np.percentile(latencies, 95)
        avg_uptime = np.mean(uptimes)
        breaches = sum(1 for l in latencies if l > threshold)

        response[region] = {
            "avg_latency": round(float(avg_latency), 2),
            "p95_latency": round(float(p95_latency), 2),
            "avg_uptime": round(float(avg_uptime), 2),
            "breaches": breaches
        }

    return response
