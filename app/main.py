"""FastAPI entry point for Sky Poster Studio."""

from __future__ import annotations

import json
import re
import threading
import time
from collections import defaultdict, deque
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from timezonefinder import TimezoneFinder

from .generator import PAPER_MM, THEMES, PosterOptions, render

BASE = Path(__file__).resolve().parents[1]
CACHE_FILE = BASE / "data" / "geocoding.json"
CACHE_FILE.parent.mkdir(exist_ok=True)
app = FastAPI(title="Sky Poster Studio", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
timezone_finder = TimezoneFinder(in_memory=True)
rate_lock = threading.Lock(); requests_by_ip = defaultdict(deque)
geocode_cache = json.loads(CACHE_FILE.read_text()) if CACHE_FILE.exists() else {}


class PosterRequest(BaseModel):
    date_time: str
    timezone: str = Field(max_length=64)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    location: str = Field(min_length=1, max_length=100)
    title: str = Field(default="THE SKY ABOVE", max_length=100)
    subtitle: str = Field(default="", max_length=160)
    footer: str = Field(default="", max_length=160)
    paper: str = "A3"
    orientation: str = "landscape"
    bleed_mm: float = Field(default=3, ge=0, le=10)
    magnitude: float = Field(default=5.5, ge=3, le=7)
    theme: str = "midnight"
    constellations: bool = True
    constellation_names: bool = True
    coordinate_grid: bool = True
    milky_way: bool = False
    ecliptic: bool = False
    sun: bool = True
    moon: bool = True
    cardinal_points: bool = True

    @field_validator("date_time")
    @classmethod
    def valid_datetime(cls, value):
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", value):
            raise ValueError("Use YYYY-MM-DDTHH:MM")
        return value

    @field_validator("paper")
    @classmethod
    def valid_paper(cls, value):
        if value not in PAPER_MM: raise ValueError("Unsupported paper size")
        return value

    @field_validator("orientation")
    @classmethod
    def valid_orientation(cls, value):
        if value not in {"portrait", "landscape"}: raise ValueError("Unsupported orientation")
        return value

    @field_validator("theme")
    @classmethod
    def valid_theme(cls, value):
        if value not in THEMES: raise ValueError("Unsupported theme")
        return value


def limited(request: Request, limit=40, window=60):
    ip = request.client.host if request.client else "unknown"; now = time.monotonic()
    with rate_lock:
        bucket = requests_by_ip[ip]
        while bucket and bucket[0] < now - window: bucket.popleft()
        if len(bucket) >= limit: raise HTTPException(429, "Too many requests. Please wait a minute.")
        bucket.append(now)


@app.get("/")
def index(): return FileResponse(BASE / "static" / "index.html")


@app.get("/health", include_in_schema=False)
def health(): return {"status": "ok"}


@app.get("/api/geocode")
async def geocode(q: str, request: Request):
    limited(request, 20); query = q.strip()
    if len(query) < 2 or len(query) > 100: raise HTTPException(400, "Enter at least two characters.")
    key = query.casefold()
    if key in geocode_cache: return geocode_cache[key]
    async with httpx.AsyncClient(timeout=8, headers={"User-Agent": "SkyPosterStudio/1.0 (private poster generator)"}) as client:
        response = await client.get("https://nominatim.openstreetmap.org/search", params={"q": query, "format": "jsonv2", "limit": 6, "featuretype": "city", "addressdetails": 1})
        response.raise_for_status()
    results = []
    for item in response.json():
        lat, lon = float(item["lat"]), float(item["lon"])
        results.append({"name": item["display_name"], "latitude": lat, "longitude": lon, "timezone": timezone_finder.timezone_at(lat=lat, lng=lon) or "UTC"})
    geocode_cache[key] = results; CACHE_FILE.write_text(json.dumps(geocode_cache, ensure_ascii=False, indent=2))
    return results


def create(payload: PosterRequest, output_format: str, preview=False):
    try: content = render(PosterOptions(**payload.model_dump()), output_format, preview)
    except Exception as exc: raise HTTPException(400, f"Could not generate poster: {exc}") from exc
    media = {"pdf": "application/pdf", "svg": "image/svg+xml", "png": "image/png"}[output_format]
    headers = {} if preview else {"Content-Disposition": f'attachment; filename="sky-poster-{payload.date_time[:10]}.{output_format}"'}
    return Response(content, media_type=media, headers=headers)


@app.post("/api/preview")
def preview(payload: PosterRequest, request: Request): limited(request); return create(payload, "png", True)


@app.post("/api/export/{output_format}")
def export(output_format: str, payload: PosterRequest, request: Request):
    limited(request)
    if output_format not in {"pdf", "svg", "png"}: raise HTTPException(404, "Unsupported format.")
    return create(payload, output_format)
