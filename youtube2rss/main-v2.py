#!/usr/bin/env python3
import requests
import fire
import os

from requests.exceptions import RequestException
from youtube_dl.utils import UnavailableVideoError, MaxDownloadsReached
from youtube_dl import YoutubeDL

class RSSFeedBuilder(object)

    def __init__(self, videos):
        self.videos = videos

    def build_rss_feed(channel_info, channel_downloads):
        root = build_rss_root(channel_info)
        channel = root.find('channel')

        # append episodes aka 'items'
        for video in channel_downloads:
            item = build_rss_episode_item(video, channel_info)
            channel.append(item)

        write_rss_feed(channel_info, root)

class Youtube2Rss(object):

    def build_feed(self, channel_id):
        videos = Youtube2Rss.build_videos_dict(channel_id)

    @staticmethod
    def build_rss_feed(channel_info, channel_downloads):
        root = build_rss_root(channel_info)
        channel = root.find('channel')

        # append episodes aka 'items'
        for video in channel_downloads:
            item = build_rss_episode_item(video, channel_info)
            channel.append(item)

    @staticmethod
    def build_videos_dict(channel_id):
        videos = {}

        for snippet in Youtube2Rss.fetch_playlist_videos(channel_id):
            vid = (snippet.get('resourceId', {})
                          .get('videoId'))

            info = Youtube2Rss.fetch_video_info(vid)

            # build <key, value> dict where
            # key = video id and value = snippet & info
            videos[vid] = {'snippet': snippet, 'info': info}

        return videos

    @staticmethod
    def fetch_video_info(self, video_id):
        try:
            options = {}
            with YoutubeDL(options) as ydl:
                return ydl.extract_info(video_id, download=False)

        except UnavailableVideoError:
            print('Video is unavailable')

        except MaxDownloadsReached:
            print('Reached the maximum of downloads.')

    @staticmethod
    def fetch_playlist_videos(self, playlist_id):
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
            return [item['snippet'] for item in data['items']]

        except RequestException:
            print('HTTP Request failed')


if __name__ == '__main__':
    fire.Fire(Youtube2Rss)
