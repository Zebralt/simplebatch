import sys
from typing import Union, List


"""
A few tools to put user prompts in your program.
"""


ARG_YES_MAN = False


def build_prompt_message(msg: str, options: Union[str, List[str]], required: bool = False) -> str:
    t = "\033[94m[?]\033[m " + msg + ' (%s) ' % '/'.join(options)
    if required:
        m = ':required:'
        t += '\033[90m%s\033[m\033[%dD' % (m, len(m))
    return t


def display_answer(char: str, color: Union[int, str], n: int = 1):
    """Updates prompt message to highlight chosen answer as a reminder."""
    print(
        '\033[A' * n + 
        '\033[1;%sm[' % color + char + ']\033[m' + 
        '\033[B' * n +
        '\033[G', 
        end=''
    )
    sys.stdout.flush()


def prompt(msg: str, options: Union[str, List[str]], required: bool = False) -> str:
    """
    Pause the program and asks the user a question.
    Options are meant to be single characters. The default option must be uppercase.
    If more than one option is uppercase, the first one found will be picked.

    :msg
    The question to ask.

    :options
    The possible answers: "yN" => (y/N). They must be single characters.
    The first uppercase option will be chosen as the default option.

    :required
    If this is True, the user must input one the available options. There is no
    default option.
    """

    prompt_msg = build_prompt_message(msg, options, required)
    default_answer = None

    if not required:
        default_answer = max(options, key=lambda x: x == x.upper())

    while True:

        ans = input(prompt_msg).strip()

        if not ans:
            if default_answer is not None:
                return default_answer
            print('\033[A\033[G', end='')
            continue

        if ans not in options:
            print('Please enter one the following options: %s' % ', '.join(options))
            continue

        return ans


def yesno(msg: str, options: Union[str, List[str]] = 'Yn', required: bool = False) -> bool:
    """
    Asks a yes/no question to the user. Return True if answer is 'yes'.
    """

    if options.lower() != 'yn':
        raise UserWarning("yesno.options can only be yn, Yn or yN")

    # No default option if answer is explicitly required
    if required:
        options = options.lower()

    # Prompt user for answer
    if ARG_YES_MAN and '-y' in sys.argv:
        ans = 'y'
        print(build_prompt_message(msg, options))
    else:
        ans = prompt(msg, options=options, required=required).lower()

    # Print answer on screen
    if ans == 'y':
        display_answer('\u2713', 92, n=msg.count('\n') + 1)
    else:
        display_answer('x', 91, n=msg.count('\n') + 1)

    return ans == 'y'
