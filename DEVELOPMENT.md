# 新同学开发说明

## 1. 项目用途一句话说明

本项目是一个基于 Flask 的企业微信机器人回调服务简单框架，封装了企业微信回调消息的加解密、请求解析、响应消息生成和主动消息发送能力。

## 2. 本地启动 / 配置 / 测试步骤

### 环境要求

- Python 版本：`pyproject.toml` 声明 `requires-python = ">=3.8"`。
- Python 依赖：`pyproject.toml` 声明依赖 `requests>=2.32.3`、`Flask>=3.0.0`、`wx-crypt>=0.0.2`。
- 仓库未提供 `requirements.txt`、`Makefile` 或专门的本地开发脚本。

### 安装本地包

在仓库根目录执行：

```bash
python3 -m pip install -e .
```

说明：当前源码采用 `src/` 目录布局，直接运行测试前需要先安装本地包，否则可能出现 `ModuleNotFoundError: No module named 'wecom_bot_svr'`。

### 启动 demo 服务

仓库内 demo 文件位于 `demo/demo.py`。在仓库根目录可执行：

```bash
python3 demo/demo.py
```

或进入 demo 目录后执行：

```bash
cd demo
python3 demo.py
```

`demo/demo.py` 中当前默认配置如下：

- HTTP 监听地址：`0.0.0.0`
- HTTP 端口：`5001`
- 企业微信回调路径：`/wecom_bot`
- 主动发送路径：`/active_send`
- 状态检查路径：`/status`
- `token`、`aes_key`、`bot_key`：示例占位值，需要按企业微信机器人配置替换
- `bot_name`：示例值 `jasonzxpan-test`，代码注释说明需要与机器人名字一致，用于切分群聊中的 @ 消息

本地启动后，可访问状态检查接口：

```bash
curl http://127.0.0.1:5001/status
```

README 中也提供了一个用于验证企业微信 URL 回调校验的 `curl` 示例，该示例依赖 demo 中匹配的 token 和 AESKey。当前 `demo/demo.py` 已使用占位配置，实际可用的验证链接需要根据真实企业微信配置重新生成，待确认。

### 配置项

`WecomBotServer` 构造函数支持直接传参：

- `name`
- `host`
- `port`
- `path`
- `token`
- `aes_key`
- `corp_id`
- `bot_key`
- `active_msg_path`，默认 `/active_send`
- `status_path`，默认 `/status`，传入 `None` 可关闭状态检查路由

如果未通过构造函数传入部分配置，代码会读取以下环境变量：

- `WX_BOT_TOKEN`
- `WX_BOT_AES_KEY`
- `WX_BOT_CORP_ID`
- `WX_BOT_KEY`

README 中只明确提到 `WX_BOT_TOKEN`、`WX_BOT_AES_KEY`、`WX_BOT_CORP_ID`，`WX_BOT_KEY` 来自当前 `src/wecom_bot_svr/app.py` 代码。

### 运行测试

仓库当前测试使用 Python 标准库 `unittest`，测试文件位于 `tests/test_status.py`。在完成本地包安装后执行：

```bash
python3 -m unittest discover -s tests
```

当前验证结果：执行上述命令通过 2 个测试。

### 构建发布包

`.github/workflows/python-publish.yml` 中的发布流程在 GitHub Release 发布时触发，核心构建命令是：

```bash
python -m pip install --upgrade pip
pip install build
python -m build
```

发布到 PyPI 使用 `pypa/gh-action-pypi-publish`，依赖仓库密钥 `PYPI_API_TOKEN`。

## 3. 核心目录说明

- `src/wecom_bot_svr/`：Python 包源码目录。
- `src/wecom_bot_svr/app.py`：`WecomBotServer` 主实现，包含 Flask 路由注册、企业微信回调校验、消息解密、响应加密、状态检查、文件上传和主动发送消息逻辑。
- `src/wecom_bot_svr/req_msg.py`：企业微信回调请求消息对象，当前支持 `text`、`event`、`image`、`attachment`、`mixed` 等消息类型解析。
- `src/wecom_bot_svr/rsp_msg.py`：机器人响应消息对象，当前包含基础 `RspMsg`、文本响应 `RspTextMsg` 和 Markdown 响应 `RspMarkdownMsg`。
- `src/wecom_bot_svr/version.py`：版本信息读取逻辑，优先读取已安装包版本，读取失败时回退到源码内 `__version__`。
- `src/wecom_bot_svr/__init__.py`：包导出入口，导出 `WecomBotServer`、响应消息类、请求消息类和版本号。
- `src/wecom_bot_svr/req_msg_str.py`：请求消息 XML 示例与解析打印脚本，用于理解不同消息结构；当前文件导入时会直接执行打印逻辑，作为正式测试工具的用途待确认。
- `demo/`：demo 服务示例和 demo Dockerfile。
- `docker/`：基础 Dockerfile，当前安装的是 `wecom-bot-svr==0.2.1`，与 `pyproject.toml` 中版本 `0.3.3` 不一致，是否仍用于当前版本待确认。
- `tests/`：单元测试目录，当前覆盖状态检查接口。
- `images/`：README 使用的截图资源。
- `.github/workflows/`：GitHub Actions 工作流，目前包含 PyPI 发布流程。

## 4. 常见开发任务流程

### 修改机器人回调处理逻辑

