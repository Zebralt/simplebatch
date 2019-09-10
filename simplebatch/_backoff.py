

# Not the 'true' exponential backoff, I gather.
def exponential_backoff(start=0, add=1, factor=1.5, max=30):

    value = abs(start)
    add = abs(add)
    factor = abs(factor)
    max = abs(max)

    while value < max:
        yield value

        if value < 1:
            value += add
        else:
            value = value * factor

    while 1:
        yield max
