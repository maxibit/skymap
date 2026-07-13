"""Print-ready star poster renderer used only by the web application."""

from __future__ import annotations

import io
import math
import os
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache" / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / ".cache"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from skyfield.api import Loader, Star, load_constellation_names, wgs84
from skyfield.data import hipparcos, stellarium

CONSTELLATION_URL = "https://gist.githubusercontent.com/gacarrillor/e7fc425b5443617afd294b7ba6169864/raw/constellationship.fab"
PAPER_MM = {"A3": (297.0, 420.0), "A4": (210.0, 297.0)}
THEMES = {
    "midnight": {"background": "#07111f", "map_background": "#0c1c2e", "ink": "#f4efe2", "secondary": "#aebfd0", "grid": "#8295a8", "accent": "#c7a96b"},
    "black": {"background": "#050505", "map_background": "#141414", "ink": "#f5f3ed", "secondary": "#b8b8b8", "grid": "#888888", "accent": "#d6b96d"},
    "ivory": {"background": "#f3eee3", "map_background": "#e8e0d2", "ink": "#17202b", "secondary": "#4c5863", "grid": "#7e888e", "accent": "#9b702e"},
    "emerald": {"background": "#071b18", "map_background": "#0d2b26", "ink": "#f1ebda", "secondary": "#abc4bb", "grid": "#789a90", "accent": "#cfad67"},
}

_lock = threading.Lock()
_loader = Loader(str(ROOT / "data"), verbose=False)
_catalog = None
_outlines = None


@dataclass
class PosterOptions:
    date_time: str
    timezone: str
    latitude: float
    longitude: float
    location: str
    title: str
    subtitle: str
    footer: str
    paper: str = "A3"
    orientation: str = "landscape"
    bleed_mm: float = 3.0
    magnitude: float = 5.5
    theme: str = "midnight"
    constellations: bool = True
    constellation_names: bool = True
    coordinate_grid: bool = True
    milky_way: bool = False
    ecliptic: bool = False
    sun: bool = True
    moon: bool = True
    cardinal_points: bool = True


def _assets():
    global _catalog, _outlines
    if _catalog is None:
        with _loader.open(hipparcos.URL) as f:
            frame = hipparcos.load_dataframe(f)
        needed = ["magnitude", "ra_degrees", "dec_degrees", "ra_mas_per_year", "dec_mas_per_year", "parallax_mas"]
        _catalog = frame.dropna(subset=needed)
    if _outlines is None:
        with _loader.open(CONSTELLATION_URL) as f:
            _outlines = stellarium.parse_constellations(f)
    return _catalog, _outlines


def _project(alt, az):
    alt, az = np.asarray(alt), np.asarray(az)
    visible = alt >= 0
    radius = np.tan(np.radians(90 - alt[visible]) / 2)
    angle = np.radians(az[visible])
    return radius * np.sin(angle), radius * np.cos(angle), visible


def _split_visible(alt, az):
    x, y, visible = _project(alt, az)
    points = np.full((len(np.atleast_1d(alt)), 2), np.nan)
    points[visible] = np.column_stack((x, y))
    return [points[i:i + 2] for i in range(len(points) - 1) if np.isfinite(points[i:i + 2]).all()]


def _milky_way(observer_at):
    transform = np.array([[-.05487556, .49410943, -.86766615], [-.87343709, -.44482963, -.19807637], [-.48383502, .74698224, .45598378]])
    result = []
    for latitude in (-10, 0, 10):
        longitude = np.linspace(0, 360, 721)
        lon, lat = np.radians(longitude), math.radians(latitude)
        galactic = np.vstack((np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.full(lon.shape, np.sin(lat))))
        icrs = transform @ galactic
        apparent = observer_at.observe(Star(ra_hours=(np.degrees(np.arctan2(icrs[1], icrs[0])) % 360) / 15, dec_degrees=np.degrees(np.arcsin(icrs[2])))).apparent()
        alt, az, _ = apparent.altaz()
        result.extend(_split_visible(alt.degrees, az.degrees))
    return result


def _constellations(catalog, outlines, observer_at):
    official = dict(load_constellation_names())
    segments, labels = [], {}
    for abbreviation, edges in outlines:
        points = []
        for first, second in edges:
            if first not in catalog.index or second not in catalog.index:
                continue
            apparent = observer_at.observe(Star.from_dataframe(catalog.loc[[first, second]])).apparent()
            alt, az, _ = apparent.altaz()
            x, y, visible = _project(alt.degrees, az.degrees)
            if visible.all():
                segment = [(x[0], y[0]), (x[1], y[1])]
                segments.append(segment); points.extend(segment)
        if points:
            labels[official.get(abbreviation, abbreviation)] = np.mean(points, axis=0)
    return segments, labels


def _paper(options):
    short, long = PAPER_MM[options.paper]
    trim = (long, short) if options.orientation == "landscape" else (short, long)
    page = (trim[0] + 2 * options.bleed_mm, trim[1] + 2 * options.bleed_mm)
    return trim, page


