"""
Color helper module.

Provides a Colors class with method colorizing messages.
"""


class Colors:
    """
    Colorizer class.

    Provides ANSI colors escape sequences and helper functions to colorize messages.
    """

    NORMAL = '\033[0m'
    BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = ('\033[1;3%dm' % i for i in range(8))

    @classmethod
    def _color(cls, color, message):
        """Internal generic colorizer."""
        return color + message + cls.NORMAL

    @classmethod
    def black(cls, message):
        """Colorize message with black."""
        return cls._color(cls.BLACK, message)

    @classmethod
    def red(cls, message):
        """Colorize message with red."""
        return cls._color(cls.RED, message)

    @classmethod
    def green(cls, message):
        """Colorize message with green."""
        return cls._color(cls.GREEN, message)

    @classmethod
    def yellow(cls, message):
        """Colorize message with yellow."""
        return cls._color(cls.YELLOW, message)

    @classmethod
    def blue(cls, message):
        """Colorize message with blue."""
        return cls._color(cls.BLUE, message)

    @classmethod
    def magenta(cls, message):
        """Colorize message with magenta."""
        return cls._color(cls.MAGENTA, message)

    @classmethod
    def cyan(cls, message):
        """Colorize message with cyan."""
        return cls._color(cls.CYAN, message)

    @classmethod
    def white(cls, message):
        """Colorize message with white."""
        return cls._color(cls.WHITE, message)
