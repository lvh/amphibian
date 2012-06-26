"""
Functional end-to-end test for amphibian.
"""
import json

from twisted.internet import defer, endpoints, protocol, reactor
from twisted.protocols import amp, basic
from twisted.trial import unittest

from amphibian import service


class Add(amp.Command):
    arguments = [("a", amp.Integer()), ("b", amp.Integer())]
    response = [("sum", amp.Integer())]



class Multiply(amp.Command):
    arguments = [("a", amp.Integer()), ("b", amp.Integer())]
    response = [("product", amp.Integer())]



class Calculator(amp.AMP):
    @Add.responder
    def add(self, a, b):
        return {"sum": a + b}


    @Multiply.responder
    def multiply(self, a, b):
        return {"product": a * b}



def listenAMP():
    factory = protocol.Factory()
    factory.protocol = Calculator
    endpoint = endpoints.TCP4ServerEndpoint(reactor, 0)
    return endpoint.listen(factory)


def _clientEndpointForPort(listeningPort):
    h = listeningPort.getHost()
    return endpoints.TCP4ClientEndpoint(reactor, h.host, h.port)



class _AMPClientFactory(protocol.Factory):
    protocol = amp.AMP



class CalculatorTests(unittest.TestCase):
    """
    Tests that the calculator works without any fancy translation magic.
    """
    def setUp(self):
        d = listenAMP().addCallback(self._ampListening)
        d.addCallback(self._connect).addCallback(self._clientConnected)
        return d


    def _ampListening(self, port):
        self._ampListeningPort = port


    def _connect(self, _result):
        endpoint = _clientEndpointForPort(self._ampListeningPort)
        return endpoint.connect(_AMPClientFactory())


    def _clientConnected(self, client):
        self.client = client


    def tearDown(self):
        self.client.transport.loseConnection()
        self._ampListeningPort.stopListening()

    
    def test_add(self):
        d = self.client.callRemote(Add, a=2, b=2)

        @d.addCallback
        def checkResult(result):
            self.assertEqual(result["sum"], 4)

        return d


    def test_multiply(self):
        d = self.client.callRemote(Multiply, a=2, b=2)

        @d.addCallback
        def checkResult(result):
            self.assertEqual(result["product"], 4)

        return d



class FunctionalTests(unittest.TestCase):
    def setUp(self):
        """
        Sets up an AMP server, a proxy to it, and a netstring client factory.
        """
        self._listeningPorts = {}

        d = listenAMP().addCallback(self._listening, "amp")
        d.addCallback(self._buildProxy).addCallback(self._listening, "proxy")

        self.netstringClientFactory = f = protocol.Factory()
        f.protocol = basic.NetstringReceiver

        return d


    def _listening(self, listeningPort, key):
        """
        Keeps a reference to the port on which a server is listening.
        """
        self._listeningPorts[key] = listeningPort


    def _buildProxy(self, _result):
        listeningEndpoint = endpoints.TCP4ServerEndpoint(reactor, 0)
        ampEndpoint = _clientEndpointForPort(self._listeningPorts["amp"])
        s = service.NetstringService(listeningEndpoint, ampEndpoint)
        return s.startService()


    def tearDown(self):
        """
        Stops listening on all ports.
        """
        for port in self._listeningPorts.values():
            port.stopListening()


    def sendRequest(self, methodName, requiresAnswer=1, **kwargs):
        request = {"jsonrpc": "2.0", "method": methodName, "params": [kwargs]}

        if requiresAnswer:
            request["id"] = 1

        return self._sendNetstring(json.dumps(request))


    def _sendNetstring(self, string):
        """
        Sends the given netstring.

        Returns a deferred that will fire with the first netstring received.
        """
        responseDeferred = defer.Deferred()

        e = _clientEndpointForPort(self._listeningPorts["proxy"])
        d = e.connect(self.netstringClientFactory)

        @d.addCallback
        def hookUpResponseDeferredAndSendString(client):
            client.stringReceived = responseDeferred.callback
            client.sendString(string)

        return responseDeferred


    def _extractResult(self, responseString):
        response = json.loads(responseString)
        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertNotIn("error", response)
        return response["result"]


    def test_add(self):
        d = self.sendRequest("Add", a=2, b=2).addCallback(self._extractResult)

        @d.addCallback
        def checkResult(result):
            self.assertEqual(result["sum"], 4)

        return d


    def test_multiply(self):
        d = self.sendRequest("Multiply", a=2, b=2)
        d.addCallback(self._extractResult)

        @d.addCallback
        def checkResult(result):
            self.assertEqual(result["product"], 4)

        return d
