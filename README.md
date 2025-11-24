# FastTube Django (yt-dlp) - API Only

This project provides a simple Django REST-like API using `yt-dlp` to fetch YouTube info and download media.
Endpoints:
- GET /api/info?url=VIDEO_URL
- GET /api/download?url=VIDEO_URL[&format=mp4|webm|best]
- GET /api/audio?url=VIDEO_URL[&format=m4a|mp3|best]
- GET /api/search?q=QUERY[&limit=10]
- GET /health

Features:
- Uses `yt-dlp` which supports cookies and geo-bypass.
- Optional COOKIEFILE environment variable path to a cookies.txt (Netscape format) for age-restricted or region-restricted videos.
- Streaming download implemented by downloading to a temporary file then serving as attachment.

Quick start (local):
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export COOKIEFILE=/path/to/cookies.txt    # optional
python manage.py runserver 0.0.0.0:8000
```

Notes for deployment:
- Ensure `yt-dlp` binary dependencies are available on the host.
- For large-scale use, consider streaming or handing off downloads rather than serving files through Django process.
