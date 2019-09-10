from functools import wraps
from typing import Union
import time
from _userprompt import yesno


def pricewarning(
    key: callable,
    pricekey: callable,
    targetn: Union[int, str] = 0,
    currency: str = '$'
) -> callable:

    """
    A decorator which adds a prompt before executing the decorated function.
    It produces an estimate of the cost incured by the function call, then ask
    the user to confirm the operation before resuming. If the user refuses, an
    exception is raised.

    :key
    A function taking the target field(s) and producing the total quantity to
    put against a price quota.

    For example, with the Google Cloud Translate API, the price is by the character,
    so we need to compute the sum of the length of each string found in the list
    we want to translate.

    :pricekey
    A function that takes the total previously computed and generates a price
    estimate.

    e.g. `total_length * 20 / 1000000` > 20$ per 1M characters

    :targetn
    The argument to target. If it's an integer, it will be assumed to search for
    a positional argument; if it's a string, for a keyword argument.

    :currency
    The currency to show on screen. $, €, £, dollars, etc.

    """

    def decorator(fn: callable) -> callable:

        @wraps(fn)
        def wrapper(*args, **kwargs):

            args = list(args)

            if type(targetn) == str:
                target = kwargs[targetn]
            else:
                target = args[targetn]

            # Converts potential generator to list and hand it back to wrapped function args
            try:
                target = [*target]

                if type(targetn) == str:
                    kwargs[targetn] = target
                else:
                    args[targetn] = target

            except TypeError as te:
                print('Not a list or generator.', te)

            # Compute total
            if type(target) in (list, tuple):
                count = len(target)
                total = sum(map(key, target))
            else:
                count = 1
                total = key(target)

            # Compute price from total
            price = pricekey(total)

            msg = (
                "This operation will incure the \nfollowing \ncost: " +
                "[ \033[93m%s %s\033[m ] (n=%s, total=%s). " % (
                    '%.5f' % price,
                    currency,
                    count,
                    total,
                ) +
                "Proceed?"
            )

            if yesno(msg, options='yN', required=True):
                return fn(*args, **kwargs)

            else:
                raise UserWarning('Process aborted by user.')

        return wrapper

    return decorator


@pricewarning(key=len, pricekey=lambda _: _ * 20 / 1000000)
def f(items):
    for item in items:
        print(repr(item), end='\r')
        time.sleep(.01)
    print(34)


if __name__ == "__main__":
    f(map(str, range(22881)))
