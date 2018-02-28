from dataclasses import dataclass

@dataclass(frozen=True, init=True)
class DownloadConfiguration:
    range_from: str = 'today-1week'
    range_to: str = 'today'
    keep_latest: int = 4


@dataclass(frozen=True, init=True)
class RssConfiguration:
    title: str
    author: str
    description: str
    image: str
    feed_base_url: str
    feed_output_file_name: str
    link: str


@dataclass(frozen=True, init=True)
class Configuration:
    channel: str
    rss: RssConfiguration
    download: DownloadConfiguration = DownloadConfiguration()
    verbose_output: bool = False

    @staticmethod
    def create_configuration_from_dict(configuration):
        download_configuration = DownloadConfiguration(
            **configuration.pop('download')
        )

        rss_configuration = RssConfiguration(
            **configuration.pop('rss')
        )

        return Configuration(
            download=download_configuration,
            rss=rss_configuration,
            **configuration,
        )
