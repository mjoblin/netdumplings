import json
import logging
import logging.config
import time

import pytest

from netdumplings.exceptions import InvalidDumpling
from netdumplings._shared import configure_logging, validate_dumpling


@pytest.fixture(scope='function')
def packet_dumpling_dict():
    return {
        'metadata': {
            'chef': 'TestChef',
            'kitchen': 'TestKitchen',
            'creation_time': time.time(),
            'driver': 'packet',
        },
        'payload': {
            'one': 1,
            'two': [1, 2, 3],
            'three': {
                'four': 5,
            }
        }
    }


class TestShared:
    """
    Test shared utility functions.
    """
    def test_valid_dumpling(self, packet_dumpling_dict):
        """
        Test validation of JSON-serialized dumplings.
        """
        assert validate_dumpling(
            json.dumps(packet_dumpling_dict)) == packet_dumpling_dict

    def test_dumpling_with_missing_chef(self, packet_dumpling_dict):
        """
        Test dumpling missing a chef name.
        """
        del packet_dumpling_dict['metadata']['chef']

        with pytest.raises(InvalidDumpling):
            validate_dumpling(json.dumps(packet_dumpling_dict))

    def test_invalid_json_dumpling(self):
        """
        Test a dumpling containing text which is not legitimately
        JSON-serialized.
        """
        with pytest.raises(InvalidDumpling):
            validate_dumpling("{'invalid_single_quotes': 'value'}")

    def test_logging_formatter(self):
        """
        Test that the logging formatter gets configured like we expect.
        """
        configure_logging()

        assert logging.Formatter.converter == time.gmtime
        assert logging.Formatter.default_time_format == '%Y-%m-%dT%H:%M:%S'
        assert logging.Formatter.default_msec_format == '%s.%03d'

    def test_logging_config_file(self, monkeypatch):
        """
        Test NETDUMPLINGS_LOGGING_CONFIG environment variable for setting the
        logging config.
        """
        # We still want the Formatter to be configured.
        assert logging.Formatter.converter == time.gmtime
        assert logging.Formatter.default_time_format == '%Y-%m-%dT%H:%M:%S'
        assert logging.Formatter.default_msec_format == '%s.%03d'

        # Set NETDUMPLINGS_LOGGING_CONFIG to point to a test logging config.
        logging_config_file = 'tests/data/logging.json'
        monkeypatch.setenv('NETDUMPLINGS_LOGGING_CONFIG', logging_config_file)

        configure_logging()

        # The test config file sets all the loggers to ERROR.
        assert logging.getLogger('netdumplings').level == logging.ERROR
        assert logging.getLogger(
            'netdumplings.dumplinghub').level == logging.ERROR
        assert logging.getLogger(
            'netdumplings.dumplingkitchen').level == logging.ERROR
        assert logging.getLogger(
            'netdumplings.dumplingeater').level == logging.ERROR

    def test_invalid_logging_config_file(self, monkeypatch, mocker):
        """
        Test NETDUMPLINGS_LOGGING_CONFIG environment variable for setting the
        logging config with an invalid file. Should fall back on basicConfig().
        """
        # We still want the Formatter to be configured.
        assert logging.Formatter.converter == time.gmtime
        assert logging.Formatter.default_time_format == '%Y-%m-%dT%H:%M:%S'
        assert logging.Formatter.default_msec_format == '%s.%03d'

        # Set NETDUMPLINGS_LOGGING_CONFIG to point to a test logging config.
        logging_config_file = 'tests/data/logging_bogus.json'
        monkeypatch.setenv('NETDUMPLINGS_LOGGING_CONFIG', logging_config_file)
        spy_basic_config = mocker.spy(logging, 'basicConfig')

        configure_logging(logging.DEBUG)

        spy_basic_config.assert_called_once_with(level=logging.DEBUG)

    def test_missing_logging_config_file(self, monkeypatch, mocker):
        """
        Test NETDUMPLINGS_LOGGING_CONFIG environment variable for setting the
        logging config with a missing file. Should fall back on basicConfig().
        """
        # We still want the Formatter to be configured.
        assert logging.Formatter.converter == time.gmtime
        assert logging.Formatter.default_time_format == '%Y-%m-%dT%H:%M:%S'
        assert logging.Formatter.default_msec_format == '%s.%03d'

        # Set NETDUMPLINGS_LOGGING_CONFIG to point to a test logging config.
        logging_config_file = 'does_not_exist.json'
        monkeypatch.setenv('NETDUMPLINGS_LOGGING_CONFIG', logging_config_file)
        spy_basic_config = mocker.spy(logging, 'basicConfig')

        configure_logging(logging.DEBUG)

        spy_basic_config.assert_called_once_with(level=logging.DEBUG)
