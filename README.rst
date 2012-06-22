===========
 amphibian
===========

amphibian is `JSON-RPC`_ to AMP_ bridge.

.. _`JSON-RPC`: http://json-rpc.org/
.. _AMP: http://amp-protocol.net/

.. image:: http://project-logos.lvh.cc/amphibian.png
    :align: center

Why?
====

AMP_ is an awesome protocol, but it's inherently binary. While binary support
in browsers is improving (ArrayBuffer_ and Blob_), they're still nowhere near
widely supported and using them for anything other than their immediate use
case (WebGL and the File API, respectively) is incredibly annoying.

.. _ArrayBuffer: https://developer.mozilla.org/en/JavaScript_typed_arrays
.. _Blob: http://www.w3.org/TR/FileAPI/#dfn-Blob

Bottom line: anything you send across the WebSocket wire better be 7-bit safe.

Although base64 seems like the obvious solution, you still lack the tools to
parse and produce those AMP boxes.

At the same time, browsers everywhere speak JSON_, and usually pretty
efficiently, too. JSON has a de facto RPC protocol called `JSON-RPC`_ which is
very similar in many ways to AMP_. Hence, it made sense to attempt to proxy
them.

.. _JSON: http://www.json.org/

How it works
============

amphibian supports `JSON-RPC 2.0`_ encoded as netstrings_ (the standard for
`JSON-RPC 2.0`_ over TCP) over anything you can specify as an endpoint, and,
more importantly, `JSON-RPC 2.0`_ encoded as netstrings_ over WebSockets_.

.. _`JSON-RPC 2.0`: http://www.jsonrpc.org/specification
.. _netstrings: http://cr.yp.to/proto/netstrings.txt
.. _WebSockets: http://www.websocket.org

Differences
===========

The main difference is that JSON-RPC takes positional arguments whereas AMP
generally takes named keyword arguments (with the exception of protocol
switching). To fix this, amphibian requires the JSON-RPC parameters array to
consist of a single JSON object that has the keyword arguments for the AMP
call::

    {
      jsonrpc: "2.0",
      method: "Transmogrify",
      params: [{withFluxCapacitor: true, volume: 11}],
      identifier: 1
    }

This maps to::

    ampClient.callRemote(Transmogrify, withFluxCapacitor=True, volume=11)
