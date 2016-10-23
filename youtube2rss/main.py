#!/usr/bin/env python3.4
from os import walk
from xml.etree import ElementTree as et
import youtube_dl
import datetime
import urllib
import json
import os


# get the meta data we care about there is much more
# (different formats etc.) but we do not need it anyways.
def get_metadata(filename):
    with open(filename) as metadata_file:
        video_info = json.load(metadata_file)

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
            "_video_filename": video_info.get("_filename"),            # filename of the video file
            "_metadata_filename": filename,                            # filename of meta data file
            "_url": video_info.get("url"),                             # points to mp4/video (FIXME)
            "_keep": True,                                             # keep only once
        }

        return metadata


# progress hook that gets called during download.
# => progress looks like this:
#
# {
#   '_total_bytes_str': '391.30MiB',
#   'filename': 'five million-UqADuUBMoZ4.mp4',
#   'status': 'finished',
#   'total_bytes': 410304772
# }
#
def progress_hook(progress, channel, downloads):
    if progress.get('status') == 'finished':
        filename_video = progress.get('filename')
        base_filename = os.path.splitext(filename_video)[0]

        # the meta data file is stored with the extension .info.json
        filename_metadata = "{filename}{extension}".format(
            filename=base_filename,
            extension=".info.json")

        video = {
            'filename_video': filename_video,
            'filename_video_url': urllib.parse.quote_plus(filename_video),
            'filename_metadata': filename_metadata,
            'metadata': get_metadata(filename_metadata),
            'channel': channel,
        }

        downloads.append(video)


def download(channel, downloads):
    verbose = channel.get("verbose_output")
    download_settings = channel.get("download")
    archive_file = get_download_archive_filepath(channel)
    within_range = youtube_dl.utils.DateRange(
        start=download_settings.get("from"),
        end=download_settings.get("to")
    )

    # you can find all the options in the YoutubeDL.py file on Github, see:
    # https://github.com/rg3/youtube-dl/blob/master/youtube_dl/YoutubeDL.py#L131-L291
    #
    options = {
        'quiet': not verbose,                   # do not print messages to standard out.
        'format': "22",                         # figure out with youtube-dl -F => 22 = video/mp4.
        'download_archive': archive_file,       # file that tracks downloads, videos present in file are not downloaded again.
        'daterange': within_range,              # date range of videos we are going to download.
        'ignoreerrors': True,                   # can happen when format is not available, then just skip.
        'writeinfojson': True,                  # write the video description to .info.json.
        'nooverwrites': True,                   # prevent overwriting files if we have them.
        'progress_hooks': [
            lambda progress: progress_hook(progress, channel, downloads)
        ]
    }

    with youtube_dl.YoutubeDL(options) as ydl:
        ydl.download(['ytuser:{username}'.format(
            username=channel.get("username")
        )])

    return downloads


def get_processing_filepath(channel):
    rss = channel.get("rss")
    rss_file = rss.get("feed_output_file_name")
    return "{rss_file}.json".format(
        rss_file=rss_file
    )


def get_download_archive_filepath(channel):
    username = channel.get("username")
    return "{username}_download_archive".format(
        username=username
    )


def read_processing_file(channel):
    try:
        with open(get_processing_filepath(channel), 'r') as input_file:
            return json.load(input_file)
    except:
        return []  # no such file, or whatever


def write_processing_file(channel, downloads):
    with open(get_processing_filepath(channel), 'w') as output_file:
        json.dump(downloads, output_file)


