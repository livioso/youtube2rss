from django.db import models


class DownloadOptions(models.Model):
    begin = models.CharField(max_length=30)
    end = models.CharField(max_length=30)
    keep_latest = models.IntegerField(default=5)


class RssOptions(models.Model):
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    image = models.URLField(max_length=200)
    feed_base_url = models.URLField(max_length=200)
    feed_output_file_name = models.CharField(max_length=100)
    link = models.URLField(max_length=200)


class Channel(models.Model):
    channel = models.CharField(max_length=200)
    download_options = models.ForeignKey(RssOptions, related_name='download_options', on_delete=models.CASCADE)
    rss_options = models.ForeignKey(RssOptions, related_name='rss_options', on_delete=models.CASCADE)
