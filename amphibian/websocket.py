"""
Netstring-encoded JSON-RPC over WebSockets support.
"""
import txws

from amphibian import netstring


def makeFactory(clientFactory):
    """
    Builds a factory for netstring-encoded JSON-RPC over WebSockets.
    """
    netstringFactory = netstring.NetstringFactory(clientFactory)
    return txws.WebsocketFactory(netstringFactory)
