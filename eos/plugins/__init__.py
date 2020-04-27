"""
EOS plugin repository.

This module implements the base plugin class and a plugin manager.
The former is an abstract class handling the plugin initialization.
The latter is responsible for plugins detection, loading and running.
Each plugin gets access to the Symfony instance and the scanner engine.

The package contains plugins (one per file) inherited from AbstractPlugin.
Each file is inspected to have at least one class inheriting from it and not being abstract itself.
Buggy plugins logged but ignored.
"""

from sys import exc_info
from pathlib import Path
from pkgutil import iter_modules
from abc import ABC, abstractmethod
from importlib import import_module
from inspect import isclass, isabstract

from eos.core import Base, Symfony, Engine


class AbstractPlugin(Base, ABC):
    """
    Abstract EOS plugin.
    """

    priority = 100
    """Plugin priority. The lower, the better."""
    requirements = '0.0.0'
    """Minimum Symfony version required for the plugin to run."""

    def __init__(self, symfony: Symfony, engine: Engine = None, wordlists=None, **kwargs):
        """
        Initialization.

        Plugins receive a Symfony instance containing all the previously found information.
        It also contains previous requests and responses, allowing the plugin to look for information there
        instead of performing new requests.
        In addition, an engine instance is received to perform scans requiring multiple concurrent requests.
        Additional options can be received (reserved).

        :param symfony: Symfony instance to use the plugin against
        :param engine: workers engine
        :param wordlists: fuzz wordlists to use against the profiler
        :param kwargs: additional kwargs
        """

        self.symfony = symfony or []
        self.engine = engine
        self.wordlists = wordlists
        self.kwargs = kwargs

    @property
    @abstractmethod
    def name(self):
        """Plugin name displayed in logs before its execution."""

    @abstractmethod
    def run(self):
        """Run the plugin."""

    @property
    def requests(self):
        """Previously issued requests."""
        if not self.symfony.requests:
            self.symfony.get()
        return self.symfony.requests

    @property
    def token(self):
        """Token of the first issued request."""
        return self.requests[0].token


class PluginManager(Base):
    """
    EOS Plugin Manager.

    Provides an automatic plugin loader.
    Plugins can then be run sequentially according to their priority.
    """

    package = __name__
    repositories = [Path(__file__).parent]

    def __init__(self, symfony, engine, load=True, **options):
        """
        Initialization.

        :param symfony: Symfony instance to load the plugin for
        :param engine: instance of EOSWorkerManager
        :param load: load plugins on instantiation
        :param options: additional options for plugins
        """

        self.plugins = []
        self.engine = engine
        self.symfony = symfony
        self.options = options or {}
        if load:
            self.load()

    def load(self):
        """
        Plugin loader.

        Load plugins from python modules in eos.plugins.
        A class is considered a plugin if it inherits from AbstractPlugin and is not abstract itself.
        Plugins are instantiated with the symfony instance and additional options before being added to self.plugins.
        Buggy plugins are ignored.
        """

        self.log.debug('Loading plugins')

        for finder, name, is_pkg in iter_modules(path=self.repositories):
            try:
                module = import_module('.' + name, package=__name__)
                plugin = None
                for element in [getattr(module, name) for name in dir(module)]:
                    if isclass(element) and issubclass(element, AbstractPlugin) and not isabstract(element):
                        plugin = element
                if not plugin:
                    self.log.debug('No plugin found in %s.py, skipping', name)
                    continue
                self.plugins.append(plugin(symfony=self.symfony, engine=self.engine, **self.options))
                self.log.debug('Loaded %s', plugin.name)

            except Exception as error:
                self.log.warning('Could not load plugin from %s.py: %s', name, error)

        self.log.debug('Loaded %d plugin(s)', len(self.plugins))

    def run(self):
        """
        Run plugins by priority.

        Run each plugin sequentially by calling its run method.
        Engine is cleared between each call.
        Exceptions are caught, logged and ignored.
        """

        key = lambda plugin: plugin.priority
        for plugin in sorted(self.plugins, key=key):

            # Version check
            if self.symfony.version < plugin.requirements:
                print()
                self.log.info('%s plugin requires Symfony >= %s', plugin.name, plugin.requirements)
                continue

            # Run
            try:
                print()
                self.log.info('%s', plugin.name)
                self.engine.clear()
                plugin.run()

            # Catch and log errors
            except Exception as error:
                self.log.exception('%s', error)
