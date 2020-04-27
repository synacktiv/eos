"""Routes EOS plugin."""

from random import choice
from string import ascii_lowercase

from eos.plugins import AbstractPlugin


class Plugin(AbstractPlugin):
    """
    Routes EOS plugin.

    Extract the list of registered routes on the target by triggering a 404
    error. When analyzing a request, the routing section of the profiler view
    enumerates registered routes that have been compared against the requested
    URL. This list stops when a route matches. When a request triggers a 404,
    the profiler will list all registered routes.
    """

    name = 'Routes'

    ignore = ['/_profiler', '/_error', '/_wdt']
    """List of routes to ignore."""

    def run(self):
        """
        Get application routes.

        1. Request a random URL to trigger a 404 response.
        2. Extract the debug token from it and request the associated routing
           panel.
        3. Parse the HTML to extract the list of registered routes
        4. Filter out builtin routes (based on the self.ignore list) using the
           self.filter method.

        The random URL is generated using a series of {rand}/{rand}/... to
        prevent parameterized routes from matching it.
        """

        # Trigger and ensure a 404
        self.log.debug('Triggering a 404 error')
        rand = '/'.join(choice(ascii_lowercase) for _ in range(12))
        r = self.symfony.get(rand)
        if r.status_code != 404:
            self.log.error('Target responded with status code %d!', r.status_code)
            return

        # Check that no route has matched
        r = self.symfony.profiler.get(r.token, params={'panel': 'router'})
        soup = self.parse(r.text)
        label = soup.find('span', class_='label', string='Matched route')
        route = label.find_previous('span', class_='value').text
        if route != '(none)':
            self.log.warning('Route matched: %s', route)

        # Extract routes while ignoring builtins (_profiler, _error and _wdt)
        table = soup.find('table', id='router-logs')
        routes = self.filter(table.find('tbody').find_all('tr'))
        if not routes:
            self.log.info('Did not find any route')
            return
        self.log.warning('Found the following routes:')
        for name, path in routes:
            self.symfony.routes[name] = path
            self.log.warning('  %s', path)

    @classmethod
    def filter(cls, entries):
        """Wrapper on generator version."""
        return list(cls._filter(entries))

    @classmethod
    def _filter(cls, entries):
        """Filter out builtin routes from cls.ignore."""
        for entry in entries:
            elements = entry.find_all('td')
            key = elements[1].text
            value = elements[2].text
            if any(value.startswith(_) for _ in cls.ignore):
                continue
            yield key, value
