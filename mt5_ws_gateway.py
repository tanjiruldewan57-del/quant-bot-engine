"""
================================================================================
⚡ ASYNC WEBSOCKET GATEWAY (MT5 PYTHON HYBRID SERVER)
================================================================================
File: mt5_ws_gateway.py
Purpose:
- Bridges asynchronous Python quant engine with MetaTrader 5 Expert Advisor
- Secures connection with authentication token and low latency WebSockets
================================================================================
"""

import asyncio
import websockets
import json
import logging
from daps_calculator import calculate_daps_position_size

logging.basicConfig(level=logging.INFO)

class MT5WebSocketGateway:
    def __init__(self, host="0.0.0.0", port=8765, secret_token="MUDARABAH_SECURE_TOKEN_2026"):
        self.host = host
        self.port = port
        self.token = secret_token
        self.connected_terminals = set()
        self.high_water_mark = 100000.0

    async def register(self, websocket):
        try:
            auth_data = json.loads(await websocket.recv())
            if auth_data.get("token") == self.token:
                self.connected_terminals.add(websocket)
                await websocket.send(json.dumps({"status": "CONNECTED", "message": "Handshake validated."}))
            else:
                await websocket.close(code=4001, reason="Invalid Credentials")
        except:
            await websocket.close()

    async def unregister(self, websocket):
        if websocket in self.connected_terminals:
            self.connected_terminals.remove(websocket)

    async def handle_tick_stream(self, websocket, path=None):
        await self.register(websocket)
        try:
            async for message in websocket:
                data = json.loads(message)
                if data.get("type") == "TICK":
                    sym, bid, ask, bal = data["symbol"], data["bid"], data["ask"], data["balance"]
                    sizing = calculate_daps_position_size(bal, self.high_water_mark, 0.03)
                    if bal > self.high_water_mark:
                        self.high_water_mark = bal
                    
                    if sizing["status"] == "EXECUTION_ALLOWED" and bid < 50000.0:
                        await websocket.send(json.dumps({
                            "action": "BUY_LIMIT",
                            "symbol": sym,
                            "price": bid,
                            "position_size_usd": sizing["optimal_position_size_usd"],
                            "stop_loss": round(bid * 0.99, 2),
                            "take_profit": round(bid * 1.025, 2)
                        }))
        except websockets.ConnectionClosedError:
            pass
        finally:
            await self.unregister(websocket)

    def start(self):
        print(f"🚀 [MT5 WS GATEWAY] Listening on ws://{self.host}:{self.port}...")
        server = websockets.serve(self.handle_tick_stream, self.host, self.port)
        asyncio.get_event_loop().run_until_complete(server)
        asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    gateway = MT5WebSocketGateway()
    gateway.start()