def build_rss_episode_item(video, channel):
    metadata = video.get('metadata')

    # build item with the minimal set of tags
    item = et.Element('item')
    title = et.SubElement(item, 'title')
    title.text = metadata.get('title')

    link = et.SubElement(item, 'link')
    link.text = metadata.get('webpage_url')

    description = et.SubElement(item, 'description')
    description.text = metadata.get('description')

    enclosure_url = "{base_url}{filename}".format(
        base_url=channel.get("rss").get("feed_base_url"),
        filename=video.get("filename_video_url")
    )

    enclosure = et.SubElement(item, 'enclosure')
    enclosure.set('url', enclosure_url)
    enclosure.set('length', str(metadata.get('filesize')))
    enclosure.set('type', 'video/mp4')

    # pubDate is a bit clowny. The expected format is: Wed, 03 Nov 2015 19:18:00 GMT 🙄
    upload_date = datetime.datetime.strptime(metadata.get("upload_date"), "%Y%m%d").date()
    upload_date_formated = upload_date.strftime("%a, %d %b %Y 12:00:00 GMT")

    pubDate = et.SubElement(item, 'pubDate')
    pubDate.text = upload_date_formated

    return item  # minimal item tag


# build the minimal root // channel RSS feed.
def build_rss_root(channel_info):
    root = et.Element('rss')
    root.set('version', "2.0")
    root.set('xmlns:itunes', "http://www.itunes.com/dtds/podcast-1.0.dtd")
    channel = et.SubElement(root, 'channel')

    rss = channel_info.get("rss")

    # add minimal set of elements to channel
    title = et.SubElement(channel, 'title')
    title.text = rss.get("title")

    itunes_image = et.SubElement(channel, 'itunes:image')
    itunes_image.set('href', rss.get("image"))

    itunes_author = et.SubElement(channel, 'itunes:author')
    itunes_author.text = rss.get("author")

    link = et.SubElement(channel, 'link')
    link.text = rss.get("link")

    description = et.SubElement(channel, 'description')
    description.text = rss.get("description")

    return root


def build_rss_feed(channel_info, channel_downloads):
    root = build_rss_root(channel_info)
    channel = root.find("channel")

    # append episodes aka 'items'
    for video in channel_downloads:
        item = build_rss_episode_item(video, channel_info)
        channel.append(item)

    write_rss_feed(channel_info, root)


def write_rss_feed(channel_info, root):
    print("🚚  Writing RSS feed file...")
    rss = channel_info.get("rss")
    rss_file = rss.get("feed_output_file_name")

    root_et = et.ElementTree(root)
    root_et.write(
        rss_file,
        xml_declaration=True,
        encoding='utf-8'
    )


def discard_old_files(channel, downloads):
    files_to_keep = []     # these are the good guys
    files_to_discard = []  # these are the bad guys!

    # keep: the feed itself .rss
    rss_feed_file = channel.get("rss").get("feed_output_file_name")
    files_to_keep.append(rss_feed_file)

    # keep: the download_archive file
    archive_file = get_download_archive_filepath(channel)
    files_to_keep.append(archive_file)

    # keep: the processing file .rss.json
    files_to_keep.append(get_processing_filepath(channel))

    # keep: all (in this cycle) downloaded videos & meta data
    for download in downloads[-50:]:
        metadata_file = download.get("metadata").get("_metadata_filename")
        video_file = download.get("metadata").get("_video_filename")
        download["metadata"]["_keep"] = True
        files_to_keep.append(metadata_file)
        files_to_keep.append(video_file)

    # discard: assume guilty until proven innocent
    for (dirpath, dirnames, filenames) in walk("."):
        files_to_discard.extend(filenames)
        break

    # discard: files_to_discard without files_to_keep
    files_to_discard = list(set(files_to_discard) - set(files_to_keep))
    print(files_to_keep)
    print(files_to_discard)
    for file_to_discard in files_to_discard:
        print("  ➟ Discarding {filename}".format(filename=file_to_discard))
        os.remove(file_to_discard)


