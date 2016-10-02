#!/usr/bin/env python3.4
import youtube_dl
import json
import urllib
import os

# keep track of the downloaded videos here
downloaded_videos = []


# get the meta data we care about
# there is much more (different formats)
# but we do not need it anyways.
def get_metadata(filename):
    with open(filename) as json_data:
        video_info = json.load(json_data)

        metadata = {
            "id": video_info.get("id"),                                # id of the video
            "description": video_info.get("description"),              # video description
            "title": video_info.get("title"),                          # short title of video
            "full_title": video_info.get("full_title"),                # full title of the video
            "thumbnail": video_info.get("thumbnail"),                  # thumbnail of video
            "upload_date": video_info.get("upload_date", '20160101'),  # date in YYYYDDMM
            "playlist_title": video_info.get("playlist_title"),        # name of the play list
            "webpage_url": video_info.get("webpage_url"),              # link to Youtube video
            "uploader_url": video_info.get("uploader_url"),            # link to profile
            "filesize": video_info.get("filesize", 0),                 # file size in bytes
            "_url": video_info.get("url"),                             # points to mp4/video (FIXME)
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
        filename_video = progress.get('filename')
        base_filename = os.path.splitext(filename_video)[0]

        filename_metadata = "{filename}{extension}".format(
            filename=base_filename,
            extension=".info.json")

        video = {
            'filename_video': filename_video,
            'filename_video_url': urllib.parse.quote_plus(filename_video),
            'filename_metadata': filename_metadata,
            'metadata': get_metadata(filename_metadata),
        }

        downloaded_videos.append(video)


def download(username):
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
        ydl.download(['ytuser:{username}'.format(username=username)])


def main():
    download(username="caseyneistat")


main()
