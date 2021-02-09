"""
Symfony Profiler module.

Contains a Profiler class for communicating with the Symfony profiler.
"""

import csv
from io import StringIO
from pathlib import Path
from urllib.parse import urljoin

from requests import Session
from bs4 import BeautifulSoup

from eos.core import Base


class Profiler(Base):
    """
    Symfony Profiler.

    Implements the Symfony web profiler bundle.
    Provides methods to communicate with the profiler.
    """

    path = '_profiler'
    cache_path = 'profiler/index.csv'

    def __init__(self, url, session=None):
        """
        Initialization.

        :param url: target URL
        """

        self._url = urljoin(url + '/', self.path)
        self.session = session or Session()
        self._cache = None

    def get(self, token='', **kwargs):
        """
        GET request to the profiler.

        Perform a GET request to the profiler with an optional part of the URL.

        :param token: last part of the URL (e.g: token)
        :param kwargs: wrapped to requests.get
        """

        url = self.url(token)
        self.log.debug(url)
        r = self.session.get(url, **kwargs)
        return r

    def open(self, *path):
        """
        Get project file.

        Use the Symfony > 3.4 profiler feature to preview files with
        _profiler/open?file=path/to/file.
        Parses the response to extract the actual file content.

        :param path: file path elements relative to the project directory
        :return:
        """

        path = str(Path(*path))
        r = self.session.get(self.url('open'), params={'file': path, 'line': 1})
        if r.status_code != 200 or '<h2>Token not found</h2>' in r.text:
            return None
        return self.parse_file_preview(r.text)

    @staticmethod
    def parse_file_preview(data):
        """
        Parse the file preview HTML to extract the raw source code.

        Each source code line is in a <code> tag. Simply join them with new lines.
        Note that binary files are likely to be corrupted.

        :param data: HTML data to parse
        :return: raw source code
        """

        soup = BeautifulSoup(data.replace('&nbsp;', ' '), 'html.parser')
        codes = soup.find_all('code')
        return '\n'.join(code.text for code in codes)

    def url(self, token=''):
        """URL builder."""
        return urljoin(self._url + '/' if token else self._url, token)

    def cache(self, symfony_cache=None, refresh=True):
        if refresh or self._cache is None:
            cache_path = str(Path(symfony_cache, self.cache_path))
            index = self.open(cache_path)
            self._cache = list(csv.reader(StringIO(index)))
        return self._cache

    def logs(self, filters=None, symfony_cache=None, refresh=True):
        all = lambda token, ip, method, url, timestamp, x, code: True
        filters = filters or all
        wrapper = lambda row: filters(*row)
        return list(filter(wrapper, self.cache(symfony_cache, refresh)))
