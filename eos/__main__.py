#!/usr/bin/env python3

"""EOS Command Line Interface."""

import sys
from os import makedirs
from pathlib import Path
from base64 import b64decode

from requests import Session
from requests.packages.urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

from eos import __version__
from eos.core import EOS, Symfony, Engine, RememberMe
from eos.utils import log, ArgumentParser, combo
from eos.plugins.info import Plugin as Info
from eos.plugins.logs import Plugin as Logs
from eos.plugins.sources import Plugin as Sources

scan_examples = [
    'eos scan http://localhost',
    "eos scan -H 'Cookie: foo=bar; john=doe' -H 'User-Agent: EOS' http://localhost",
]

get_examples = [
    'eos get http://localhost config/services.yaml',
]

cookies_examples = [(
    "eos cookies -u jane_admin -H '$2y$13$IMalnQpo7xfZD5FJGbEadOcqyj2mi/NQbQiI8v2wBXfjZ4nwshJlG' "
    "-s 67d829bf61dc5f87a73fd814e2c9f629"
)]

all_examples = [*scan_examples, *get_examples, *cookies_examples]


class CLI:
    """EOS Command Line handlers."""

    log = log.LOGGER

    @classmethod
    def scan(cls, args):
        """Scan handler."""
        eos = EOS(url=args.url, output=args.output, session=args.session)
        eos.run(threads=args.threads)

    @classmethod
    def sources(cls, args):
        """Sources handler."""

        # Prep
        symfony = Symfony(url=args.url, session=args.session)
        engine = Engine(size=args.threads, session=args.session)
        engine.start()

        # Run
        cls.log.info(Info.name)
        Info(symfony).run()
        print()
        cls.log.info(Sources.name)
        Sources(symfony, engine).run()

        # Save
        engine.stop()
        if args.output:
            print()
            EOS.save(symfony, args.output)

    @classmethod
    def get(cls, args):
        """Download handler."""
        symfony = Symfony(url=args.url, session=args.session)
        data = symfony.profiler.open(args.path)
        if data is None:
            cls.log.error('Not found')
            return
        print(data)

    @classmethod
    def credentials(cls, args):
        """Credentials handler."""

        # Prep
        symfony = Symfony(url=args.url, session=args.session)
        engine = Engine(size=args.threads, session=args.session)
        engine.start()

        # Run
        cls.log.info(Logs.name)
        Logs(symfony, engine).run()

        # Save
        engine.stop()
        if args.output:
            print()
            EOS.save(symfony, args.output)

    @classmethod
    def cookies(cls, args):
        """Cookies handler."""

        # Run
        r = RememberMe(args.secret, cls=getattr(args, 'class'), delimiter=args.delimiter)
        cookie = r.generate(args.username, args.hash, args.lifetime)

        # Output
        cls.log.debug(b64decode(cookie))
        cls.log.info(cookie)


def main():
    """EOS Command Line Interface."""

    # Parser
    p = ArgumentParser('eos', examples=all_examples, max_help_position=25)
    p.add_argument('-V', '--version', action='version', version=__version__, help='display version info')
    p.add_argument('-v', '--verbose', action='count', help='increase verbosity')
    p.add_argument('--no-colors', action='store_false', help='disable colors in output')

    # Common
    sub = p.add_subparsers(dest='command', required=True)
    common = ArgumentParser(add_help=False)
    common.add_argument('url', help='target URL')
    common.add_argument('-k', '--insecure', action='store_false', help='no SSL certificate verification')
    common.add_argument('-H', '--header', metavar='Header: value', action='append', type=combo, default=[],
                        help='custom HTTP headers')
    common.set_defaults(output=None, timestamps=None)

    output = ArgumentParser(add_help=False)
    output.add_argument('-o', '--output', metavar='dir', help='output directory')

    threads = ArgumentParser(add_help=False)
    threads.add_argument('-t', '--threads', metavar='num', type=int, default=10,
                         help='simultaneous threads (default: 10)')

    # Scan
    scan = sub.add_parser('scan', component='Scanner', help='perform a full scan', examples=scan_examples,
                          parents=[common, output, threads])
    scan.add_argument('--timestamps', action='store_true', help='log with timestamps')
    scan.set_defaults(handler=CLI.scan)

    # Sources
    sources = sub.add_parser('sources', component='Sources', help='download application source code',
                             parents=[common, output, threads])
    sources.set_defaults(handler=CLI.sources)

    # Download
    get = sub.add_parser('get', component='Downloader', help='download a file from the application',
                         examples=get_examples, parents=[common])
    get.add_argument('path', help='path to the file')
    get.set_defaults(handler=CLI.get)

    # Credentials
    creds = sub.add_parser('creds', component='Credentials', help='extract credentials from request logs',
                           parents=[common, threads])
    creds.set_defaults(handler=CLI.credentials)

    # Cookies
    cookies = sub.add_parser('cookies', component='Cookie maker', examples=cookies_examples,
                             help='craft remember me cookies with a great lifetime')
    cookies.set_defaults(header=[])
                          
    cookies.add_argument('-c', '--class', metavar='cls', default=RememberMe.cls,
                         help='user class (default: {})'.format(RememberMe.cls))
    cookies.add_argument('-u', '--username', metavar='user', required=True, help='the user to impersonate')
    cookies.add_argument('-l', '--lifetime', metavar='sec', type=int, default=RememberMe.lifetime,
                         help='cookie lifetime in seconds (default: 1 year)')
    cookies.add_argument('-H', '--hash', metavar='hash', required=True, help="the user's password hash")
    cookies.add_argument('-s', '--secret', metavar='secret', required=True, help="the application's remember_me secret")
    cookies.add_argument('-d', '--delimiter', metavar='char', default=RememberMe.delimiter,
                         help='the cookie delimiter (default: "{}")'.format(RememberMe.delimiter))
    cookies.set_defaults(handler=CLI.cookies, output=None, timestamps=None, headers=[], insecure=None)

    # Parse
    args = p.parse_args()
    logger = log.configure(debug=args.verbose, colors=args.no_colors, time=args.timestamps)
    if args.output:
        output = Path(args.output)
        if not output.exists():
            makedirs(output, mode=0o700, exist_ok=True)
        if list(output.iterdir()):
            logger.critical('Output directory is not empty!')
            sys.exit(1)

    # Requests session
    disable_warnings(category=InsecureRequestWarning)
    session = Session()
    session.headers = {'User-Agent': 'Mozilla/5.0'}
    session.headers.update(dict(args.header))
    session.verify = args.insecure
    args.session = session

    # Run
    try:
        args.handler(args)
    except KeyboardInterrupt:
        logger.critical('Aborted')
        return 1
    except Exception as error:
        logger.critical('%s', error)
        logger.critical('Aborted')
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
