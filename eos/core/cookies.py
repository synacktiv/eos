"""EOS implementation of Symfony REMEMBERME cookies."""

import hmac
import hashlib
from pathlib import Path
from datetime import datetime

from eos.core import Base
from eos.utils.encoders import b64encode


class RememberMe(Base):
    """EOS RememberMe Cookie Maker."""

    cls = r'App\Entity\User'
    """The default user class."""
    lifetime = 360*24*60*60
    """The default cookie lifetime (1 year)."""
    delimiter = ':'
    """The default delimiter to use."""

    def __init__(self, secret, cls=None, delimiter=None):
        """
        Initialization.

        Provides help on the class syntax by removing extra slashes and converting slashes to backslashes.

        :param secret: the remember me secret, usually the APP_SECRET .env variable
        :param cls: the user class
        :param delimiter: the delimiter used (default to ':')
        """

        self.secret = secret
        self.cls = cls or self.cls
        self.cls = str(Path(self.cls)).replace('/', '\\')
        self.delimiter = delimiter or self.delimiter

    def generate(self, username, hash_, lifetime=None):
        """
        Generate a magic cookie for the given user and for a given duration.

        First handle the lifetime parameter by adding the current timestamp to it.
        Then generate the cookie hash.
        Finally put parts together and base64 encode the result.
        Note: the username is base64 encoded

        :param username: the user to create the cookie for
        :param hash_: the user's password hash
        :param lifetime: the cookie lifetime in seconds (default to 1 year)
        :return: the base64 encode cookie
        """

        # Lifetime
        lifetime = lifetime or self.lifetime
        lifetime = int(lifetime)
        lifetime += int(datetime.now().timestamp())
        lifetime = str(lifetime)

        cookie_hash = self.generate_cookie_hash(username, hash_, lifetime)
        parts = [self.cls, b64encode(username), lifetime, cookie_hash]
        data = self.delimiter.join(parts)
        return b64encode(data)

    def generate_cookie_hash(self, username, hash_, lifetime):
        """
        Generate the cookie hash.

        Symfony uses HMAC-SHA256 to hash its remember me cookies.
        The hash is calculated on the following elements, separated by the delimiter.
            * the user class
            * the username
            * the lifetime
            * the user's password hash

        :param username: the user to create the cookie for
        :param hash_: the user's password hash
        :param lifetime: the cookie lifetime
        :return: the hexdigest of the cookie
        """

        lifetime = lifetime or self.lifetime
        parts = [self.cls, username, lifetime, hash_]
        message = self.delimiter.join(parts)
        return hmac.new(self.secret.encode(), message.encode(), hashlib.sha256).hexdigest()
