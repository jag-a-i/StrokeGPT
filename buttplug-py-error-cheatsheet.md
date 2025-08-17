# buttplug-py Error Handling Cheatsheet

This document provides a summary of the error hierarchy in the `buttplug-py` library, with code examples to help you handle exceptions gracefully.

## Error Hierarchy

All exceptions in `buttplug-py` inherit from the base `ButtplugError` class. The hierarchy is divided into two main branches: `ClientError` and `ServerError`.

-   `ButtplugError`
    -   `ClientError`
        -   `ReconnectError`
        -   `ScanNotRunningError`
        -   `UnsupportedCommandError`
        -   `UnexpectedMessageError`
        -   `ConnectorError`
            -   `InvalidAddressError`
            -   `ServerNotFoundError`
            -   `InvalidHandshakeError`
            -   `WebsocketTimeoutError`
            -   `DisconnectedError`
    -   `ServerError`
        -   `UnknownServerError`
        -   `InitServerError`
        -   `PingServerError`
        -   `MessageServerError`
        -   `DeviceServerError`

## Exception Categories

### Client Errors

`ClientError` exceptions are raised by the client when an operation fails due to a client-side issue.

-   **`ReconnectError`**: Raised when a client tries to reconnect without a connector.
-   **`ScanNotRunningError`**: Raised when a stop scan is attempted while no scan is running.
-   **`UnsupportedCommandError`**: Raised when an unsupported command is attempted.
-   **`UnexpectedMessageError`**: Raised when an unexpected message is received.

### Connector Errors

`ConnectorError` exceptions are raised when there is an issue with the connection to the server.

-   **`InvalidAddressError`**: Raised when the provided endpoint is not a valid websocket URI.
-   **`ServerNotFoundError`**: Raised when the provided endpoint returns a refused connection error.
-   **`InvalidHandshakeError`**: Raised when a faulty websocket handshake is received.
-   **`WebsocketTimeoutError`**: Raised when the endpoint does not answer within the accepted deadline.
-   **`DisconnectedError`**: Raised when trying to send a message over a disconnected connector.

### Server Errors

`ServerError` exceptions are raised when the server returns an error message.

-   **`UnknownServerError`**: Raised when an unknown error occurs on the server.
-   **`InitServerError`**: Raised when the handshake with the server does not succeed.
-   **`PingServerError`**: Raised when a ping is not sent in the expected time.
-   **`MessageServerError`**: Raised when a message parsing or permission error occurs.
-   **`DeviceServerError`**: Raised when a command sent to a device returns an error.

## Code Examples

Here are some examples of how to handle specific exceptions in your code.

### Handling Connection Errors

```python
import asyncio
from buttplug import Client, WebsocketConnector
from buttplug.errors import ServerNotFoundError, InvalidAddressError

async def main():
    try:
        connector = WebsocketConnector("ws://localhost:12345")
        client = Client("Test Client", connector)
        await client.connect()
    except ServerNotFoundError as e:
        print(f"Server not found: {e.message}")
    except InvalidAddressError as e:
        print(f"Invalid address: {e.message}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Handling Device Errors

```python
import asyncio
from buttplug import Client, WebsocketConnector
from buttplug.errors import DeviceServerError

async def main():
    try:
        connector = WebsocketConnector("ws://localhost:12345")
        client = Client("Test Client", connector)
        await client.connect()
        await client.start_scanning()
        # ... device interaction logic ...
    except DeviceServerError as e:
        print(f"Device error: {e.message}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())