#!/usr/bin/env python3
"""WebSocket 示例服务端。用法：pip install websockets && python server.py"""
import asyncio
import json
import math
import time

import websockets


async def handler(ws):
    n = 0
    async for _ in ws:
        pass


async def serve(ws):
    n = 0
    try:
        while True:
            n += 1
            v = 50 + 40 * math.sin(n / 8)
            await ws.send(json.dumps({
                "type": "patch",
                "metrics": [{"id": "ws", "label": "WS 实时值", "value": round(v, 1),
                             "unit": "", "color": "#4488FF"}],
                "cards": [{"id": "conn", "title": "WebSocket 已连接",
                           "body": time.strftime("%H:%M:%S")}],
            }))
            await asyncio.sleep(2)
    except websockets.exceptions.ConnectionClosed:
        pass


async def main():
    async with websockets.serve(serve, "127.0.0.1", 8766):
        print("listening on ws://127.0.0.1:8766")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
