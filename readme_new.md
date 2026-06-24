# wecom-bot-svr · 企业微信机器人回调服务框架

[![PyPI](https://img.shields.io/pypi/v/wecom-bot-svr.svg)](https://pypi.org/project/wecom-bot-svr/)
[![Python](https://img.shields.io/badge/python-%3E%3D3.8-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Star History](https://img.shields.io/github/stars/easy-wx/wecom-bot-svr?style=social)](https://github.com/easy-wx/wecom-bot-svr)

基于 [Flask](https://flask.palletsprojects.com/) 的企业微信群机器人**回调服务**最小化框架。开发者只需实现两个回调函数（消息处理 + 事件处理），即可快速搭建一个具备加解密、主动推送、文件发送、健康检查、配置后台的完整服务。

> 如果项目对你有帮助，欢迎点一个 ⭐ Star。

---

## **特性**

- 开箱即用：两个函数即可上线一个企业微信机器人
- 内置回调消息加解密（兼容企业微信官方协议）
- 支持文本 / Markdown 回复，支持主动发送文件
- 内置 **主动推送接口**（仅本地网络可调用，安全隔离）
- 内置 **健康检查接口** `/health`，输出版本与运行状态
- 内置 **配置管理页面** `/config`，支持表单校验、敏感信息隐藏
- 支持 Docker 一键部署，支持环境变量注入敏感配置
- 日志级别可配置（环境变量或参数）

---

## **更新日志**

| 日期 | 版本 | 变更 |
|------|------|------|
| 2025-02-08 | - | 新增主动发送消息服务（本地网络 POST 触发） |
| 2024-12-09 | - | 新增主动文件发送（可由消息触发） |

---

## **快速开始**

### 1. 安装

```bash
pip3 install wecom-bot-svr
```

要求：Python ≥ 3.8。

### 2. 最小示例

参考 [demo/demo.py](demo/demo.py)：

```python
from wecom_bot_svr import WecomBotServer, RspTextMsg, RspMarkdownMsg, ReqMsg
from wecom_bot_svr.req_msg import TextReqMsg

def msg_handler(req_msg: ReqMsg, server: WecomBotServer):
    if req_msg.msg_type == 'text' and isinstance(req_msg, TextReqMsg):
        if req_msg.content.strip() == 'help':
            ret = RspMarkdownMsg()
            ret.content = "### Help\n- 输入任意消息回显类型"
            return ret
    ret = RspTextMsg()
    ret.content = f'msg_type: {req_msg.msg_type}'
    return ret

def event_handler(req_msg):
    ret = RspMarkdownMsg()
    if req_msg.event_type == 'add_to_chat':
        ret.content = f'欢迎！群ID：{req_msg.chat_id}，回复 help 查看用法'
    return ret

server = WecomBotServer('my-bot', '0.0.0.0', 5001, path='/wecom_bot',
                        token='xxx', aes_key='x' * 43, corp_id='', bot_key='xxxxx')
server.set_message_handler(msg_handler)
server.set_event_handler(event_handler)
server.run()
```

### 3. 本地验证

```bash
python3 demo.py
curl 'http://127.0.0.1:5001/wecom_bot?msg_signature=09380007d4f0891d966988e5450ad794c77fa01c&timestamp=1703041184&nonce=1703023880&echostr=oCdlC8pJ%2FDIjXnC8F9reyjDYlSImCmIgxA4prPD%2Bl2Fj5qBHjFiWnpelQofsDCJrSEvNVTET6oQmoXLQxzUkyQ%3D%3D'
```

---

## **接入企业微信**

### 1. 创建机器人并配置回调

群聊右上角「...」→「添加群机器人」→「接收消息配置」，填入回调地址、Token、AESKey。

<img src="https://github.com/easy-wx/wecom-bot-svr/raw/main/images/new_wecom_bot.png" width="420" />

### 2. 群内体验

支持 `help` 命令回复、入群事件触发欢迎语：

<p>
<img src="https://github.com/easy-wx/wecom-bot-svr/raw/main/images/add_wecom_bot.png" width="320" />
<img src="https://github.com/easy-wx/wecom-bot-svr/raw/main/images/wecom_bot_join.png" width="320" />
</p>

### 3. 发布到公司

机器人资料页 → 「发布到公司」，发布后才能被同事搜索并添加到其他群。

<img src="https://github.com/easy-wx/wecom-bot-svr/raw/main/images/publish_wecom_bot.png" width="420" />

---

## **配置项**

### 构造参数

```python
WecomBotServer(
    bot_name, host, port,
    path='/wecom_bot',          # 回调路径
    token=..., aes_key=..., corp_id=...,
    bot_key=...,                # WebHook key，用于发送文件/主动消息
    config_page_path='/config', # 设为 None 可关闭
    health_check_path='/health',
    log_level='INFO',
)
```

### 环境变量（推荐生产使用）

| 变量 | 说明 |
|------|------|
| `WX_BOT_TOKEN` | 回调 Token |
| `WX_BOT_AES_KEY` | 回调 AESKey（43 字符） |
| `WX_BOT_CORP_ID` | 企业 CorpID |
| `WX_BOT_LOG_LEVEL` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |

> Token / AESKey 建议在机器人配置页使用「随机生成」按钮获取，不要硬编码到代码中。

<p>
<img src="https://github.com/easy-wx/wecom-bot-svr/raw/main/images/random_token_1.png" width="320" />
<img src="https://github.com/easy-wx/wecom-bot-svr/raw/main/images/random_token_2.png" width="320" />
</p>

---

## **核心能力**

### 消息与事件处理

- `msg_handler(req_msg, server) -> rsp_msg`：处理文本等消息
- `event_handler(req_msg) -> rsp_msg`：处理入群等事件
- 请求消息类型见 [src/wecom_bot_svr/req_msg.py](src/wecom_bot_svr/req_msg.py)
- 响应消息支持 `RspTextMsg` / `RspMarkdownMsg`，定义见 [src/wecom_bot_svr/rsp_msg.py](src/wecom_bot_svr/rsp_msg.py)

### 发送文件

构造服务时传入 `bot_key`（来自 WebHook URL 的 key），即可在消息处理函数中调用：

```python
def msg_handler(req_msg: ReqMsg, server: WecomBotServer):
    with open('output.txt', 'w') as f:
        f.write("hello from wecom-bot-svr")
    server.send_file(req_msg.chat_id, 'output.txt')
    return RspTextMsg()
```

<img src="https://github.com/easy-wx/wecom-bot-svr/raw/main/images/send_file.png" width="420" />

原理参考：[企业微信文件类型文档](https://developer.work.weixin.qq.com/document/path/91770)。

### 主动推送（`/active_send`）

独立路由用于业务侧主动触发消息，**仅接受本地网络 POST**，外网请求自动拒绝。可与回调逻辑解耦。

```python
import requests
requests.post("http://127.0.0.1:5001/active_send",
              data={"msg_type": "text", "chat_id": "<user_or_chat_id>", "content": "主动消息"})
```

<p>
<img src="https://github.com/easy-wx/wecom-bot-svr/raw/main/images/active_send.png" width="320" />
<img src="https://github.com/easy-wx/wecom-bot-svr/raw/main/images/active_send_group.png" width="320" />
</p>

### 健康检查（`/health`）

```bash
curl http://127.0.0.1:5001/health
```

返回服务名、版本、监听地址、各路由路径、日志级别、启动时间和已运行秒数，便于运维探活。

### 配置管理页面（`/config`）

浏览器访问 `/config` 可查看 / 编辑 Token、AESKey、CorpID、Bot Key 等配置项。
- 仅写入当前浏览器 `localStorage`，**不落盘**到服务端
- 支持敏感信息隐藏 / 显示、表单校验、启动参数预览
- 生产环境如需开放该页面，建议加鉴权或仅允许内网访问；不需要时可设 `config_page_path=None`

---

## **Docker 部署**

```bash
cd demo
docker build -t wecom-bot-svr-demo .
docker run -d -p 5001:5001 \
  -e WX_BOT_TOKEN=xxx \
  -e WX_BOT_AES_KEY=xxx \
  -e WX_BOT_CORP_ID=xxx \
  wecom-bot-svr-demo
```

回调地址即 `http(s)://<your-domain>/wecom_bot`，填入企业微信机器人后台即可。

---

## **项目结构**

```
wecom-bot-svr/
├── src/wecom_bot_svr/      # 框架源码
│   ├── app.py              # WecomBotServer 主体
│   ├── req_msg.py          # 请求消息模型
│   ├── rsp_msg.py          # 响应消息模型
│   └── req_msg_str.py      # 原始字符串解析
├── demo/                   # 最小示例 + Dockerfile
├── docker/                 # 部署用 Dockerfile
├── tests/                  # 单元测试
└── pyproject.toml
```

更多开发细节见 [DEVELOPMENT.md](DEVELOPMENT.md)。

---

## **路线图**

- [ ] 默认权限支持（按用户 / 群组）
- [ ] 更多响应消息类型支持

欢迎通过 Issue / PR 提建议。

---

## **License**

[MIT](LICENSE) © panzhongxian

## **Star History**

[![Star History Chart](https://api.star-history.com/svg?repos=easy-wx/wecom-bot-svr&type=Date)](https://star-history.com/#easy-wx/wecom-bot-svr&Date)
