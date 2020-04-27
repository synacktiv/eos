"""Project files EOS plugin."""

from requests import Request

from eos.plugins import AbstractPlugin


class Plugin(AbstractPlugin):
    """
    Project files EOS plugin.

    Fuzz the profiler's code visualization feature with a list of interesting project files.
    These files can contain sensible information.
    This plugin uses the EOS engine to perform its requests.
    """

    name = 'Project files'
    requirements = '3.0.0'
    security_url = 'https://security.symfony.com'

    def run(self):
        """
        Run.

        Read the wordlist and enqueue its content to the engine.
        Wait for it.
        Display the list of found files.
        """

        self.log.debug('Reading wordlist %s', self.wordlists)

        # Test
        data = self.symfony.profiler.open(self.symfony.root)
        if data is None:
            self.log.info('The target does not support file preview')
            return

        # Enqueue
        with open(self.wordlists) as file:
            i = 0
            for i, line in enumerate(file, 1):
                url = self.symfony.profiler.url('open')
                params = {'line': 1, 'file': line.strip()}
                self.engine.queue.put(Request(method='GET', url=url, params=params))
            self.log.debug('Enqueued %d entries', i)

        self.engine.join()
        found = [response for response in self.engine.results if response.status_code != 404]
        files = [resp.request.params['file'] for resp in found]

        # Composer lookup
        composer = [file for file in files if file.endswith('composer.lock')]
        if composer:
            self.log.info("Found: %s, run 'symfony security:check' or submit it at %s", composer[0], self.security_url)

        if not found:
            self.log.warning('Did not find any file')
            return

        # Save results
        for response in found:
            data = self.symfony.profiler.parse_file_preview(response.text)
            self.symfony.files[response.request.params['file']] = data

        self.log.warning('Found the following files:')
        for file in files:
            self.log.warning('  %s', file)
