Download a Youtube channel and build a RSS podcast feed for it.

### Motivation 🤔
My growing number of Youtube Channel Subscriptions caused a lot of
frustration with the official Youtube app. The app doesn't allow me
to download videos. Neither is it possible to resume playback nor
can I play a video when the app is not on screen. Features that my
podcast client of choice, PocketCasts already has.

So the solution is simple, just get all the Youtube Subscriptions to
my podcast client. This is exactly what this script does:

- Download all videos from a channel (within a given date range).
- Build a subscribe-able (iTunes RSS feed)[http://www.itunes.com/dtds/podcast-1.0.dtd]
  which is compatible with any Podcast client.
- Optional: Delete old episodes to save precious disk space.

### Getting Started 🚀

- Install all required packages: `pip3 install -r requirements.txt`
- Edit the configuration file (see `casey.json` for an example)
- Run the script with: `./youtube2rss/main.py ./youtube2rss/casey.json`

### Configuration, see `casey.json` 🔧
```
  {
    "channel": "ytuser:caseyneistat",                           # either username (prefix with ytuser:{username}), playlist id or channel id.
    "verbose_output": true,                                     # optional: show debug output, errors are always enabled
    "download": {
      "from": "today-1week",                                    # date range you wish to download, accepts: -xday, -xhour, -xweek
      "to": "today",                                            # ^ the end date of the range, accepts the same format
      "keep_latest": 4                                          # Max. amount of episodes you want to keep
    },
    "rss": {
      "title": "Casey Neistat",                                 # podcast title
      "author": "Casey Neistat",                                # podcast author
      "description": "Casey's Vlogs",                           # podcast description
      "image": "http://your-domain.com/youtube2rss/feed.png",   # podcast image
      "link": "https://www.youtube.com/user/caseyneistat"       # podcast website link
      "feed_base_url": "http://your-domain.com/youtube2rss/",   # location where you put the downloads from youtube2rss
      "feed_output_file_name": "feed.rss",                      # name of the generated feed file => feed_base_url/feed_output_file_name
    }
  }
```

