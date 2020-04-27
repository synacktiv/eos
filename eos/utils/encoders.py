"""
Encoding helpers.

Base64 wrappers to allow direct string encoding.
"""

from base64 import b64encode as b64encode_bytes, b64decode as b64decode_bytes


def b64encode(data):
    """Simple wrapper to allow non-bytes objects."""
    if not isinstance(data, bytes):
        data = data.encode()
    return b64encode_bytes(data).decode()


def b64decode(data):
    """Simple wrapper to allow non-bytes objects."""
    if not isinstance(data, bytes):
        data = data.encode()
    return b64decode_bytes(data).decode()
