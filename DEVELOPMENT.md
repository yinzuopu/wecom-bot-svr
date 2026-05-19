# wecom-bot-svr 开发说明

本文面向第一次接触本仓库的新同学，内容基于当前仓库内真实文件整理；未在仓库中确认的信息以“待确认”标注。

## 1. 项目用途一句话说明

`wecom-bot-svr` 是一个基于 Flask 的企业微信机器人回调服务简单框架，封装了企业微信机器人回调的加解密、消息解析、响应消息生成、主动发送与健康检查能力。

依据：`README.md`、`pyproject.toml`、`src/wecom_bot_svr/app.py`。

## 2. 本地启动 / 配置 / 测试步骤

### 2.1 环境要求

- Python：`>=3.8`，见 `pyproject.toml`。
- 运行依赖，见 `pyproject.toml`：
  - `requests>=2.32.3`
  - `Flask>=3.0.0`
  - `wx-crypt>=0.0.2`

### 2.2 安装依赖

仓库内未提供 `requirements.txt`，也未提供明确的本地开发安装脚本。可基于 `pyproject.toml` 使用 Python 包安装方式安装当前仓库：

```bash
python3 -m pip install .
```

如需以可编辑模式开发，可使用：

```bash
python3 -m pip install -e .
```

> 说明：以上命令基于当前仓库存在的 `pyproject.toml`。仓库 README 中也提供了安装已发布包的方式：`pip3 install wecom-bot-svr`。

### 2.3 配置项

`WecomBotServer` 构造函数支持直接传入配置，也支持从环境变量读取部分配置。

| 配置 | 代码中的来源 | 用途 |
| --- | --- | --- |
| `token` / `WX_BOT_TOKEN` | `src/wecom_bot_svr/app.py` | 企业微信机器人回调 Token |
| `aes_key` / `WX_BOT_AES_KEY` | `src/wecom_bot_svr/app.py` | 企业微信机器人回调 AESKey |
| `corp_id` / `WX_BOT_CORP_ID` | `src/wecom_bot_svr/app.py` | 企业 ID；默认空字符串 |
| `bot_key` / `WX_BOT_KEY` | `src/wecom_bot_svr/app.py` | WebHook key，用于主动发送和文件上传 |
| `path` | `demo/demo.py`、`src/wecom_bot_svr/app.py` | 回调路径，demo 中为 `/wecom_bot` |
| `active_msg_path` | `src/wecom_bot_svr/app.py` | 主动发送路径，默认 `/active_send` |
| `health_check_path` | `src/wecom_bot_svr/app.py` | 健康检查路径，默认 `/health` |

README 中说明：实际使用时建议在机器人配置页面随机生成 Token 和 AESKey；demo 中的固定值仅用于示例。

### 2.4 启动 demo

当前仓库提供 demo：`demo/demo.py`。

README 中给出的启动方式是进入 demo 所在目录运行：

```bash
cd demo
python3 demo.py
```

`demo/demo.py` 中默认配置包括：

- `host = '0.0.0.0'`
- `port = 5001`
- `path = '/wecom_bot'`
- `bot_name = 'jasonzxpan-test'`
- `token`、`aes_key`、`bot_key` 为示例占位值，需要按实际机器人配置替换或改为环境变量方式。

> 待确认：当前仓库没有提供 `.env`、配置文件模板或启动脚本；实际团队内部使用的配置管理方式需要进一步确认。

### 2.5 健康检查

服务启动后默认注册健康检查接口：

```bash
curl http://127.0.0.1:5001/health
```

返回内容来自 `WecomBotServer.get_runtime_status()`，包含：

- `status`
- `name`
- `version`
- `host`
- `port`
- `callback_path`
- `active_msg_path`
- `health_check_path`
- `started_at`
- `uptime_seconds`

也可以在构造 `WecomBotServer` 时通过 `health_check_path` 自定义路径。

### 2.6 回调 URL 验证

README 中给出了针对 demo 默认 Token 和 AESKey 的 curl 示例：

