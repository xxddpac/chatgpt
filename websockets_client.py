import asyncio
import websockets
import json


##本地测试用


async def heartbeat(websocket):
    while True:
        if websocket.closed:
            break
        try:
            await websocket.send(json.dumps({'ping': 'pong'}))
        except websockets.ConnectionClosedOK:
            break
        await asyncio.sleep(3)


async def handle_websocket():
    uri = 'ws://127.0.0.1:52712/ws'
    async with websockets.connect(uri) as websocket:
        heartbeat_task = asyncio.create_task(heartbeat(websocket))
        while True:
            try:
                message = input('Websocket: ')  # 客户端发送json消息：{"username":"企业微信用户001","content":"hi"}
                await websocket.send(message)
                response = await websocket.recv()
                print('ChatGPT:', response)
                if message == 'exit' or websocket.closed:
                    break
            except Exception as e:
                print(str(e))

        heartbeat_task.cancel()


asyncio.get_event_loop().run_until_complete(handle_websocket())
