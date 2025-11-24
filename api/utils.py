import os
from yt_dlp import YoutubeDL

def get_ydl_options(skip_download=True, cookiefile=None, extra_opts=None):
    opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': skip_download,
        'format': 'bestvideo+bestaudio/best' if skip_download else 'best',
        'writesubtitles': False,
        'cachedir': False,
    }
    if cookiefile:
        opts['cookiefile'] = cookiefile
    if extra_opts:
        opts.update(extra_opts)
    return opts