```bash
curl 'http://127.0.0.1:5001/wecom_bot?msg_signature=09380007d4f0891d966988e5450ad794c77fa01c&timestamp=1703041184&nonce=1703023880&echostr=oCdlC8pJ%2FDIjXnC8F9reyjDYlSImCmIgxA4prPD%2Bl2Fj5qBHjFiWnpelQofsDCJrSEvNVTET6oQmoXLQxzUkyQ%3D%3D'
```

该接口对应 `src/wecom_bot_svr/app.py` 中的 `handle_bot_call_get()`。

### 2.7 主动发送消息

服务默认注册本地主动发送接口：`POST /active_send`。

示例，见 README：

```python
import requests

url = "http://127.0.0.1:5001/active_send"
data = {"msg_type": "text", "chat_id": "12345", "content": "主动消息推送测试"}

response = requests.post(url, data=data)

print(response.text)
```

注意：`handle_active_send()` 中限制 `request.remote_addr` 必须是 `127.0.0.1`，非本地来源会返回 `Invalid request`。

当前支持的 `msg_type` 来自 `src/wecom_bot_svr/app.py`：

- `file`：需要 `chat_id`、`file_path`
- `markdown`：需要 `chat_id`、`content`
- `text`：需要 `chat_id`、`content`
- `image`：需要 `chat_id`、`base64_image_data`、`md5`
- `news`：需要 `chat_id`、`title`、`description`、`url`、`pic_url`

### 2.8 运行测试

当前仓库存在 `tests/test_health_check.py`，使用 Python 标准库 `unittest`。

已在本地验证可运行：

```bash
python3 -m unittest discover -s tests
```

当前测试覆盖：

- `WecomBotServer.get_runtime_status()` 返回字段。
- 自定义健康检查路径注册和 Flask test client 访问。

> 当前测试运行时，本地环境可能出现 `urllib3` 关于 LibreSSL 的 warning，但测试结果为 OK；是否需要处理该 warning 待确认。

## 3. 核心目录说明

```text
.
├── README.md
├── pyproject.toml
├── src/wecom_bot_svr/
├── demo/
├── tests/
├── docker/
├── images/
└── .github/workflows/
```

| 路径 | 说明 |
| --- | --- |
| `README.md` | 项目介绍、使用方式、企业微信机器人配置、发送文件、主动发送、健康检查说明。 |
| `pyproject.toml` | Python 包元信息、版本、依赖、Python 版本要求和构建后端配置。 |
| `src/wecom_bot_svr/__init__.py` | 包导出入口，导出 `WecomBotServer`、`ReqMsg`、`RspMsg`、`RspTextMsg`、`RspMarkdownMsg`。 |
| `src/wecom_bot_svr/app.py` | 核心服务实现：Flask 路由注册、企业微信加解密、消息/事件分发、主动发送、文件上传、健康检查。 |
| `src/wecom_bot_svr/req_msg.py` | 回调请求消息模型，支持 `text`、`event`、`image`、`attachment`、`mixed` 等消息类型解析。 |
| `src/wecom_bot_svr/rsp_msg.py` | 响应消息模型，当前包含文本和 Markdown 回复类型。 |
| `src/wecom_bot_svr/req_msg_str.py` | 内置若干 XML 消息样例并打印解析结果，可用于理解 `ReqMsg.create_msg()` 的解析效果；不是单元测试文件。 |
| `demo/demo.py` | 可运行 demo，展示 `msg_handler`、`event_handler`、文件发送、服务启动方式。 |
| `demo/Dockerfile` | demo 镜像构建文件，基于 `docker.io/panzhongxian/wecom-bot-svr`，复制 demo 并运行 `demo.py`。 |
| `docker/Dockerfile` | 基础镜像构建文件，安装 Python3、pip 和已发布的 `wecom-bot-svr==0.2.1`。 |
| `tests/test_health_check.py` | 健康检查相关单元测试。 |
| `images/` | README 中使用的截图资源。 |
| `.github/workflows/python-publish.yml` | GitHub Release 发布时构建并发布 Python 包到 PyPI 的工作流。 |

## 4. 常见开发任务流程

