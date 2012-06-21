import json
import mock

from twisted.internet import defer
from twisted.trial import unittest

from amphibian import jsonrpc


class _JSONRPCAssertions(unittest.TestCase):
    """
    JSON-RPC well-formedness assertion.
    """
    def assertWellFormed(self, response):
        """
        Asserts that the given response is well-formed.
        """
        self.assertEquals(response["jsonrpc"], "2.0")

        if "result" in response:
            self.assertNotIn("error", response)
        else:
            self.assertNotIn("result", response)
            for key in ["code", "message"]:
                self.assertIn(key, response["error"])



class ResponseEncodingTests(_JSONRPCAssertions):
    """
    Tests the response encoding.
    """
    def test_result(self):
        response = json.loads(jsonrpc.encode("result"))
        self.assertWellFormed(response)


    def test_resultWithIdentifier(self):
        response = json.loads(jsonrpc.encode("result", identifier=1))
        self.assertWellFormed(response)
        self.assertEqual(response["id"], 1)



VERSION = "jsonrpc", "2.0"
METHOD = "method", "Transmogrify"
PARAMS = "params", [{}]
IDENTIFIER = "id", 1


class RequestHandlingTests(_JSONRPCAssertions):
    def setUp(self):
        self.write = mock.Mock()
        self.client = mock.Mock()
    
        def fakeCallRemoteString(method, requiresAnswer=True, **kwargs):
            if requiresAnswer:
                return defer.succeed({"transmogrified": True})
            else:
                return None
            
        self.client.callRemoteString.side_effect = fakeCallRemoteString


    def handleRequest(self, string):
        """
        Tries to handle a request specified by the given string with the mock
        client and writer.
        """
        response = jsonrpc.handleRequest(string, self.client, self.write)

        if response is not None:
            response.addCallback(json.loads)

        return response


    def assertClientCalled(self, _result):
        """
        Asserts that the mock client was called and asked to invoke the
        'Transmogrify' command with no arguments.
        """
        self.assertTrue(self.client.called)
        args, kwargs = self.client.call_args
        self.assertEqual(args, ("Transmogrify",))
        self.assertEqual(kwargs, {})


    def assertClientNotCalled(self, _result):
        """
        Asserts that the mock client wasn't called.
        """
        self.assertFalse(self.client.called)


    def assertErrorWritten(self, _result, E):
        """
        Asserts that the given exception class was successfully reported to
        the peer as a JSON-RPC error message.
        """
        self.assertTrue(self.write.called)
        
        written, = self.write.call_args[0]
        response = json.loads(response)
        self.assertWellFormed(response)
        self.assertEqual(response["code"], E.code)
        self.assertEqual(response["message"], E.message)


    def assertNotWritten(self, _result=None):
        """
        Assert that no write attempt was made.
        """
        self.assertFalse(self.write.called)


    def test_callWithMissingVersion(self):
        """
        Attempts to make a method call without specifying the JSON-RPC
        version.
        """
        request = dict([METHOD, PARAMS, IDENTIFIER])
        d = self.handleRequest(json.dumps(request))

        E = jsonrpc.InvalidRequestError
        self.assertFailure(d, E)
        d.addCallback(self.assertClientNotCalled)

        return d


    def test_notificationWithMissingVersion(self):
        """
        Attempts to send a notification without sending the JSON-RPC version.
        """
        request = dict([METHOD, PARAMS])
        d = self.handleRequest(json.dumps(request))

        self.assertFailure(d, jsonrpc.InvalidRequestError)
        d.addCallback(self.assertClientNotCalled)

        return d


    def test_notification(self):
        """
        Tests that a notification doesn't incur a write.
        """
        request = dict([METHOD, PARAMS, VERSION])
        self.handleRequest(json.dumps(request))
        self.assertNotWritten()


    def test_badNotification(self):
        """
        Tests that a bad notification doesn't result in an error being written
        back.
        """
        request = dict([METHOD, PARAMS])
        d = self.handleRequest(json.dumps(request))
        self.assertFailure(d, jsonrpc.InvalidRequestError)
        d.addCallback(self.assertNotWritten)


    def test_notJSON(self):
        """
        Tests what happens when receiving a string that isn't JSON.
        """
        d = self.handleRequest("{")

        E = jsonrpc.ParseError
        self.assertFailure(d, E)

        return d



class ParseRequestTests(unittest.TestCase):
    """
    Tests for parsing incoming JSON-RPC requests.
    """
    def test_valid(self):
        """
        Tests that valid JSON is parsed correctly.
        """
        self.assertEqual(jsonrpc._parseRequest("{}"), {})


    def test_invalid(self):
        """
        Tests that invalid JSON raises ``ParseError``.
        """
        self.assertRaises(jsonrpc.ParseError, jsonrpc._parseRequest, "{")



class ExtractDetailsTests(unittest.TestCase):
    """
    Tests for extracting details from a request.
    """
    def test_methodCall(self):
        """
        Tests details extraction for a method call.
        """
        request = dict([METHOD, PARAMS, VERSION, IDENTIFIER])
        method, identifier, kwargs = jsonrpc._extractDetails(request)
        self.assertEqual(method, METHOD[1])
        self.assertEqual(identifier, IDENTIFIER[1])
        self.assertEqual(kwargs, PARAMS[1][0])


    def test_notification(self):
        """
        Tests details extraction for a notification request (one that is
        missing an identifier).
        """
        request = dict([METHOD, PARAMS, VERSION])
        method, identifier, kwargs = jsonrpc._extractDetails(request)
        self.assertEqual(method, METHOD[1])
        self.assertEqual(identifier, None)
        self.assertEqual(kwargs, PARAMS[1][0])


    def test_callWithMissingMethod(self):
        """
        Tests details extraction for a method call request when the method is
        missing.
        """
        request = dict([PARAMS, VERSION, IDENTIFIER])
        E = jsonrpc.InvalidRequestError
        self.assertRaises(E, jsonrpc._extractDetails, request)


    def test_notificationWithMissingMethod(self):
        """
        Tests details extraction for a notification request when the method is
        missing.
        """
        request = dict([PARAMS, VERSION])
        E = jsonrpc.InvalidRequestError
        self.assertRaises(E, jsonrpc._extractDetails, request)


    def test_missingKwargs(self):
        """
        Tests details extraction when the kwargs are missing.
        """
        request = dict([METHOD, VERSION, IDENTIFIER], params=[])
        E = jsonrpc.BadParametersError
        self.assertRaises(E, jsonrpc._extractDetails, request)


    def test_multipleParams(self):
        """
        Tests details extraction when multiple params are specified.
        """
        request = dict([METHOD, VERSION, IDENTIFIER], params=[{}, {}])
        E = jsonrpc.BadParametersError
        self.assertRaises(E, jsonrpc._extractDetails, request)
