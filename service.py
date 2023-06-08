import json
import openai
import random
import aiohttp
import asyncio
import xml.etree.cElementTree as ET
from cache import dequeue, enqueue, connect_redis
from WXBizMsgCrypt3 import WXBizMsgCrypt
from utils import *
from logs import logger

wxcpt = WXBizMsgCrypt(we_chat_work_token, we_chat_work_encodingAESKey, we_chat_work_corpid)


async def chat_verifychat_verif(request) -> str:
    msg_signature = request.query_params.get('msg_signature')
    timestamp = request.query_params.get('timestamp')
    nonce = request.query_params.get('nonce')
    echostr = request.query_params.get('echostr')
    ret, sReplyEchoStr = wxcpt.VerifyURL(msg_signature, timestamp, nonce, echostr)
    if ret != 0:
        return 'ERR: VerifyURL ret:' + str(ret)
    # noinspection PyTypeChecker
    return int(sReplyEchoStr)


async def chat_recv_msg(msg_signature, timestamp, nonce, data):
    ret, xml_content = wxcpt.DecryptMsg(data, msg_signature, timestamp, nonce)
    if ret != 0:
        return 'ERR: DecryptMsg ret:' + str(ret)
    root = ET.fromstring(xml_content)
    from_user_name_element = root.find('FromUserName')
    content_element = root.find('Content')
    agent_id_element = root.find('AgentID')
    msg_type_element = root.find('MsgType')
    if msg_type_element is None or from_user_name_element is None or agent_id_element is None or content_element is None:
        return
    from_user_name = from_user_name_element.text
    content = content_element.text
    agent_id = agent_id_element.text
    msg_type = msg_type_element.text
    if msg_type != 'text':
        await send_message(from_user_name, agent_id, '暂只支持文本消息哦')
        return
    chat_gpt_content = await chat_gpt_api(from_user_name, content)
    await send_message(from_user_name, agent_id, chat_gpt_content)


async def check_proxy_port(host: str, port: str) -> bool:
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=5
        )
        writer.close()
        await writer.wait_closed()
        return True
    except (asyncio.TimeoutError, ConnectionRefusedError):
        return False


async def chat_gpt_api(from_user_name, content, error=None) -> str:
    if proxy_host and proxy_port:
        if not await check_proxy_port(proxy_host, proxy_port):
            error = '【network error:】代理网络请求不可达'
            return error
        os.environ['HTTP_PROXY'] = 'http://%s:%s' % (proxy_host, proxy_port)
        os.environ['HTTPS_PROXY'] = 'http://%s:%s' % (proxy_host, proxy_port)
    openai.api_key = open_ai_key[random.randint(0, len(open_ai_key) - 1)]
    ask = {"role": "user", "content": "%s" % content}
    await enqueue(from_user_name, json.dumps(ask, ensure_ascii=False))
    request = await dequeue(from_user_name)
    try:
        chat = openai.ChatCompletion.create(
            model='gpt-3.5-turbo', messages=request
        )
        reply = chat.choices[0].message.content
        response = {"role": "assistant", "content": "%s" % reply}
        await enqueue(from_user_name, json.dumps(response, ensure_ascii=False))
        return reply

    except openai.error.APIError:
        error = '【openai error:】这是openAI出现了问题,请稍后重试'
    except openai.error.Timeout:
        error = '【openai error:】请求超时了,稍等片刻后重试您的请求'
    except openai.error.RateLimitError:
        error = '【openai error:】请求速率太快了,openAI提供了恶意请求防护,稍等片刻后重试您的请求'
    except openai.error.APIConnectionError:
        error = '【openai error:】API连接错误,检查您的网络设置、代理配置、SSL 证书或防火墙规则'
    except openai.error.InvalidRequestError:
        error = '【openai error:】您的请求格式错误或缺少一些必需的参数，例如令牌或输入,请检查后重试'
    except openai.error.AuthenticationError:
        error = '【openai error:】您的API密钥或令牌无效、过期或已撤销,请检查您的API密钥或令牌并确保其正确且有效'
    except openai.error.ServiceUnavailableError:
        error = '【openai error:】openAI的服务器出现了问题,稍等片刻后重试您的请求'
    except Exception as e:
        error = '【openai error:】%s' % str(e)
    finally:
        if error is not None:
            logger.error(error)
            return error


async def get_we_chat_work_access_token() -> str:
    key = 'we_chat_work_access_token'
    url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=%s&corpsecret=%s' % (
        we_chat_work_corpid, we_chat_work_corpsecret)
    redis = await connect_redis()
    token = await redis.get(key)
    if token:
        return token
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            await redis.setex(key, 7000, data['access_token'])
            return data['access_token']


async def send_message(user, agent_id, content):
    token = await get_we_chat_work_access_token()
    body = {
        'touser': user,
        'msgtype': 'text',
        'agentid': agent_id,
        'text': {'content': content},
        'safe': 0,
        'enable_id_trans': 0,
        'enable_duplicate_check': 0,
        'duplicate_check_interval': 1800
    }
    url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=%s' % token
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=json.dumps(body)) as response:
            data = await response.json()
            if data['errcode'] != 0:
                logger.error('send message error:%s' % data['errmsg'])
