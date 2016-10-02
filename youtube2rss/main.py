#!/usr/bin/env python3.4
import youtube_dl
import json
import urllib
import os

# keep track of the downloaded videos here
downloaded_videos = []


def get_video_metadata(filename):
    video_info_path = "{filename}.info.json".format(filename=filename)

    with open(video_info_path) as json_data:
        video_info = json.load(json_data)

        metadata = {
            "description": video_info.get("description"),
            "playlist_title": video_info.get("playlist_title"),
            "title": video_info.get("title"),
            "webpage_url": video_info.get("webpage_url"),
            "thumbnail": video_info.get("thumbnail"),
            "uploader_url": video_info.get("uploader_url"),
            "upload_date": video_info.get("upload_date"),
            "id": video_info.get("id"),
            "full_title": video_info.get("full_title"),
            "full_filename": video_info.get("_filename"),
            "filesize": video_info.get("filesize"),
            "url": video_info.get("url"),
        }

        return metadata


# progress looks like this:
#
# {
#   '_total_bytes_str': '391.30MiB',
#   'filename': 'five million-UqADuUBMoZ4.mp4',
#   'status': 'finished',
#   'total_bytes': 410304772
# }
def progress_hook(progress):
    if progress.get('status') == 'finished':
        full_filepath = progress.get('filename')
        filename, file_extension = os.path.splitext(full_filepath)

        video = {
            'metadata': get_video_metadata(filename),
            'full_filenpath': full_filepath,
            'full_filepath_url': urllib.parse.quote_plus(full_filepath),
            '_filename': filename,
            '_file_extension': file_extension,
            'bytes': progress.get('total_bytes'),
        }

        print(video.get("metadata"))
        downloaded_videos.append(video)


# this should be fine as we run the cron job more frequently anyway
within_last_day = youtube_dl.utils.DateRange(start='today-1day', end='today')

options = {
    'daterange': within_last_day,
    'format': '137',                # 137 => video/mp4. Figure out with youtube-dl -F.
    'ignoreerrors': True,           # can happen when format is not available, then just skip.
    'writeinfojson': True,          # write the video description to .info.json.
    'nooverwrites': True,           # prevent overwriting files.
    'progress_hooks': [progress_hook]
}

with youtube_dl.YoutubeDL(options) as ydl:
    ydl.download(['ytuser:caseyneistat'])



