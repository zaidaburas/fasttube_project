# api/views.py (مقتطف)
from django.http import JsonResponse, StreamingHttpResponse
from .scraper import ytdlp_get_info, ytdlp_download_to_temp, playwright_extract_player_response, extract_stream_urls_from_player, stream_via_requests
import os, shutil

def info_view(request):
    url = request.GET.get('url')
    if not url:
        return JsonResponse({'success': False, 'error': 'Missing url param'}, status=400)
    try:
        info = ytdlp_get_info(url)  # try yt-dlp first
        return JsonResponse({'success': True, 'info': info})
    except Exception as e:
        # fallback playwright
        try:
            player = playwright_extract_player_response(url)
            streams = extract_stream_urls_from_player(player)
            return JsonResponse({'success': True, 'info': {'player': player, 'streams': streams}})
        except Exception as e2:
            return JsonResponse({'success': False, 'error': str(e), 'fallback_error': str(e2)}, status=500)

def info_view(request):
    url = request.GET.get('url')
    if not url:
        return JsonResponse({'success': False, 'error': 'Missing url param'}, status=400)
    # try yt-dlp download to temp file
    try:
        filepath = ytdlp_download_to_temp(url, format_selector='best')
        filename = os.path.basename(filepath)
        def file_iterator(path):
            with open(path, 'rb') as f:
                while True:
                    chunk = f.read(1024*64)
                    if not chunk:
                        break
                    yield chunk
            # cleanup after streaming
            try:
                shutil.rmtree(os.path.dirname(path))
            except Exception:
                pass

        resp = StreamingHttpResponse(file_iterator(filepath), content_type='application/octet-stream')
        resp['Content-Disposition'] = f'attachment; filename="{filename}"'
        return resp
    except Exception as e:
        # fallback: try playwright -> direct stream
        try:
            player = playwright_extract_player_response(url)
            streams = extract_stream_urls_from_player(player)
            if not streams:
                raise RuntimeError('No direct streams found in player JSON')
            # pick best video+audio or the first available
            direct = streams[0]['url']
            generator = stream_via_requests(direct)
            resp = StreamingHttpResponse(generator, content_type='video/mp4')
            resp['Content-Disposition'] = 'attachment; filename="video.mp4"'
            return resp
        except Exception as e2:
            return JsonResponse({'success': False, 'error': str(e), 'fallback_error': str(e2)}, status=500)
