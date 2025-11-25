# api/scraper.py
import os
import tempfile
import subprocess
import json
import shutil
import requests
from yt_dlp import YoutubeDL

COOKIEFILE = os.getenv('COOKIEFILE')  # optional path to cookies.txt
PROXY = os.getenv('HTTP_PROXY') or os.getenv('HTTPS_PROXY')  # optional

def ytdlp_get_info(url, extra_opts=None):
    """Try to get metadata + formats using yt-dlp (recommended)."""
    opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'format': 'best',
        'cachedir': False,
        'noplaylist': True,
        'ignoreerrors': False,
        'nocheckcertificate': True,
        'outtmpl': '%(id)s.%(ext)s',
    }
    if COOKIEFILE:
        opts['cookiefile'] = COOKIEFILE
    if PROXY:
        opts['proxy'] = PROXY
    if extra_opts:
        opts.update(extra_opts)

    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return info

def ytdlp_download_to_temp(url, format_selector='best'):
    """Download video/audio to a temporary file using yt-dlp and return local path."""
    tmpdir = tempfile.mkdtemp(prefix='fasttube_')
    outtmpl = os.path.join(tmpdir, '%(title)s.%(ext)s')
    opts = {
        'outtmpl': outtmpl,
        'format': format_selector,
        'quiet': True,
        'no_warnings': True,
    }
    if COOKIEFILE:
        opts['cookiefile'] = COOKIEFILE
    if PROXY:
        opts['proxy'] = PROXY

    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
    return filename  # caller should serve file and remove tmpdir afterwards

# -------- Playwright fallback to extract player JSON -----------
def playwright_extract_player_response(url, browser_type='chromium', headless=True):
    """Use Playwright to fetch page and extract ytInitialPlayerResponse JSON."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = getattr(p, browser_type).launch(headless=headless, args=['--no-sandbox'])
        page = browser.new_page()
        page.goto(url, wait_until='networkidle')
        # get page content
        content = page.content()
        browser.close()

    # find ytInitialPlayerResponse in HTML (common pattern)
    import re
    m = re.search(r'ytInitialPlayerResponse\s*=\s*({.*?});', content, re.S)
    if not m:
        # sometimes YouTube has a JSON inside "ytplayer.config = {...}" or other keys
        m2 = re.search(r'ytplayer\.config\s*=\s*({.*?});', content, re.S)
        if m2:
            return json.loads(m2.group(1))
        raise RuntimeError('ytInitialPlayerResponse not found in page')

    return json.loads(m.group(1))

def extract_stream_urls_from_player(player_json):
    """Find streamingData / adaptiveFormats and return list of direct URLs (if present)."""
    sd = player_json.get('streamingData') or {}
    out = []
    for arr_key in ('formats', 'adaptiveFormats'):
        for f in sd.get(arr_key, []) or []:
            url = f.get('url') or f.get('signatureCipher') or f.get('cipher')
            if url:
                # signatureCipher needs parsing: 's=...&url=...&sp=...'
                if isinstance(url, dict):
                    direct = url.get('url')
                else:
                    # parse query string
                    from urllib.parse import parse_qs
                    if isinstance(url, str) and 'url=' in url:
                        q = parse_qs(url)
                        direct = q.get('url', [None])[0]
                    else:
                        direct = url
                if direct:
                    out.append({
                        'itag': f.get('itag'),
                        'mimeType': f.get('mimeType'),
                        'qualityLabel': f.get('qualityLabel'),
                        'url': direct,
                        'content_length': f.get('contentLength') or f.get('content_length')
                    })
    return out

def stream_via_requests(direct_url, chunk_size=1024*32, headers=None):
    """Stream a direct URL using requests (generator yielding bytes)."""
    headers = headers or {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    with requests.get(direct_url, stream=True, headers=headers, timeout=30, proxies={'http': PROXY, 'https': PROXY} if PROXY else None) as r:
        r.raise_for_status()
        for chunk in r.iter_content(chunk_size=chunk_size):
            if chunk:
                yield chunk
