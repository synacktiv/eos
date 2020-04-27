"""
EOS CLI Utils.

Provides CLI helpers such as ArgumentParser, a custom ArgumentParser wrapper.
It basically colorizes output, add examples to the epilog and add default arguments such as version and verbosity.
"""

import sys
from argparse import ArgumentParser as _ArgumentParser, RawTextHelpFormatter, ArgumentError

from eos.utils import Colors
from eos import __banner__, __version__


def combo(arg):
    """
    Combo argument type.

    Format: key:value.
    Both parts are stripped before being returned.

    :param arg: argument to parse
    """

    parts = arg.split(':', 1)
    if len(parts) != 2:
        raise ArgumentError
    key, value = parts

    return key.strip(), value.strip()


class HelpFormatter(RawTextHelpFormatter):
    """
    EOS Help Formatter.

    Colorize the help message.
    Handle to extra offsets created by the ANSI chars by increasing the max_help_position.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialization.

        Increase the max_help_position due to the extra ANSI chars added with colorization.

        :param args: wrapped
        :param kwargs: wrapped
        """

        self._ansi_padding = len(Colors.green(''))
        kwargs.setdefault('max_help_position', 24)
        kwargs['max_help_position'] += self._ansi_padding
        super().__init__(*args, **kwargs)

    def _format_action(self, action):
        # determine the required width and the entry label
        help_position = min(self._action_max_length + 2,
                            self._max_help_position)
        help_width = max(self._width - help_position, 11)
        action_width = help_position - self._current_indent - 2
        action_header = self._format_action_invocation(action)

        # no help; start on same line and add a final newline
        if not action.help:
            tup = self._current_indent, '', action_header
            action_header = '%*s%s\n' % tup

        # short action name; start on the same line and pad two spaces
        elif len(action_header) <= action_width:
            tup = self._current_indent, '', action_width, action_header
            action_header = '%*s%-*s  ' % tup
            indent_first = 0

        # long action name; start on the next line
        else:
            tup = self._current_indent, '', action_header
            action_header = '%*s%s\n' % tup
            indent_first = help_position - self._ansi_padding

        # collect the pieces of the action help
        parts = [action_header]

        # if there was help for the action, add lines of help text
        if action.help:
            help_text = self._expand_help(action)
            help_lines = self._split_lines(help_text, help_width)
            parts.append('%*s%s\n' % (indent_first, '', help_lines[0]))
            for line in help_lines[1:]:
                parts.append('%*s%s\n' % (help_position, '', line))

        # or add a newline if the description doesn't end with one
        elif not action_header.endswith('\n'):
            parts.append('\n')

        # if there are any sub-actions, add their help as well
        for subaction in self._iter_indented_subactions(action):
            parts.append(self._format_action(subaction))

        # return a single string
        return self._join_parts(parts)

    def _format_action_invocation(self, action):
        """
        Override default formatting.

        Colorize parameters with green.
        """

        if not action.option_strings:
            default = self._get_default_metavar_for_positional(action)
            metavar, = self._metavar_formatter(action, default)(1)
            return Colors.green(metavar)

        parts = []

        # if the Optional doesn't take a value, format is:
        #    -s, --long
        if action.nargs == 0:
            parts.extend(action.option_strings)

        # if the Optional takes a value, format is:
        #    -s ARGS, --long ARGS
        else:
            default = self._get_default_metavar_for_optional(action)
            args_string = self._format_args(action, default)
            parts.extend(action.option_strings[:-1])
            parts.append('%s %s' % (action.option_strings[-1], args_string))

        return Colors.green(', '.join(parts))

    class _Section(RawTextHelpFormatter._Section):
        """Custom section."""

        def format_help(self):
            """
            Override default formatting.

            Colorize headings with yellow.
            Restore them after the formatting process.
            """

            tmp = self.heading
            if self.heading:
                self.heading = Colors.yellow(tmp)
            output = super().format_help()
            self.heading = tmp
            return output


class ArgumentParser(_ArgumentParser):
    """
    EOS ArgumentParser wrapper.
    """

    def __init__(self, *args, component=None, examples=None, max_help_position=30, **kwargs):
        """
        Initialization.

        Forces the use of an HelpFormatter with a max_help_position.
        Add the component name to the banner.
        Add examples to the epilog.
        Initialize the ArgumentParser.
        Add default arguments: version and verbosity.

        :param args: wrapped
        :param component: the EOS component name
        :param examples: list of examples
        :param max_help_position: wrapped to HelpFormatter
        :param kwargs: wrapped
        """

        kwargs['formatter_class'] = lambda prog: HelpFormatter(prog, max_help_position=max_help_position)
        kwargs['description'] = __banner__ + (Colors.yellow('  {}'.format(component.strip())) if component else '')
        super().__init__(*args, **kwargs)
        if examples:
            self.epilog = Colors.yellow('examples:\n') + '  {}'.format('\n  '.join(examples))

    def error(self, *args, **kwargs):
        """
        Error handler override.

        Print help when no command line parameter is given, instead of an error.
        """

        if len(sys.argv) <= 2:
            self.print_help()
            sys.exit(0)
        super().error(*args, **kwargs)
