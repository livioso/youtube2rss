from django.contrib import admin

# Register your models here.
from .models import Channel, RssOptions, DownloadOptions

admin.site.register(Channel)
admin.site.register(RssOptions)
admin.site.register(DownloadOptions)
