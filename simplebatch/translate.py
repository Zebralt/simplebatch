from functools import partial, wraps
from string import punctuation as PUNCT
import time
from typing import Any, Optional, Tuple
import os
import threading

import pandas as pd
from google.cloud import translate
from google.auth.exceptions import RefreshError

from simplebatch import batch_apply
from simplebatch._pricewarn import pricewarning
from simplebatch._backoff import exponential_backoff


CLIENT = None
PUNCT = {*PUNCT}


def prepare_celltext(item: str) -> str:
    """
    Prepare a dataframe cell for translation. It's supposed to be text.
    If it is, it's simply stripped of leading and trailing whitespace.
    Otherwise, nothing happens.
    """

    if reject_celltext(item):
        return item

    return item.strip()


def reject_celltext(item: str) -> str:
    """
    A default rejectkey function which denies any element which is None or np.NAN.
    Should return 'True' is the item is to be rejected, 'False' otherwise.
    For a DataFrame cell.
    """
    if (
        item is None or
        type(item) == float and pd.isna(item)
    ):
        return True

    # If contains only punctuation
    if type(item) == str and not {*item} - PUNCT:
        return True

    return False


def retry_caller_partial(
    fn: callable,
    *a,
    dealbreaking: Tuple[Exception] = (
        KeyboardInterrupt,
        RefreshError
    ),
    **kw
) -> callable:
    """
    Create a function partially binding 'fn' with the given arguments which
    upon calling the target function and receiving a exception raised, will
    wait an increasing amount of time before retrying, with a maximum amount
    of retries before giving up.

    :fn
    The function to wrap.
    """

    @wraps(partial(fn, *a, **kw))
    def ptr(item: Any) -> Any:

        expb_iter = exponential_backoff()
        max_retries = 500
        retry_countdown = max_retries

        while True:

            try:
                return fn(item, *a, **kw)

            except dealbreaking as e:
                print('\033[95m[DEALBREAKING]\033[m', type(e), e)
                raise

            except Exception as e:

                # print exception in details
                print('\033[91m[ERROR]\033[m (%s)' % threading.get_ident(), end='; ')
                print(e.__class__.__qualname__ + ': ' + str(e), end='; ')

                # wait
                delay = next(expb_iter)
                print('Retrying after %s seconds.' % delay)
                time.sleep(delay)

                retry_countdown -= 1

                if retry_countdown <= 0:
                    raise Exception('No response after %d retries. Aborting process.' % max_retries)

    return ptr


def batch_translator(
    source: Optional[str] = None,
    target: str = None,
    credentials: Optional[str] = None
) -> callable:

    if credentials:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.fspath(credentials)

    global CLIENT
    if CLIENT is None or credentials:
        CLIENT = translate.Client()

    """
    Creates a partial object over 'batch_apply' and
    'google.cloud.translate.Client.translate' to enable
    batch translation with the specified source and target
    languages.
    """

    if source is None and target is None:
        raise UserWarning('You need to provide at least a target language. (target=)')

    fn = partial(
        batch_apply,
        fnct=retry_caller_partial(CLIENT.translate, source_language=source, target_language=target),
        preparekey=prepare_celltext,
        rejectkey=reject_celltext,
        quota=8000,
        interval=1
    )

    # Add a price warning before executing the function
    fn = pricewarning(
        key=lambda _: type(_) == str and len(_) or 1,
        pricekey=lambda _: _ * 20 / 1000000
    )(fn)

    return fn
