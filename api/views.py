import yt_dlp
from django.http import JsonResponse, FileResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import tempfile
import os


# ============================
# 🔥 Bypass Options
# ============================
YDL_BYPASS_OPTS = {
    'geo_bypass': True,
    'nocheckcertificate': True,
    'youtube_include_dash_manifest': False,

    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'android_music', 'tv'],  # Bypass Anti-bot
        }
    },

    'http_headers': {
        'User-Agent': 'com.google.android.youtube/19.09.37 (Linux; U; Android 13)',
        'Accept-Language': 'en-US,en;q=0.9',
    },

    'quiet': True,
}


# ============================
# 📌 API: Get Video Info
# ============================
def get_info(request):
    url = request.GET.get("url")
    if not url:
        return JsonResponse({'success': False, 'error': 'Missing URL'})

    try:
        with yt_dlp.YoutubeDL(YDL_BYPASS_OPTS) as ydl:
            info = ydl.extract_info(url, download=False)

        return JsonResponse({
            'success': True,
            'video_id': info.get('id'),
            'title': info.get('title'),
            'author': info.get('channel'),
            'channel_id': info.get('channel_id'),
            'duration': info.get('duration'),
            'view_count': info.get('view_count'),
            'like_count': info.get('like_count'),
            'thumbnail': info.get('thumbnail'),
            'description': info.get('description'),
            'formats': info.get('formats'),
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ============================
# 📌 API: Download Video
# ============================
@csrf_exempt
def download(request):
    url = request.GET.get("url")
    quality = request.GET.get("quality", "best")

    if not url:
        return JsonResponse({'success': False, 'error': 'Missing URL'})

    # تخزين مؤقت للملف
    temp_dir = tempfile.mkdtemp()
    output_path = os.path.join(temp_dir, "%(title)s.%(ext)s")

    ydl_opts = YDL_BYPASS_OPTS.copy()
    ydl_opts.update({
        'format': f'bestvideo[height<={quality}]+bestaudio/best' if quality != "best" else 'best',
        'outtmpl': output_path,
    })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        final_path = ydl.prepare_filename(info)

        # إعادة الملف للمتصفح
        return FileResponse(open(final_path, 'rb'),
                            as_attachment=True,
                            filename=os.path.basename(final_path))

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

