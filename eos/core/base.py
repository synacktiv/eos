"""
EOS base classes.

Contains the very base class of the EOS package and the base Exception class.
Base provides generic helpers and holds the default logger.
"""

from bs4 import BeautifulSoup

from eos.utils.log import LOGGER


class EOSException(Exception):
    """Base EOS Exception."""


class Base:
    """
    EOS base class.

    Implements the default properties and methods of EOS classes.
    Holds the default logger.
    """

    log = LOGGER
    """Logger to use for output."""

    @staticmethod
    def parse(html):
        """
        HTML parser.

        Parse the given HTML and return a Soup instance.

        :param html: HTML string
        """

        return BeautifulSoup(html, 'html.parser')
