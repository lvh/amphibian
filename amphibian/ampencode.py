"""
Encodes simple Python data structures into their AMP wire formats.
"""
from twisted.protocols import amp


def toBoxKwargs(inputKwargs):
    """
    Encodes kwargs for an AMP remote call as box arguments, assuming the
    kwargs are all of the correct type.
    """
    boxKwargs = {}
    for key, value in inputKwargs.iteritems():
        boxKwargs[key] = _ampEncoders[value.__class__](value)

    return boxKwargs


_ampEncoders = {
    int: amp.Integer().toString,
    float: amp.Float().toString,
    unicode: amp.Unicode().toString,
    list: lambda l: amp.ListOf(_ampEncoders[l[0].__class__].im_self).toString(l)
}
