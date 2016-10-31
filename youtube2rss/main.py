#!/usr/bin/env python3.4
from os import walk
from xml.etree import ElementTree as et
import youtube_dl
import datetime
import urllib
import json
import sys
import os


# download a channel and return array of downloaded videos.
# channel (options) are described in the channel_file
# => see read_channel_file for more.
def download(channel, downloads):
    verbose = channel.get('verbose_output', False)
    download_settings = channel.get('download')
    archive_file = get_download_archive_filepath(channel)
    within_range = youtube_dl.utils.DateRange(
        start=download_settings.get('from'),
        end=download_settings.get('to')
    )

    # you can find all the options in the YoutubeDL.py file on Github, see:
    # https://github.com/rg3/youtube-dl/blob/master/youtube_dl/YoutubeDL.py#L131-L291
    #
    options = {
        'quiet': not verbose,                   # do not print messages to standard out
        'format': '22',                         # figure out with youtube-dl -F => 22 = video/mp4
        'download_archive': archive_file,       # file that tracks downloads, videos present in file are not downloaded again
        'daterange': within_range,              # date range of videos we are going to download
        'restrictfilenames': True,              # do not allow "&" and spaces in file names
        'ignoreerrors': True,                   # can happen when format is not available, then just skip
        'writeinfojson': True,                  # write the video description to .info.json
        'nooverwrites': True,                   # prevent overwriting files if we have them
        'progress_hooks': [
            lambda progress: progress_hook(progress, channel, downloads)
        ]
    }

    with youtube_dl.YoutubeDL(options) as ydl:
        ydl.download([channel.get('channel')])

    # sort the video by upload_date, given as a string => YYYYMMDD.
    downloads.sort(key=lambda video: video.get('metadata', {}).get('upload_date'))

    return downloads


# progress hook that gets called during download =>
# this callback gets progress that is defined like this:
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
        filename_metadata = '{filename}{extension}'.format(
            filename=base_filename,
            extension='.info.json')

        video = {
            'filename_video': filename_video,
            'filename_video_url': urllib.parse.quote_plus(filename_video),
            'filename_metadata': filename_metadata,
            'metadata': get_metadata(filename_metadata),
            'channel': channel,
        }

        downloads.append(video)


# get the meta data we care about there is much more
# (different formats etc.) but we do not need it anyways.
def get_metadata(filename):
    with open(filename) as metadata_file:
        video_info = json.load(metadata_file)

        metadata = {
            'id': video_info.get('id'),                                # id of the video
            'description': video_info.get('description'),              # video description
            'title': video_info.get('title'),                          # short title of video
            'full_title': video_info.get('full_title'),                # full title of the video
            'thumbnail': video_info.get('thumbnail'),                  # thumbnail of video
            'upload_date': video_info.get('upload_date', '20160101'),  # date in YYYYDDMM
            'playlist_title': video_info.get('playlist_title'),        # name of the play list
            'webpage_url': video_info.get('webpage_url'),              # link to Youtube video
            'uploader_url': video_info.get('uploader_url'),            # link to profile
            'filesize': video_info.get('filesize', 0),                 # file size in bytes
            '_video_filename': video_info.get('_filename'),            # filename of the video file
            '_metadata_filename': filename,                            # filename of meta data file
            '_url': video_info.get('url'),                             # points to mp4/video (FIXME)
        }

        return metadata


# build the RSS feed & write it to feed_output_file_name.
def build_rss_feed(channel_info, channel_downloads):
    root = build_rss_root(channel_info)
    channel = root.find('channel')

    # append episodes aka 'items'
    for video in channel_downloads:
        item = build_rss_episode_item(video, channel_info)
        channel.append(item)

    write_rss_feed(channel_info, root)


# build the minimal root // channel RSS feed.
def build_rss_root(channel_info):
    root = et.Element('rss')
    root.set('version', '2.0')
    root.set('xmlns:itunes', 'http://www.itunes.com/dtds/podcast-1.0.dtd')
    channel = et.SubElement(root, 'channel')
    rss = channel_info.get('rss')

    # add minimal set of elements to channel
    title = et.SubElement(channel, 'title')
    title.text = rss.get('title')

    itunes_image = et.SubElement(channel, 'itunes:image')
    itunes_image.set('href', rss.get('image'))

    itunes_author = et.SubElement(channel, 'itunes:author')
    itunes_author.text = rss.get('author')

    link = et.SubElement(channel, 'link')
    link.text = rss.get('link')

    description = et.SubElement(channel, 'description')
    description.text = rss.get('description')

    return root


