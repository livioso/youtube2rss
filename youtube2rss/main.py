#!/usr/bin/env python3.4
from xml.etree import ElementTree as et
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
        build_rss_feed()


def download(username):
    # this should be fine as we run the cron job more frequently anyway
    within_last_day = youtube_dl.utils.DateRange(start='today-1day', end='today')

    options = {
        'daterange': within_last_day,
        'format': '22',                 # 22 => video/mp4. Figure out with youtube-dl -F.
        'ignoreerrors': True,           # can happen when format is not available, then just skip.
        'writeinfojson': True,          # write the video description to .info.json.
        'nooverwrites': True,           # prevent overwriting files.
        'progress_hooks': [progress_hook]
    }

    with youtube_dl.YoutubeDL(options) as ydl:
        ydl.download(['ytuser:{username}'.format(username=username)])


def build_rss_episode_item(video):
    metadata = video.get('metadata')

    # build item with the minimal set of tags
    item = et.Element('item')
    title = et.SubElement(item, 'title')
    title.text = metadata.get('full_title')

    link = et.SubElement(item, 'link')
    link.text = metadata.get('webpage_url')

    description = et.SubElement(item, 'description')
    description.text = metadata.get('description')

    enclosure_url = "{base_url}{filename}".format(
        base_url='http://livio.li/podcasts/yt/',
        filename=video.get("filename_video_url")
    )

    enclosure = et.SubElement(item, 'enclosure')
    enclosure.set('url', enclosure_url)
    enclosure.set('length', str(metadata.get('filesize')))
    enclosure.set('type', 'video/mp4')

    pubDate = et.SubElement(item, 'pubDate')
    pubDate.text = 'Wed, 03 Nov 2015 19:18:00 GMT'  # FIXME

    return item  # minimal item tag


def build_rss_feed():
    root = et.Element('rss')
    root.set('version', "2.0")
    channel = et.SubElement(root, 'channel')

    # add minimal set of elements to channel
    title = et.SubElement(channel, 'title')
    title.text = 'Livioso'

    itunes_image = et.SubElement(channel, 'itunes:image')
    itunes_image.set('href', "https://yt3.ggpht.com/-x2NNN2y49G0/AAAAAAAAAAI/AAAAAAAAAAA/RhwVaxMvqW8/s100-c-k-no-mo-rj-c0xffffff/photo.jpg")

    itunes_author = et.SubElement(channel, 'itunes:author')
    itunes_author.text = 'Livioso'

    link = et.SubElement(channel, 'link')
    link.text = 'http://livio.li/podcasts/'

    description = et.SubElement(channel, 'description')
    description.text = 'Livioso Podcasts'

    # append episodes (aka 'items')
    for video in downloaded_videos:
        item = build_rss_episode_item(video)
        channel.append(item)

    # dump the tree as feed.xml
    tree = et.ElementTree(root)
    tree.write('feed.rss', xml_declaration=True, encoding='utf-8')


def cleanup():
    print("Clean up unused, old files")


def main():
    download(username="caseyneistat")
    # build_rss_feed


main()
