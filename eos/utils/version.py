"""
Versions helper.

Wrapper on distutils.version to allow more laziness.
"""

from distutils.version import LooseVersion


class Version(LooseVersion):
    """
    EOS Version.

    Simple wrapper on distutils.LooseVersion to provide more abstraction on version comparison.
    """

    def _cmp(self, other):
        """
        Comparison override to support extra types.

        If other is not an Version instance (or LooseVersion by inheritance), cast it to string and Version.
        This provides integers support among others.
        The base method is then called.

        :param other: the other object to compare against
        """

        if not isinstance(other, Version):
            other = Version(str(other))

        return super()._cmp(other)
