import json

import pygments
import pygments.lexers
import pygments.formatters


CLICK_CONTEXT_SETTINGS = {
    'max_content_width': 100,
    'help_option_names': ['--help'],
}


def printable_dumpling(contents, colorize=True):
    """
    Converts dumpling contents to a pretty-printed and optionally colorized
    output string.

    :param contents: Dumpling contents to generate printable string from.
    :param colorize: Whether to colorize the dumpling string.
    :return: Pretty-printed string representing the dumpling contents.
    """
    contents_printable = json.dumps(
        contents,
        sort_keys=True,
        indent=4,
        separators=(',', ': ')
    )

    if colorize:
        contents_printable = pygments.highlight(
            contents_printable,
            pygments.lexers.JsonLexer(),
            pygments.formatters.TerminalFormatter(),
        ).rstrip()

    return contents_printable
