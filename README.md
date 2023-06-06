# chatgpt

## 实现功能
- 对接内部企业微信,实现自建应用会话聊天功能

- 提供websocket服务,实现类似chatGPT官网页面功能

## 企业微信接收消息服务器配置

- 申请企业微信应用(拥有应用管理的设置权限)

- 应用设置
```bash
开启API接收消息功能,其中token和EncodingAESKey随机获取即可,URL用来提供企业微信的请求验证,
假设部署此项目的服务器在企业内网且IP地址为192.168.10.100,提供的验证接口为http://192.168.10.100:52712/api/v1/chat,
将192.168.10.100以及端口52712映射到公网,最后在nginx上配置一个域名解析,域名要求企业备案,否则验证不通过,域名解析后最终得到http://xxx.xxx.com/api/v1/chat粘贴到URL中,暂时不要点击保存,接下来部署服务
```  
![img](docs/api.png)
  
- 下载项目/编辑配置文件(sit_config.toml)
```bash
git clone git@github.com:xxddpac/chatgpt.git
```
```bash
[we_chat_work]中token以及EncodingAESKey对应以上随机获取的值,corpid/corpsecret从企业微信管理员获取
  
[redis]作为缓存企业微信发送消息的access_token以及chatgpt根据企业微信用户名关联的上下文
  
[proxy]作为获取代理服务器的IP端口以及chatgpt的openai_key的接口,将这部分配置抽出来为了后续方便新增或删除openai_key时服务不用重新发布
```
- proxy接口API返回示例(自行实现此接口)
```json
      {
    "code": 200,
    "msg": "success",
    "data": {
        "key": [
            "key1",
            "key2",
            "key3",
            "key4"
        ],
        "port": "7890",
        "proxy": "10.10.10.10"
    }}
```
- docker构建启动服务

```bash
docker build -t chatgpt .
docker images | grep chatgpt
docker run -d -p 52712:52712 -v /var/log:/var/log --name 'secchatgpt' chatgpt
docker ps -a | grep chatgpt
```
- 消息验证
```bash
点击企业微信保存按钮,此刻企业微信会立即发送验证信息,若验证失败,检查域名连通性以及服务日志

docker logs secchagpt
```

## 代理服务器配置(可自行选择适合代理,这里使用clash for linux)
```bash
mkdir clash
cd clash
wget https://github.com/Dreamacro/clash/releases/download/v1.8.0/clash-linux-amd64-v1.8.0.gz
mv clash-linux-amd64-v1.8.0 clash
wget -O config.yaml "替换你的服务订阅地址"?clash=1 --no-check-certificate
chmod +x clash
```
编辑config.yaml将allow-lan由fasle改为true
```bash
allow-lan: true
```
下载MMDB并启动clash
```bash
./clash -d .
```
## 最后
- 至此企业微信与chatgpt对接成功,为了节省chatgpt关联上下文消耗token数,使用过期的定长队列来缓存上下文,每个企业微信用户只关联最近6次会话历史,缓存时间60分钟

- websocket_client作为测试客户端,前端作为客户端连接ws://服务地址:52712/ws即可实现类似chatgpt官网效果