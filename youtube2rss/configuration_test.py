import unittest
from dataclasses import FrozenInstanceError
from yolo import Configuration, RssConfiguration, DownloadConfiguration


class RssConfigurationTest(unittest.TestCase):

    RSS_TEST_CONFIGURATION = {
        'title': 'test_title',
        'author': 'test_author',
        'description': 'test_description',
        'image': 'test_image',
        'feed_base_url': 'test_feed_base_url',
        'feed_output_file_name': 'test_feed_output_file_name',
        'link': 'test_link'
    }

    def setUp(self):
        self.cut = RssConfiguration(
            **self.RSS_TEST_CONFIGURATION
        )

    def test_attributes_match_test_configuration(self):
        for attribute, expected in self.RSS_TEST_CONFIGURATION.items():
            self.assertEqual(self.cut.__getattribute__(attribute), expected)

    def test_instance_is_frozen(self):
        with self.assertRaises(FrozenInstanceError):
            self.cut.title = 'should_fail'


class DownloadConfigurationTest(unittest.TestCase):

    DOWNLOAD_TEST_CONFIGURATION = {
        'range_from': 'test_range_from',
        'range_to': 'test_range_to',
        'keep_latest': 0
    }

    def setUp(self):
        self.cut = DownloadConfiguration(
            **self.DOWNLOAD_TEST_CONFIGURATION
        )

    def test_attributes_match_test_configuration(self):
        for attribute, expected in self.DOWNLOAD_TEST_CONFIGURATION.items():
            self.assertEqual(self.cut.__getattribute__(attribute), expected)

    def test_instance_is_frozen(self):
        with self.assertRaises(FrozenInstanceError):
            self.cut.range_from = 'should_fail'


class ConfigurationTest(unittest.TestCase):

    TEST_CONFIGURATION = {
        'channel': 'test_channel',
        'verbose_output': True,
        'download': {
            'range_from': 'test_range_from',
            'range_to': 'test_range_to',
            'keep_latest': 0
        },
        'rss': {
            'title': 'test_title',
            'author': 'test_author',
            'description': 'test_description',
            'image': 'test_image',
            'feed_base_url': 'test_feed_base_url',
            'feed_output_file_name': 'test_feed_output_file_name',
            'link': 'test_link'
        }
    }

    def test_walking_skeleton(self):
        self.cut = Configuration.create_configuration_from_dict(
            self.TEST_CONFIGURATION
        )


if __name__ == '__main__':
    unittest.main()