### 4.1 新增或修改机器人消息回复逻辑

1. 参考 `demo/demo.py` 中的 `msg_handler(req_msg, server)`。
2. 根据 `req_msg.msg_type` 和具体消息类判断消息类型。
3. 返回 `RspTextMsg()` 或 `RspMarkdownMsg()`。
4. 使用 `server.set_message_handler(msg_handler)` 注册处理函数。
5. 启动服务后在企业微信群中发送消息验证。

示例逻辑来自 `demo/demo.py`：

- 收到文本 `help` 时返回 Markdown 帮助。
- 收到文本 `give me a file` 时生成 `output.txt` 并调用 `server.send_file()`。
- 其他消息返回 `msg_type`。

### 4.2 新增或修改事件处理逻辑

1. 参考 `demo/demo.py` 中的 `event_handler(req_msg)`。
2. 根据 `req_msg.event_type` 判断事件类型。
3. 返回 `RspTextMsg()` 或 `RspMarkdownMsg()`。
4. 使用 `server.set_event_handler(event_handler)` 注册处理函数。

当前 demo 已处理 `add_to_chat` 入群事件。

### 4.3 新增请求消息类型解析

1. 修改 `src/wecom_bot_svr/req_msg.py`。
2. 新增对应的 `ReqMsg` 子类。
3. 在 `ReqMsg.create_msg(xml_tree)` 中增加 `msg_type` 分支。
4. 可参考 `src/wecom_bot_svr/req_msg_str.py` 增加 XML 样例进行本地解析验证。
5. 建议补充对应单元测试；当前仓库尚未提供请求消息解析的单元测试，待确认测试规范。

### 4.4 新增响应消息类型

1. 修改 `src/wecom_bot_svr/rsp_msg.py`。
2. 继承 `RspMsg`，设置 `self.msg_type`。
3. 实现或扩展 `update_xml()`，写入企业微信要求的 XML 节点。
4. 如需对外导出，在 `src/wecom_bot_svr/__init__.py` 中补充导出。
5. 补充测试，测试命令见“2.8 运行测试”。

### 4.5 调整服务路由或运行状态字段

1. 核心逻辑在 `src/wecom_bot_svr/app.py` 的 `WecomBotServer`。
2. `run()` 方法注册当前路由：
   - `GET {path}`：企业微信 URL 验证。
   - `POST {path}`：企业微信回调消息处理。
   - `POST {active_msg_path}`：主动发送。
   - `GET {health_check_path}`：健康检查。
3. 如调整健康检查字段，需同步更新 `tests/test_health_check.py`。
4. 运行：

```bash
python3 -m unittest discover -s tests
```

### 4.6 发布 Python 包

仓库包含 `.github/workflows/python-publish.yml`，触发条件是 GitHub Release `published`。

工作流步骤：

1. checkout 代码。
2. 使用 Python `3.x`。
3. 安装 `build`。
4. 执行 `python -m build`。
5. 使用 `pypa/gh-action-pypi-publish` 发布到 PyPI。

> 待确认：PyPI token、发版审批、版本号变更规范未在仓库中说明。

### 4.7 Docker 相关开发

仓库有两个 Dockerfile：

- `docker/Dockerfile`：基础镜像，安装已发布版本 `wecom-bot-svr==0.2.1`。
- `demo/Dockerfile`：demo 镜像，安装已发布版本 `wecom-bot-svr==0.2.3`，复制 demo 并执行 `python3 /data/code/demo.py`。

README 中提供的 Docker 构建命令为：

```bash
cd demo
docker build -t wx_bot docker.io/panzhongxian/wecom-bot-svr-demo:latest .
docker push docker.io/panzhongxian/wecom-bot-svr-demo:latest
```

> 注意：该 `docker build` 命令直接来自 README，但常见 Docker 用法中 `-t` 后通常接镜像名，最后一个参数是构建上下文；此处命令是否符合当前团队预期待确认。不要在未确认前修改为其他命令。

## 5. 常见问题与排查建议

### 5.1 企业微信机器人配置保存失败

可能原因：

