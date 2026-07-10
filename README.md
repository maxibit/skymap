# Sky Poster Studio

A local, English-language web application for designing astronomically accurate A3/A4 star posters and exporting PDF, SVG, or 300 DPI PNG files. The original command-line project in the parent directory is not modified or imported.

## Run with Docker Compose

Copy this project to `/docker/skymap`, then run:

```bash
cp .env.example .env
docker compose up --build -d
```

Open `http://127.0.0.1:8088`. The first poster request downloads the Hipparcos catalog, constellation data, and JPL ephemeris into the persistent `sky_data` volume.

To run the optional Cloudflare Tunnel container, place your token in `.env` and use:

```bash
docker compose --profile tunnel up --build -d
```

For a public deployment, keep Cloudflare access controls, WAF, and rate-limit rules enabled.

## Print bleed

The selected bleed is added outside the final A3/A4 trim dimensions. For example, A3 landscape with 3 mm bleed produces a 426 × 303 mm PDF page. The background extends across the full bleed area. Ask the printer to trim 3 mm from each edge.

## City search

City results come from OpenStreetMap Nominatim through the server, never directly from the browser. Results and calculated IANA timezones are stored in the persistent application-data volume.
