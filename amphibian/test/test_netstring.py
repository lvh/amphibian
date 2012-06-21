import mock

from twisted.internet import defer
from twisted.trial import unittest

from amphibian import netstring


class NetstringReceiverTests(unittest.TestCase):
    def test_connectionMade(self):
        """
        Tests that when the connection is made, the receiver instructs the
        transport to stop reading and writing, attempts to create an AMP
        client, and that reading and writing is resumed when that connection
        is made.
        """
        receiver = netstring.NetstringReceiver()

        d = defer.Deferred()
        receiver.factory = mock.Mock()
        receiver.factory.ampClientFactory.return_value = d
        receiver.transport = mock.Mock()

        receiver.connectionMade()
        self.assertTrue(receiver.transport.stopReading.called)
        self.assertTrue(receiver.transport.stopWriting.called)

        d.callback(None)
        self.assertTrue(receiver.transport.startReading.called)
        self.assertTrue(receiver.transport.startWriting.called)


    def test_stringReceived(self):
        """
        Tests that stringReceived delegates to the JSON-RPC code (so we don't
        need to test it here).
        """
        receiver = netstring.NetstringReceiver()
        receiver._client, receiver.sendString = object(), object()
        receiver._handleRequest = mock.Mock()

        receiver.stringReceived("xyz")

        string, client, write = receiver._handleRequest.call_args[0]
        self.assertEqual(string, "xyz")
        self.assertIdentical(client, receiver._client)
        self.assertIdentical(write, receiver.sendString)