1. 参考 `demo/demo.py` 中的 `msg_handler(req_msg, server)` 和 `event_handler(req_msg)`。
2. 消息处理函数通过 `server.set_message_handler(...)` 注册。
3. 事件处理函数通过 `server.set_event_handler(...)` 注册。
4. 文本响应使用 `RspTextMsg`，Markdown 响应使用 `RspMarkdownMsg`。
5. 如需在消息处理中发送文件，可使用带 `server` 参数的 handler，并调用 `server.send_file(req_msg.chat_id, file_path)`。

### 新增或调整请求消息解析

1. 在 `src/wecom_bot_svr/req_msg.py` 中新增或修改消息类。
2. 在 `ReqMsg.create_msg(xml_tree)` 中补充 `MsgType` 到消息类的分发逻辑。
3. 为新增解析行为补充测试，当前测试目录为 `tests/`；测试框架为 `unittest`。
4. 执行 `python3 -m unittest discover -s tests`。

### 新增或调整响应消息类型

1. 在 `src/wecom_bot_svr/rsp_msg.py` 中参考 `RspTextMsg` 和 `RspMarkdownMsg` 新增响应类。
2. 在 `update_xml()` 中写入企业微信要求的 XML 节点。
3. 如需对外导出，在 `src/wecom_bot_svr/__init__.py` 中补充导入和 `__all__`。
4. 补充对应测试，执行 `python3 -m unittest discover -s tests`。

### 调整主动发送消息能力

1. 主动发送入口在 `src/wecom_bot_svr/app.py` 的 `handle_active_send()`。
2. 当前仅允许 `request.remote_addr == "127.0.0.1"` 的请求，否则返回 `Invalid request`。
3. 当前支持的 `msg_type` 包括 `file`、`markdown`、`text`、`image`、`news`。
4. 实际发送通过 `proactively_send()` 调企业微信 webhook；文件发送会先通过 `upload_file()` 上传得到 `media_id`。
5. 修改后补充或更新测试，再执行 `python3 -m unittest discover -s tests`。

### 调整状态检查接口

1. 状态数据来自 `src/wecom_bot_svr/app.py` 的 `get_status()`。
2. 默认路径是 `/status`，可通过构造函数参数 `status_path` 改为其他路径，传入 `None` 可关闭。
3. 当前相关测试在 `tests/test_status.py`。
4. 修改后执行 `python3 -m unittest discover -s tests`。

### 更新版本与发布

1. 当前版本号同时出现在 `pyproject.toml` 的 `project.version` 和 `src/wecom_bot_svr/version.py` 的 `__version__`。
2. 发布包构建流程见 `.github/workflows/python-publish.yml`。
3. 发布触发方式为 GitHub Release 的 `published` 事件。
4. Docker 镜像发布流程未在仓库内发现自动化配置，待确认。

## 5. 常见问题与排查建议

### `ModuleNotFoundError: No module named 'wecom_bot_svr'`

原因通常是当前源码包尚未安装到 Python 环境。先在仓库根目录执行：

```bash
python3 -m pip install -e .
```

然后重新运行：

```bash
python3 -m unittest discover -s tests
```

### 企业微信配置保存失败

排查建议：

- 确认服务已启动，并且企业微信可访问回调地址。
- 确认回调路径与服务构造参数 `path` 一致，demo 中为 `/wecom_bot`。
- 确认 token、AESKey、corp_id 与企业微信机器人配置一致。
- 确认 `WX_BOT_TOKEN`、`WX_BOT_AES_KEY`、`WX_BOT_CORP_ID` 是否被正确设置，或确认构造函数是否显式传入了正确值。
- 如果使用 README 中的历史 `curl` 示例，需要确认它是否仍匹配当前 demo 配置；当前 demo 使用占位值，待确认。

### `/active_send` 返回 `Invalid request`

`handle_active_send()` 只接受来源 IP 为 `127.0.0.1` 的请求。请确认请求是从本机发起，例如：

```bash
curl -X POST http://127.0.0.1:5001/active_send \
  -d 'msg_type=text' \
  -d 'chat_id=待确认' \
  -d 'content=主动消息推送测试'
```

其中 `chat_id` 需要替换为真实个人 ID 或群 ID。

### 主动发送文件失败

排查建议：

- 确认构造函数传入了 `bot_key`，或环境变量 `WX_BOT_KEY` 已设置。
- 确认 `file_path` 指向的文件存在且服务进程可读取。
- 确认企业微信 webhook key 有效。
- `upload_file()` 捕获异常后会返回 `None`，外部表现通常是 `上传文件失败`；更详细错误日志当前代码未输出，是否需要增强日志待确认。

### 状态接口 404

排查建议：

- 默认状态接口为 `/status`。
- 如果构造 `WecomBotServer` 时传入了 `status_path="/healthz"`，则应访问 `/healthz`。
- 如果传入 `status_path=None`，状态接口会被关闭。

### Docker 镜像版本与源码版本不一致

当前 `pyproject.toml` 版本为 `0.3.3`，但 `docker/Dockerfile` 安装 `wecom-bot-svr==0.2.1`，`demo/Dockerfile` 安装 `wecom-bot-svr==0.2.3`。这两个 Dockerfile 是否仍是当前推荐部署方式待确认；使用前建议先确认目标版本。
