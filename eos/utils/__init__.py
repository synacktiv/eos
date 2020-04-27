"""
EOS utilities.

Contains:
* Colorizers
* Lazy encoders (e.g: base64 on strings)
* Enhanced ArgumentParser with builtin defaults and colors
* Lazy version handlers
"""

from .colors import Colors
from .encoders import b64encode, b64decode
from .cli import ArgumentParser, combo
from .version import Version


def ucfirst(string):
    """Clone of PHP ucfirst function, uppercase first character of string."""
    return string[0].upper() + string[1:]
