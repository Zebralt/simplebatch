from functools import wraps


def ctxwrap(*, obj=None, make=None):

    if (
        obj is None and make is None or
        obj is not None and make is not None
    ):
        raise UserWarning('You can only provide one parameter between obj and make, not both or neither.')

    if make is None:
        make = lambda:obj

    def deco(fn):
        @wraps(fn)
        def wrapper(*a, **kw):
            with make():
                return fn(*a, **kw)
        return wrapper
    return deco
