"""
JSON-RPC handling.
"""
import functools
import json

from twisted.internet import defer
from twisted.python import failure, log


class ParseError(Exception):
    code = -32700
    message = "Parse error"



class InvalidRequestError(Exception):
    code = -32600
    message = "Invalid request"



class BadParametersError(Exception):
    code = -32000
    message = "AMP requests need to have a single parameter with kwargs"



def handleRequest(string, client, write):
    """
    Handles an incoming request.
    """
    identifier, requiresAnswer = None, False

    try:
        request = _parseRequest(string)
        method, identifier, kwargs = _extractDetails(request)
        requiresAnswer = identifier is not None
        d = _callRemote(client, method, kwargs, requiresAnswer)
    except Exception as e:
        d = defer.fail(e)

    if requiresAnswer:
        d.addBoth(encode, identifier)
        d.addCallback(write)
    
    return d


def _parseRequest(string):
    """
    Parses a JSON-RPC request.
    """
    try:
        return json.loads(string)
    except ValueError:
        raise ParseError()


def _extractDetails(request):
    """
    Extracts the requested method, keyword arguments for that method, and
    response identifier from a request.
    """
    try:
        if request["jsonrpc"] != "2.0":
            raise InvalidRequestError
        method, identifier = request["method"], request.get("id")
        kwargs, = request["params"]
    except KeyError:
        raise InvalidRequestError()
    except ValueError:
        raise BadParametersError()

    return method, identifier, kwargs


def _callRemote(client, method, kwargs, requiresAnswer):
    """
    Calls the remote method by name.
    """
    try:
        return client.callRemoteString(method, requiresAnswer, **kwargs)
    except TypeError: # **kwargs failed, kwargs not a mapping
        raise BadParametersError()



def encode(result, identifier=None):
    """
    Encodes a JSON-RPC message.

    This includes the JSON-RPC version (2.0), the identifier (if one is
    specified), the result if the result is not a failure, or the error
    information otherwise.
    """
    response = {"jsonrpc": "2.0"}
    
    if identifier is not None:
        response["id"] = identifier
        
    if not isinstance(result, failure.Failure):
        response["result"] = result
    else:
        log.err(result)
        error = {"code": result.value.code, "message": result.value.message}
        response["error"] = error
    
    return json.dumps(response)
