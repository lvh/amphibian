import txws

from twisted.internet import protocol
from twisted.protocols import basic
from twisted.python import failure

from amphibian import jsonrpc


class NetstringReceiver(basic.NetstringReceiver):
    """
    A JSON-RPC netstring receiver that proxies calls using an AMP client.
    """
    def connectionMade(self):
        """
        Pauses the transports and makes a connection to the AMP server.
        """
        self.transport.stopReading()
        self.transport.stopWriting()

        d = self.factory.ampClientFactory()
        d.addCallback(self._ampConnectionStarted)


    def _ampConnectionStarted(self, client):
        """
        Keeps a reference to the AMP client and restarts the transports.
        """
        self._client = client

        self.transport.startReading()
        self.transport.startWriting()


    def stringReceived(self, string):
        """
        Handles an incoming JSON-RPC call.
        """
        return self._handleRequest(string, self._client, self.sendString)


    _handleRequest = staticmethod(jsonrpc.handleRequest)



class NetstringFactory(protocol.Factory):
    """
    A factory for JSON-RPC netstring receiving AMP proxies.
    """
    protocol = NetstringReceiver

    def __init__(self, ampClientFactory):
        self.ampClientFactory = ampClientFactory