def main():
    r00k123123 = {
        "username": "r00k123123",
        "verbose_output": False,
        "download": {
            "from": "today-6year",
            "to": "today",
            "keep_latest": 5,
        },
        "rss": {
            "title": "Livioso - QB",
            "author": "😎",
            "description": "QB",
            "image": "goo.gl/VkvYQN",
            "feed_base_url": "http://livio.li/podcasts/yt/",
            "feed_output_file_name": "feed-qb.rss",
            "link": "https://www.youtube.com/user/QuickyBabyTV",
        }
    }

    # TODO: move this to a JSON
    # download & build feed
    # for these channels
    channels_to_download = [
        r00k123123,
        # quickybaby,
        # caseyneistat,
        # johnoliver,
    ]

    # TODO: Load download_videos before
    # downloading & dump it to JSON after.
    for channel in channels_to_download:

        # keep track of previous downloads
        downloads = read_processing_file(channel)

        print("🌍  Downloading channel {username}..."
              .format(username=channel.get("username")))
        downloads = download(channel, downloads)

        print("🚚  Building RSS Feed...")
        build_rss_feed(channel, downloads)

        print("🗑  Discarding old files...")
        discard_old_files(channel, downloads)

        write_processing_file(channel, downloads)

        print("🍹  Finalizing... Done.")

main()

#     caseyneistat = {
#         "username": "caseyneistat",
#         "preferred_video_format": "22",                             # video/mp4 => see youtube-dl -F.
#         "download_videos_start_date": "today-7day",                 # should be fine, since yesterday.
#         "download_videos_end_date": "today",                        # cron job runs frequently anyway.
#         "file_usage_quota_gb": 2,
#         "rss": {                                                    # mostly irrelevant, just required
#             "title": "Livioso - Casey Neistat",                     # for a minimal viable set of tags.
#             "image": "goo.gl/VkvYQN",                               # FIXME used as podcast image
#             "description": "Casey's Vlogs",                         # ... whatever (but required)
#             "link": "https://www.youtube.com/user/caseyneistat",    # ... whatever (^)
#             "author": "😎",                                         # ... whatever (^)
#             "base_url": "http://livio.li/podcasts/yt/",             # where the files will accessible
#             "feed_output_file_name": "feed-casey.rss"               # is under base_url
#         }
#     }

#     johnoliver = {
#         "username": "LastWeekTonight",
#         "preferred_video_format": "22",
#         "download_videos_start_date": "today-7day",
#         "download_videos_end_date": "today",
#         "file_usage_quota_gb": 2,
#         "rss": {
#             "title": "Livioso - Last Week Tonight",
#             "image": "goo.gl/VkvYQN",                              # FIXME
#             "description": "Last Week Tonight",
#             "link": "https://www.youtube.com/user/LastWeekTonight",
#             "author": "😎",
#             "base_url": "http://livio.li/podcasts/yt/",
#             "feed_output_file_name": "feed-lwt.rss"
#         }
#     }

#     chromedevelopers = {
#         "username": "ChromeDevelopers",
#         "preferred_video_format": "22",
#         "download_videos_start_date": "today-7day",
#         "download_videos_end_date": "today",
#         "file_usage_quota_gb": 2,
#         "rss": {
#             "title": "Livioso - Chrome Developers",
#             "image": "goo.gl/VkvYQN",                              # FIXME
#             "description": "Chrome Developers",
#             "link": "https://www.youtube.com/user/ChromeDevelopers",
#             "author": "😎",
#             "base_url": "http://livio.li/podcasts/yt/",
#             "feed_output_file_name": "feed-cd.rss"
#         }
#     }

#     quickybaby = {
#         "username": "QuickyBabyTV",
#         "preferred_video_format": "22",
#         "download_videos_start_date": "today-7day",
#         "download_videos_end_date": "today",
#         "file_usage_quota_gb": 2,
#         "rss": {
#             "title": "Livioso - QB",
#             "image": "goo.gl/VkvYQN",                              # FIXME
#             "description": "QB",
#             "link": "https://www.youtube.com/user/QuickyBabyTV",
#             "author": "😎",
#             "base_url": "http://livio.li/podcasts/yt/",
#             "feed_output_file_name": "feed-qb.rss"
#         }
#     }
