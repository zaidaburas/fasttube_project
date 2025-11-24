import os
import tempfile
import json
from django.http import JsonResponse, FileResponse, HttpResponse, HttpResponseBadRequest
from .utils import get_ydl_options
from yt_dlp import YoutubeDL

COOKIEFILE = os.getenv('COOKIEFILE', None)

def sanitize_info(info):
    # pick useful fields to return
    return {
        'success': True,
        'video_id': info.get('id'),
        'title': info.get('title'),
        'author': info.get('uploader') or info.get('uploader_id'),
        'channel_id': info.get('channel_id'),
        'duration': info.get('duration'),
        'view_count': info.get('view_count'),
        'like_count': info.get('like_count'),
        'is_live': info.get('is_live'),
        'thumbnail': info.get('thumbnail'),
        'description': info.get('description'),
        'upload_date': info.get('upload_date'),
        'formats': info.get('formats', [])
    }

def info_view(request):
    url = request.GET.get('url')
    if not url:
        return HttpResponseBadRequest(json.dumps({'error': 'Missing video URL'}), content_type='application/json')
    ydl_opts = get_ydl_options(skip_download=True, cookiefile=COOKIEFILE)
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            data = sanitize_info(info)
            return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def download_view(request):
    url = request.GET.get('url')
    fmt = request.GET.get('format', 'best')
    if not url:
        return HttpResponseBadRequest(json.dumps({'error': 'Missing video URL'}), content_type='application/json')
    # download to temp file then serve
    tmpdir = tempfile.mkdtemp(prefix='fasttube_')
    outtmpl = os.path.join(tmpdir, '%(title)s.%(ext)s')
    ydl_opts = {
        'outtmpl': outtmpl,
        'format': fmt,
        'quiet': True,
        'no_warnings': True,
    }
    if COOKIEFILE:
        ydl_opts['cookiefile'] = COOKIEFILE
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # find the downloaded filename
            filename = ydl.prepare_filename(info)
            # serve file
            response = FileResponse(open(filename, 'rb'), as_attachment=True, filename=os.path.basename(filename))
            return response
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def audio_view(request):
    url = request.GET.get('url')
    quality = request.GET.get('quality', 'bestaudio')
    if not url:
        return HttpResponseBadRequest(json.dumps({'error': 'Missing video URL'}), content_type='application/json')
    tmpdir = tempfile.mkdtemp(prefix='fasttube_audio_')
    outtmpl = os.path.join(tmpdir, '%(title)s.%(ext)s')
    ydl_opts = {
        'outtmpl': outtmpl,
        'format': quality,
        'quiet': True,
        'no_warnings': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
            'preferredquality': '192',
        }],
    }
    if COOKIEFILE:
        ydl_opts['cookiefile'] = COOKIEFILE
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            # after audio postprocessor, extension may change to m4a
            audio_filename = os.path.splitext(filename)[0] + '.m4a'
            response = FileResponse(open(audio_filename, 'rb'), as_attachment=True, filename=os.path.basename(audio_filename))
            return response
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def search_view(request):
    q = request.GET.get('q')
    limit = int(request.GET.get('limit', '10'))
    if not q:
        return HttpResponseBadRequest(json.dumps({'error': 'Missing query q parameter'}), content_type='application/json')
    query = f"ytsearch{limit}:{q}"
    ydl_opts = get_ydl_options(skip_download=True, cookiefile=COOKIEFILE)
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            entries = info.get('entries', [])
            results = []
            for e in entries[:limit]:
                results.append({
                    'video_id': e.get('id'),
                    'title': e.get('title'),
                    'uploader': e.get('uploader'),
                    'duration': e.get('duration'),
                    'thumbnail': e.get('thumbnail'),
                })
            return JsonResponse({'success': True, 'query': q, 'result_count': len(results), 'videos': results})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
