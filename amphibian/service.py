import os

from twisted.application import service
from twisted.internet import endpoints
from twisted.protocols import amp

from amphibian import websocket


class WebSocketService(service.Service):
    """
    Service for proxying netstring-encoded JSON-RPC calls to AMP.
    """
    def __init__(self, listeningEndpoint, ampTargetEndpoint):
        self.listeningEndpoint = listeningEndpoint
        self.ampTargetEndpoint = ampTargetEndpoint


    def startService(self):
        """
        Starts the websocket factory.
        """
        def clientFactory():
            return self.ampEndpoint.connect(amp.AMP)

        factory = websocket.makeFactory(clientFactory)
        return self.listeningEndpoint.listen(factory)


    @classmethod
    def fromEnvironment(cls, _environ=os.environ):
        spec = _environ["AMPHIBIAN_WEBSOCKET_ENDPOINT"]
        listeningEndpoint = endpoints.serverFromString(spec)

        spec = _environ["AMPHIBIAN_AMPTARGET_ENDPOINT"]
        ampTargetEndpoint = endpoints.clientFromString(spec)

        return cls(listeningEndpoint, ampTargetEndpoint)