# build the minimal item (aka episodes):
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

    enclosure_url = '{base_url}{filename}'.format(
        base_url=channel.get('rss').get('feed_base_url'),
        filename=video.get('filename_video_url')
    )

    enclosure = et.SubElement(item, 'enclosure')
    enclosure.set('url', enclosure_url)
    enclosure.set('length', str(metadata.get('filesize')))
    enclosure.set('type', 'video/mp4')

    # pubDate is a bit clowny. The expected format is: Wed, 03 Nov 2015 19:18:00 GMT 🙄
    upload_date = datetime.datetime.strptime(metadata.get('upload_date'), '%Y%m%d').date()
    upload_date_formated = upload_date.strftime('%a, %d %b %Y 12:00:00 GMT')

    pubDate = et.SubElement(item, 'pubDate')
    pubDate.text = upload_date_formated

    return item  # minimal item tag


def write_rss_feed(channel_info, root):
    rss = channel_info.get('rss')
    rss_file = rss.get('feed_output_file_name')

    root_et = et.ElementTree(root)
    root_et.write(
        rss_file,
        xml_declaration=True,
        encoding='utf-8'
    )


# delete files that are not used anymore (see keep_latest)
# does not delete .rss, .rss.json and download_archive.
def discard_old_downloads(channel, downloads):
    files_to_keep = []     # these are the good guys
    files_to_discard = []  # these are the bad guys!

    # keep: the feed itself .rss
    rss_feed_file = channel.get('rss').get('feed_output_file_name')
    files_to_keep.append(rss_feed_file)

    # keep: the download_archive file
    archive_file = get_download_archive_filepath(channel)
    files_to_keep.append(archive_file)

    # keep: the processing file .rss.json
    files_to_keep.append(get_processing_filepath(channel))

    # keep: latest downloads, adjust with download.keep_latest
    keep_latest = channel.get('download').get('keep_latest')
    for download in downloads[-keep_latest:]:
        metadata_file = download.get('metadata').get('_metadata_filename')
        video_file = download.get('metadata').get('_video_filename')
        files_to_keep.append(metadata_file)
        files_to_keep.append(video_file)

    # discard: assume guilty until proven innocent
    for (dirpath, dirnames, filenames) in walk('.'):
        files_to_discard.extend(filenames)
        break

    # discard: files_to_discard without files_to_keep
    files_to_discard = list(set(files_to_discard) - set(files_to_keep))
    for file_to_discard in files_to_discard:
        print('  ➟ Discarding {filename}'.format(filename=file_to_discard))
        os.remove(file_to_discard)


# filename of download_archive (an option by YoutubeDL).
def get_download_archive_filepath(channel):
    channel = channel.get('channel')
    return '{channel}_download_archive'.format(
        channel=channel
    )


# filename of our own processing file (dump of downloads)
def get_processing_filepath(channel):
    rss = channel.get('rss')
    rss_file = rss.get('feed_output_file_name')
    return '{rss_file}.json'.format(
        rss_file=rss_file
    )


def write_processing_file(channel, downloads):
    with open(get_processing_filepath(channel), 'w') as output_file:
        json.dump(downloads, output_file)


def read_processing_file(channel):
    try:
        with open(get_processing_filepath(channel), 'r') as input_file:
            return json.load(input_file)
    except:
        return []  # no such file, or whatever


# read a channel from json for the required
# structure see casey.json
def read_channel_file(argv):
    if len(argv) != 2:
        print(' ➟ Aborting. Please specify a channel json as parameter.')
        sys.exit(1)

    # we only have this one parameter
    channel_json_filepath = argv[1]

    try:
        with open(channel_json_filepath, 'r') as input_file:
            return json.load(input_file)
    except:
        print(' ➟ Aborting. Can not parse file {filename}'.format(
            filename=channel_json_filepath
        ))
        sys.exit(1)


def main():
    print('⏳  Preparing channel download...')
    channel = read_channel_file(sys.argv)
    downloads = read_processing_file(channel)

    print('🌍  Downloading channel {channel}...'
          .format(channel=channel.get('channel')))
    downloads = download(channel, downloads)

    print('⚙  Building RSS Feed...')
    build_rss_feed(channel, downloads)

    print('🗑  Cleaning up...')
    discard_old_downloads(channel, downloads)
    write_processing_file(channel, downloads)

    print('🍹  Finalizing... Done.')

main()  # let's rock 🐣
