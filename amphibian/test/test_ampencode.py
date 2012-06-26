"""
Tests for encoding AMP boxes to their wire formats.
"""
import string

from twisted.protocols import amp
from twisted.trial import unittest

from amphibian import ampencode


class AMPEncodeTests(unittest.TestCase):
    def _test_encode(self, valuesWithEncoders):
        values, encoders = zip(*valuesWithEncoders)
        inKwargs = dict(zip(string.ascii_lowercase, values))
        boxKwargs = ampencode.toBoxKwargs(inKwargs)
        self.assertEqual(len(inKwargs), len(boxKwargs))

        for key, encoder in zip(string.ascii_lowercase, encoders):
            self.assertEqual(boxKwargs[key], encoder.toString(inKwargs[key]))


    def test_integer(self):
        self._test_encode([(1, amp.Integer())])


    def test_float(self):
        self._test_encode([(1.5, amp.Float())])


    def test_unicode(self):
        self._test_encode([(u"xyzzy", amp.Unicode())])


    def test_listOfIntegers(self):
        ints = [1, 2, 3, 4]
        self._test_encode([(ints, amp.ListOf(amp.Integer()))])


    def test_listOfUnicode(self):
        ts = list(u"abcdef")
        self._test_encode([(ts, amp.ListOf(amp.Unicode()))])


