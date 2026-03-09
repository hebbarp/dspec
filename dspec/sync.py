"""WebSocket sync server for collaborative CRC card editing.

Run on any machine in the network. All CRC boards connecting
to the same sync server see each other's changes in real-time.
"""

import asyncio
import json


CLIENTS = set()


async def handler(websocket):
    CLIENTS.add(websocket)
    peer_id = None
    try:
        async for raw in websocket:
            msg = json.loads(raw)
            peer_id = msg.get("peer", peer_id)

            # Broadcast to all other clients
            for client in CLIENTS:
                if client != websocket:
                    try:
                        await client.send(raw)
                    except Exception:
                        pass
    finally:
        CLIENTS.discard(websocket)
        if peer_id:
            leave = json.dumps({"type": "leave", "peer": peer_id})
            for client in CLIENTS:
                try:
                    await client.send(leave)
                except Exception:
                    pass


async def run_server(host="0.0.0.0", port=8090):
    try:
        import websockets
    except ImportError:
        print("ERROR: Install websockets to use sync:")
        print("  pip install websockets")
        return

    async with websockets.serve(handler, host, port):
        print(f"Sync server running on ws://{host}:{port}")
        print(f"Connect CRC boards with: dspec crc --sync ws://<this-ip>:{port}")
        print(f"Peers on the network can join the same board.")
        print("Press Ctrl+C to stop\n")
        await asyncio.Future()  # run forever
