import functools
from fastapi import FastAPI, Request, APIRouter, WebSocket, BackgroundTasks
from service import chat_recv_msg, chat_verifychat_verif
from service import chat_gpt_api
from logs import logger

app = FastAPI()

router = APIRouter()


@router.get('/ping')
async def ping_handler():
    return {'msg': 'success', 'code': 200, 'data': 'pong'}


# 企业微信验证请求接口
@router.get('/chat')
async def chat_verify_handler(request: Request):
    return chat_verifychat_verif(request)


# 企业微信消息发送接口
@router.post('/chat')
async def chat_recv_msg_handler(background_tasks: BackgroundTasks, request: Request):
    msg_signature = request.query_params.get('msg_signature')
    timestamp = request.query_params.get('timestamp')
    nonce = request.query_params.get('nonce')
    data = await request.body()
    # 企业微信发送消息5秒未收到回复认为请求失败,将会继续重试3次,使用异步方式避免这种情况发生
    partial_func = functools.partial(chat_recv_msg, msg_signature, timestamp, nonce, data)
    background_tasks.add_task(task, partial_func)
    return ''


async def task(func):
    await func()


@app.websocket('/ws')
async def websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_json()
            pong = message.get('ping', None)
            username = message.get('username', None)
            content = message.get('content', None)
            if pong == 'pong':
                pass
            elif not username or not content:
                await websocket.send_text('username、content不能为空')
            else:
                response = await chat_gpt_api(username, content)
                await websocket.send_text(response)
    except Exception as e:
        logger.error('websocket error:%s' % str(e))


app.include_router(router, prefix='/api/v1')
