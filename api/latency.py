import json
import numpy as np
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI()

# Remove any existing CORS middleware and add this fresh configuration
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Load telemetry data
DATA_PATH = Path(__file__).parent.parent / "q-vercel-latency.json"
with open(DATA_PATH, "r") as f:
    telemetry = json.load(f)


@app.post("/api/latency")
async def get_latency_metrics(request: Request):
    try:
        body = await request.json()
        regions = body.get("regions")

        if not regions or not isinstance(regions, (list, dict)):
            raise HTTPException(
                status_code=400,
                detail="Request must include a 'regions' array or object"
            )

        threshold_ms = body.get("threshold_ms", 180)

        region_data = {}

        for region in regions:
            region_entries = [r for r in telemetry if r["region"] == region]

            if not region_entries:
                continue

            latencies = [r["latency_ms"] for r in region_entries]
            uptimes = [r["uptime_pct"] for r in region_entries]

            avg_latency = float(np.mean(latencies))
            p95_latency = float(np.percentile(latencies, 95))
            avg_uptime = float(np.mean(uptimes))
            breaches = int(sum(l > threshold_ms for l in latencies))

            region_data[region] = {
                "avg_latency": round(avg_latency, 2),
                "p95_latency": round(p95_latency, 2),
                "avg_uptime": round(avg_uptime, 2),
                "breaches": breaches,
            }

        # Wrap the response in a "regions" property
        response = {"regions": region_data}
        return JSONResponse(content=response)

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON in request body"
        )
