import os

from twisted.application import service
from twisted.internet import endpoints
from twisted.protocols import amp

from amphibian import netstring, websocket


class _Service(service.Service):
    prefix = "AMPHIBIAN"
    serviceName, factory = None

    def __init__(self, listeningEndpoint, ampTargetEndpoint):
        self.listeningEndpoint = listeningEndpoint
        self.ampTargetEndpoint = ampTargetEndpoint


    def startService(self):
        """
        Starts the websocket factory.
        """
        def clientFactory():
            return self.ampEndpoint.connect(amp.AMP)

        factory = self.factory(clientFactory)
        return self.listeningEndpoint.listen(factory)


    @classmethod
    def fromEnvironment(cls, _environ=os.environ):
        """
        Constructs appropriate endpoints from the environment.
        """
        spec = _environ["{0.prefix}_{0.serviceName}_ENDPOINT"]
        listeningEndpoint = endpoints.serverFromString(spec)

        spec = _environ["{0.prefix}_AMPTARGET_ENDPOINT"]
        ampTargetEndpoint = endpoints.clientFromString(spec)

        return cls(listeningEndpoint, ampTargetEndpoint)



class WebSocketService(service.Service):
    """
    Service that proxies netstring-encoded JSON-RPC requests over WebSockets
    to AMP.
    """
    serviceName = "WEBSOCKET"
    factory = staticmethod(websocket.makeFactory)



class NetstringService(service.Service):
    """
    Service that proxies netstring-encoded JSON-RPC calls over TCP to AMP.
    """
    serviceName = "NETSTRING"
    factory = netstring.NetstringFactory
    
