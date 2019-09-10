from concurrent.futures import ThreadPoolExecutor, Executor
import time
from typing import Iterator, Optional, Any
from functools import partial


class RejectionFuture:
    """A simple object to emulate the Future 'result' access
    method for rejected items."""

    def __init__(self, val):
        self.val = val

    def result(self):
        return self.val


BOUNCE = object()


def batch_apply(
    items: Iterator,
    *,
    fnct: callable = None,
    quota: Optional[int] = None,
    interval: int = None,
    preparekey: Optional[callable] = None,
    rejectkey: Optional[callable] = None,
    rejectdefault: Optional[Any] = None,
    through: dict = {},
    executor: Executor = ThreadPoolExecutor()
) -> Iterator:
    """
    Applies a function to a large set of items using threading.

    :items
    The collection of items to process.

    :fnct
    The function to apply to each item. This function should only take one
    parameter: ONE item.

    :rejectkey
    This function is a filter which allows you to define which items should not be
    processed, in which case they will be replaced by the 'rejectdefault' argument.
    Should return 'True' is the item is to be rejected, 'False' otherwise.

    :rejectdefault
    The value to be returned instead of the process result for an item that has been
    rejected. The special value 'BOUNCE' allows you to return the same item instead
    of a default value.

    :quota
    Only a set amount of items can be processed in a set interval of time. Once this
    quota is spent the results already available are yielded back. Once they are
    exhausted, the next batch of items is processed, but not until the time interval
    has been completed.

    :interval
    The time interval described above (in seconds).

    :executor
    You can edit the concurrent executor if you so wish (e.g. to increase max_workers)

    """

    fnct = partial(fnct, **through)

    if (
        quota is not None and interval is None or
        interval is None and quota is not None
    ):
        raise UserWarning("When using quotas, 'quota' and 'interval' need to be both provided.")

    milestone = time.time()
    futures = []

    for idx, item in enumerate(items):

        if preparekey is not None:
            item = preparekey(item)

        if rejectkey is not None and rejectkey(item):
            if rejectdefault is not BOUNCE:
                item = rejectdefault
            futures.append(RejectionFuture(item))
            continue

        futures.append(
            executor.submit(fnct, item)
        )

        if quota is not None and not (idx + 1) % quota:

            for future in futures:
                yield future.result()
            futures = []

            remaining_time = interval - (time.time() - milestone)
            remaining_time = max(remaining_time, 0)

            if remaining_time:
                time.sleep(remaining_time)

            milestone = time.time()

    for future in futures:
        yield future.result()


def batchize(
    # TODO: Rather than break code consistency, maybe add the batch
    # version of the function as a field of the function object, like so:
    # batchize(f) => f(i), f.batch([i])
    fx: callable = None,
    through: dict = {},
    **kw
) -> callable:

    def decorator(f: callable) -> callable:
        
        f.batch = partial(
            batch_apply,
            fnct=f,
            through=through,
            **kw
        )

        return f

    if fx is None:
        return decorator

    return decorator(fx)


if __name__ == "__main__":
    
    @batchize
    def f(a: str, prefix=3):
        print(f'{prefix}[%s]' % a, end=';')

    f(1, prefix=2)
    *f.batch('alveola', prefix=3),
    print()

    import inspect
    print(inspect.getfullargspec(f))
    print('--')
    print(inspect.getfullargspec(f.batch))