def render(options: PosterOptions, output_format: str, preview: bool = False) -> bytes:
    with _lock:
        catalog, outlines = _assets()
        local = datetime.strptime(options.date_time, "%Y-%m-%dT%H:%M").replace(tzinfo=ZoneInfo(options.timezone))
        ts = _loader.timescale(); t = ts.from_datetime(local); ephemeris = _loader("de421.bsp")
        observer = ephemeris["earth"] + wgs84.latlon(options.latitude, options.longitude)
        observer_at = observer.at(t)
        stars = catalog[catalog.magnitude <= options.magnitude]
        apparent = observer_at.observe(Star.from_dataframe(stars)).apparent()
        alt, az, _ = apparent.altaz(); x, y, visible = _project(alt.degrees, az.degrees)
        magnitudes = stars.magnitude.to_numpy()[visible]

        trim, page = _paper(options); colors = THEMES[options.theme]
        fig = plt.figure(figsize=(page[0] / 25.4, page[1] / 25.4), facecolor=colors["background"])
        # Layout is relative to the trim page; bleed remains a full-color perimeter.
        landscape = options.orientation == "landscape"
        # Give the sky disc a stronger presence on the page while preserving the
        # title and footer clear zones.
        ax_rect = (.19, .095, .62, .79) if landscape else (.08, .18, .84, .62)
        ax = fig.add_axes(ax_rect, facecolor=colors["background"]); ax.set_aspect("equal")
        ax.set(xlim=(-1.06, 1.06), ylim=(-1.06, 1.06)); ax.axis("off")

        # A subtly different disc tone survives print better than relying on a
        # hairline outline alone to separate the map from the poster background.
        ax.add_patch(plt.Circle((0, 0), 1, facecolor=colors["map_background"], edgecolor="none", zorder=-10))

        if options.milky_way:
            ax.add_collection(LineCollection(_milky_way(observer_at), colors=colors["secondary"], linewidths=8, alpha=.055, zorder=0))
        if options.coordinate_grid:
            for altitude in (30, 60):
                radius = math.tan(math.radians(90 - altitude) / 2)
                ax.add_patch(plt.Circle((0, 0), radius, fill=False, color=colors["grid"], lw=.42, alpha=.48))
                ax.text(.012, radius - .012, f"{altitude}°", color=colors["secondary"], fontsize=4.3, alpha=.65)
            spokes = [[(0, 0), (math.sin(math.radians(a)), math.cos(math.radians(a)))] for a in range(0, 360, 30)]
            ax.add_collection(LineCollection(spokes, colors=colors["grid"], linewidths=.32, alpha=.32))

        labels = {}
        if options.constellations:
            segments, labels = _constellations(catalog, outlines, observer_at)
            ax.add_collection(LineCollection(segments, colors=colors["secondary"], linewidths=.70, alpha=.65, zorder=1))
        if options.constellation_names:
            for name, point in labels.items():
                if np.hypot(*point) < .94:
                    ax.text(*point, name.upper(), color=colors["secondary"], fontsize=3.8, alpha=.72, ha="center", va="center")
        if options.ecliptic:
            samples = [local + timedelta(days=i) for i in range(-183, 184)]
            path = observer.at(ts.from_datetimes(samples)).observe(ephemeris["sun"]).apparent()
            pa, pz, _ = path.altaz()
            ax.add_collection(LineCollection(_split_visible(pa.degrees, pz.degrees), colors=colors["accent"], linewidths=.65, alpha=.72, linestyles="dashed"))

        order = np.argsort(magnitudes)[::-1]
        sizes = np.clip(3.2 * np.power(2.512, 2.2 - magnitudes[order]), .28, 42)
        ax.scatter(x[order], y[order], s=sizes, c=colors["ink"], linewidths=0, alpha=.94, zorder=2)

        for enabled, body, glyph, color in ((options.sun, "sun", "☉", colors["accent"]), (options.moon, "moon", "●", colors["ink"])):
            if enabled:
                body_app = observer_at.observe(ephemeris[body]).apparent(); ba, bz, _ = body_app.altaz()
                bx, by, bv = _project(np.atleast_1d(ba.degrees), np.atleast_1d(bz.degrees))
                if bv[0]:
                    ax.scatter(bx, by, s=42 if body == "sun" else 28, facecolors=color, edgecolors=colors["map_background"], linewidths=.7, zorder=5)
                    ax.text(bx[0], by[0] - .035, body.upper(), color=colors["secondary"], fontsize=4.5, ha="center", va="top")

        ax.add_patch(plt.Circle((0, 0), 1, fill=False, color=colors["ink"], lw=1.1, alpha=.92, zorder=4))
        if options.cardinal_points:
            for label, px, py, ha, va in (("N", 0, 1.025, "center", "bottom"), ("E", 1.025, 0, "left", "center"), ("S", 0, -1.025, "center", "top"), ("W", -1.025, 0, "right", "center")):
                ax.text(px, py, label, color=colors["ink"], fontsize=9, ha=ha, va=va)
        ax.text(0, .018, "Z E N I T H", color=colors["secondary"], fontsize=5.5, ha="center")

        auto_subtitle = f"{options.location}  ·  {local.strftime('%d %B %Y  ·  %H:%M %Z')}".upper()
        fig.text(.5, .932 if landscape else .90, options.title, color=colors["ink"], fontsize=21 if options.paper == "A3" else 16, ha="center")
        fig.text(.5, .895 if landscape else .865, options.subtitle or auto_subtitle, color=colors["secondary"], fontsize=8.5, ha="center")
        footer = options.footer or f"{abs(options.latitude):.4f}° {'N' if options.latitude >= 0 else 'S'}  ·  {abs(options.longitude):.4f}° {'E' if options.longitude >= 0 else 'W'}"
        fig.text(.5, .052, footer, color=colors["secondary"], fontsize=6.5, ha="center")

        stream = io.BytesIO()
        if output_format == "png":
            fig.savefig(stream, format="png", dpi=110 if preview else 300, facecolor=fig.get_facecolor())
        else:
            fig.savefig(stream, format=output_format, dpi=300, facecolor=fig.get_facecolor())
        plt.close(fig)
        return stream.getvalue()
