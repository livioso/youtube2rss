#!/usr/bin/env python3
import requests
import fire
import os

from requests.exceptions import RequestException
from youtube_dl.utils import UnavailableVideoError, MaxDownloadsReached
from youtube_dl import YoutubeDL


class Youtube2Rss(object):

    def build_feed(self, channel_id):
        options = {}

        with YoutubeDL(options) as ydl:

            videos = self.fetch_playlist_videos(channel_id)

            for _, (video, snippet) in enumerate(videos.items()):

                try:
                    video_info = ydl.extract_info(video, download=False)

                except UnavailableVideoError:
                    raise

                except MaxDownloadsReached:
                    raise

    def fetch_playlist_videos(self, playlist_id):

        def snippet(item):
            return item.get('snippet', {})

        def video_id(item):
            return (snippet(item).get('resourceId', {})
                                 .get('videoId'))

        videos = {}

        try:
            response = requests.get(
                url="https://www.googleapis.com/youtube/v3/playlistItems",
                params={
                    "key": os.environ.get('YOUTUBE_API_KEY', ''),
                    "playlistId": playlist_id,
                    "maxResults": "50",
                    "part": "snippet"
                }
            )

            data = response.json()

            import ipdb
            ipdb.set_trace()

            # build <key, value> dict where key = video_id and value = snippet
            videos = {video_id(item): snippet(item) for item in data.get('items', [])}

        except RequestException:
            print('HTTP Request failed')

        return videos


if __name__ == '__main__':
    fire.Fire(Youtube2Rss)
