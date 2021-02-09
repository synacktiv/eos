"""
EOS Scanner module.

Contains the scanning engine: the EOS class.
EOS handles the whole scanning process, from checks to plugins and engine management and error handling.
"""

from os import makedirs
from pathlib import Path
from datetime import datetime

from requests import Session

from eos.plugins import PluginManager
from eos.core import Base, Symfony, EOSException, Engine


class EOS(Base):
    """
    EOS Scanner.

    Orchestrate scans against a target.
    Loads plugins and manages workers.
    """

    wordlists = str(Path(__file__).parent.parent / 'wordlist.txt')

    def __init__(self, url, output, session=None):
        """
        Initialization.

        :param url: target URL
        :param session: requests session
        """

        self.url = url.rstrip('/')
        self.session = session or Session()
        self.symfony = Symfony(self.url, session=session)
        self.output = Path(output).absolute() if output else None

    @property
    def requests(self):
        """List of previously issued requests."""
        return self.symfony.requests

    def run(self, wordlists=None, threads=10):
        """
        Run scan.

        1. Start engine
        2. Load plugins and run them
        3. Output tokens generated from issued requests

        Scans can be performed in aggressive mode where aggressive plugins will be run.
        The engine can be configured using a different wordlists and a specific number of threads.

        :param wordlists: wordlists file or directory
        :param threads: number of workers to run simultaneously
        """

        self.log.info('Starting scan on %s', self.url)
        start = datetime.now()
        self.log.info('%s is a great day', start)
        wordlists = wordlists or self.wordlists

        # Start engine, load and run plugins
        engine = Engine(threads, session=self.session)
        engine.start()
        try:
            options = dict(wordlists=wordlists, output=self.output)
            manager = PluginManager(symfony=self.symfony, engine=engine, **options)
            manager.run()
        finally:
            engine.stop()

        if self.symfony.files and self.output:
            print()
            self.log.info('Saving files to %s', self.output)
            for path, data in self.symfony.files.items():
                self.write(self.output, path, data)
            self.log.info('Saved %d files', len(self.symfony.files))

        print()
        self.log.info('Generated tokens: %s', ' '.join(r.token for r in self.requests if r.token))
        duration = str(datetime.now() - start).split('.')[0]
        self.log.info('Scan completed in %s', duration)

    def check(self):
        """
        Check target.

        Ensure the target is reachable and in debug mode by issuing a GET request to it.
        Debug mode state is determined from the presence of the ``X-Debug-Token`` header in the response.

        :raise: ``EOSException`` if target is not in debug mode
        """

        self.log.info('Checks')

        self.symfony.get()
        if not self.requests[-1].token:
            raise EOSException('Target is not in debug mode!')

        self.log.warning('Target found in debug mode')

    @classmethod
    def write(self, output, path, data):
        """Write data to path relative to output directory."""

        # Format path
        if not isinstance(path, Path):
            path = Path(path)
        path = ('/' / path).resolve()
        path = Path(output) / str(path).lstrip('/')

        # Save
        makedirs(path.parent, mode=0o750, exist_ok=True)
        with open(path, 'wb') as file:
            if not isinstance(data, bytes):
                data = data.encode()
            file.write(data)

    @classmethod
    def save(cls, symfony, output):
        """Save Symfony files to output directory."""

        if symfony.files and output:
            cls.log.info('Saving files to %s', output)
            for path, data in symfony.files.items():
                cls.write(output, path, data)
            cls.log.info('Saved %d files', len(symfony.files))