- 本地服务未启动或外网无法访问回调地址。
- 企业微信配置的回调路径与服务 `path` 不一致，demo 中为 `/wecom_bot`。
- Token 或 AESKey 与代码/环境变量不一致。
- `WX_BOT_CORP_ID` 或传入的 `corp_id` 不符合实际企业配置；README 中 demo 使用空字符串，实际值待确认。

排查建议：

1. 确认服务已启动在 `host` / `port` 上，demo 为 `0.0.0.0:5001`。
2. 访问健康检查：

```bash
curl http://127.0.0.1:5001/health
```

3. 检查企业微信机器人配置中的回调地址是否包含正确路径。
4. 检查 Token、AESKey 是否与机器人配置一致。

### 5.2 启动时报 `message handler is not set` 或 `event handler is not set`

原因：`WecomBotServer.run()` 中会检查是否已注册消息处理函数和事件处理函数。

排查建议：

```python
server.set_message_handler(msg_handler)
server.set_event_handler(event_handler)
server.run()
```

### 5.3 主动发送接口返回 `Invalid request`

原因：`handle_active_send()` 只允许 `request.remote_addr == "127.0.0.1"`。

排查建议：

- 在服务本机使用 `127.0.0.1` 调用。
- 如果需要从其他机器触发主动发送，需要修改安全策略；具体方案待确认。

### 5.4 主动发送文本、Markdown、图片、图文失败

可能原因：

- `bot_key` 未传入且环境变量 `WX_BOT_KEY` 未配置。
- `chat_id` 不正确。
- 企业微信接口返回失败；当前 `proactively_send()` 只返回“发送成功/失败”，未暴露详细错误。

排查建议：

1. 确认 `bot_key` 或 `WX_BOT_KEY`。
2. 确认 `chat_id` 是个人 ID 或群 ID。
3. 如需更详细错误，待确认是否要增强日志或返回企业微信原始响应。

### 5.5 发送文件失败

可能原因：

- `file_path` 不存在或服务进程无读取权限。
- `bot_key` / `WX_BOT_KEY` 未配置。
- 企业微信上传文件接口失败。

排查建议：

1. 确认文件路径存在。
2. 确认服务进程能读取该文件。
3. 确认 `bot_key` 配置正确。
4. 查看 `src/wecom_bot_svr/app.py` 中 `upload_file()` 和 `send_file()`。

### 5.6 群聊里 @ 机器人后的文本匹配不符合预期

`handle_bot_call_post()` 中对群聊文本消息做了处理：

```python
msg.content = msg.content.replace(f"@{self.name}", "")
```

排查建议：

- 确认 `WecomBotServer` 的 `name` 与机器人名字一致。
- 在消息处理函数中对 `req_msg.content.strip()` 后再判断命令；demo 中就是这样处理 `help` 的。

### 5.7 健康检查版本显示为 `unknown`

`get_runtime_status()` 中版本来自：

```python
metadata.version("wecom-bot-svr")
```

如果当前代码未以 Python 包形式安装，可能拿不到包版本并返回 `unknown`。

排查建议：

```bash
python3 -m pip install -e .
```

然后重新启动服务。

### 5.8 测试执行有 warning

本地运行测试时观察到 `urllib3` 关于 LibreSSL 的 warning，但测试通过：

```text
urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'
```

排查建议：

- 如果只是本地单元测试且结果 OK，可先记录。
- 是否需要调整 Python/OpenSSL 环境或依赖版本，待确认。

## 6. 新同学建议阅读顺序

1. 先读 `README.md`，理解项目使用场景和企业微信机器人配置流程。
2. 再读 `demo/demo.py`，理解最小可运行服务如何实现消息和事件处理。
3. 阅读 `src/wecom_bot_svr/app.py`，理解 Flask 路由、加解密和主动发送。
4. 阅读 `src/wecom_bot_svr/req_msg.py` 与 `src/wecom_bot_svr/rsp_msg.py`，理解请求/响应消息结构。
5. 最后阅读 `tests/test_health_check.py`，了解当前测试组织方式。
