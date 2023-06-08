import os
import tomli


def parse_config() -> dict:
    env = os.environ.get('envID')
    if env is None:
        env = 'sit'
    try:
        with open('%s_config.toml' % env, encoding='utf-8') as c:
            return tomli.loads(c.read())
    except (Exception,):
        raise


config = parse_config()
redis_host = config['redis']['host']
redis_port = config['redis']['port']
redis_db = config['redis']['db']
redis_charset = config['redis']['charset']
redis_queue_max_length = config['redis']['queue_max_length']
redis_queue_ttl = config['redis']['queue_ttl']
open_ai_key = config['open_ai']['key']
proxy_host = config['proxy']['host']
proxy_port = config['proxy']['port']
log_path = config['log']['path']
app_name = config['app']['name']
we_chat_work_token = config['we_chat_work']['token']
we_chat_work_encodingAESKey = config['we_chat_work']['encodingAESKey']
we_chat_work_corpid = config['we_chat_work']['corpid']
we_chat_work_corpsecret = config['we_chat_work']['corpsecret']
