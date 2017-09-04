from os import walk
from xml.etree import ElementTree as et
import youtube_dl
import datetime
import hashlib
import logging
import urllib
import json
import sys
import os

logger = logging.getLogger(__name__)


def download(channel, downloads):
    '''
    Download a channel and return list of downloaded videos.
    Channel (options) are described in the channel_file
    → see read_channel_file for more.
    '''

    verbose = channel.get('verbose_output', False)
    download_settings = channel.get('download', {})
    archive_file = get_download_archive_filepath(channel)
    within_range = youtube_dl.utils.DateRange(
        start=download_settings.get('from', None),
        end=download_settings.get('to', 'today')
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

    with youtube_dl.YoutubeDL(options) as downloader:
        downloader.download([channel['channel']])

    # sort the video by upload_date, given as a string => YYYYMMDD.
    downloads.sort(key=lambda video: video.get('metadata', {}).get('upload_date'))

    return downloads


def progress_hook(progress, channel, downloads):
    '''
    Progress hook that gets called during download
    → this callback gets progress that is defined like this:
    {
      '_total_bytes_str': '391.30MiB',
      'filename': 'five million-UqADuUBMoZ4.mp4',
      'status': 'finished',
      'total_bytes': 410304772
    }
    '''

    if progress.get('status') == 'finished':
        filename_video = progress['filename']
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


def get_metadata(filename):
    '''
    Get the meta data we care about there is much more
    (different formats etc.) but we do not need it anyways.
    '''

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


def build_rss_feed(channel_info, channel_downloads):
    root = build_rss_root(channel_info)
    channel = root.find('channel')

    # append episodes aka 'items'
    for video in channel_downloads:
        item = build_rss_episode_item(video, channel_info)
        channel.append(item)

    return root


def build_rss_root(channel_info):
    root = et.Element('rss')
    root.set('version', '2.0')
    root.set('xmlns:itunes', 'http://www.itunes.com/dtds/podcast-1.0.dtd')
    channel = et.SubElement(root, 'channel')
    rss = channel_info['rss']

    # add minimal set of elements to channel
    title = et.SubElement(channel, 'title')
    title.text = rss['title']

    itunes_image = et.SubElement(channel, 'itunes:image')
    itunes_image.set('href', rss['image'])

    itunes_author = et.SubElement(channel, 'itunes:author')
    itunes_author.text = rss['author']

    link = et.SubElement(channel, 'link')
    link.text = rss['link']

    description = et.SubElement(channel, 'description')
    description.text = rss['description']

    return root


def build_rss_episode_item(video, channel):
    metadata = video['metadata']

    # build item with the minimal set of tags
    item = et.Element('item')
    title = et.SubElement(item, 'title')
    title.text = metadata['title']

    link = et.SubElement(item, 'link')
    link.text = metadata['webpage_url']

    description = et.SubElement(item, 'description')
    description.text = metadata['description']

    enclosure_url = '{base_url}{filename}'.format(
        base_url=channel['rss']['feed_base_url'],
        filename=video['filename_video_url']
    )

    enclosure = et.SubElement(item, 'enclosure')
    enclosure.set('url', enclosure_url)
    enclosure.set('length', str(metadata['filesize']))
    enclosure.set('type', 'video/mp4')

    # pubDate is a bit clowny. The expected format is: Wed, 03 Nov 2015 19:18:00 GMT 🙄
    upload_date = datetime.datetime.strptime(metadata.get('upload_date'), '%Y%m%d').date()
    upload_date_formated = upload_date.strftime('%a, %d %b %Y 12:00:00 GMT')

    pubDate = et.SubElement(item, 'pubDate')
    pubDate.text = upload_date_formated

    return item  # minimal item tag


def write_rss_feed(channel_info, root):
    rss = channel_info['rss']
    rss_file = rss['feed_output_file_name']

    root_et = et.ElementTree(root)
    root_et.write(
        rss_file,
        xml_declaration=True,
        encoding='utf-8'
    )


def discard_old_downloads(channel, downloads):
    '''
    Delete files that are not used anymore (only keep_latest)
    does not delete .rss, .rss.json and download_archive!
    '''

    files_to_keep = []     # these are the good guys
    files_to_discard = []  # these are the bad guys!

    # keep: the feed itself .rss
    rss_feed_file = channel['rss']['feed_output_file_name']
    files_to_keep.append(rss_feed_file)

    # keep: the download_archive file
    archive_file = get_download_archive_filepath(channel)
    files_to_keep.append(archive_file)

    # keep: the processing file .rss.json
    files_to_keep.append(get_processing_filepath(channel))

    # keep: latest downloads, adjust with download.keep_latest
    keep_latest = channel['download']['keep_latest']
    for download in downloads[-keep_latest:]:
        metadata_file = download['metadata']['_metadata_filename']
        video_file = download['metadata']['_video_filename']
        files_to_keep.append(metadata_file)
        files_to_keep.append(video_file)

    # discard: assume guilty until proven innocent
    for (dirpath, dirnames, filenames) in walk('.'):
        files_to_discard.extend(filenames)
        break

    # discard: files_to_discard without files_to_keep
    files_to_discard = list(set(files_to_discard) - set(files_to_keep))
    for file_to_discard in files_to_discard:
        logger.debug('  ➟ Discarding {filename}'.format(filename=file_to_discard))
        os.remove(file_to_discard)


def get_download_archive_filepath(channel):
    channel = channel['channel']
    # use hash as a valid channel can also be a channel url
    channel_hash = hashlib.md5(channel.encode('utf-8')).hexdigest()[:10]

    return '{channel}_download_archive'.format(
        channel=channel_hash
    )


def get_processing_filepath(channel):
    rss = channel['rss']
    rss_file = rss['feed_output_file_name']
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


def read_channel_file(argv):
    '''
    Read a channel from json for the required structure.
    '''

    if len(argv) != 2:
        logger.error(' ➟ Aborting. Please specify a channel json as parameter.')
        sys.exit(1)

    # we only have this one parameter
    channel_json_filepath = argv[1]

    try:
        with open(channel_json_filepath, 'r') as input_file:
            return json.load(input_file)
    except:
        logger.error(' ➟ Aborting. Can not parse file {filename}'.format(
            filename=channel_json_filepath
        ))
        sys.exit(1)


def main():
    logging.basicConfig(level=logging.DEBUG)

    logger.info(' ⏳  Preparing channel download...')
    channel = read_channel_file(sys.argv)
    downloads = read_processing_file(channel)

    logger.info(' 🌍  Downloading channel {channel}...'.format(
        channel=channel['channel']))
    downloads = download(channel, downloads)

    logger.info(' ⚙  Building RSS Feed...')
    rss_feed = build_rss_feed(channel, downloads)
    write_rss_feed(channel, rss_feed)

    logger.info(' 🗑  Cleaning up...')
    discard_old_downloads(channel, downloads)
    write_processing_file(channel, downloads)

    logger.info(' 🍹  Finalizing... Done.')


if __name__ == "__main__":
    main()

