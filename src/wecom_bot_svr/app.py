import inspect
import logging
import os
import xml.etree.cElementTree as ET
from datetime import datetime, timezone
from importlib import metadata

import requests
from flask import Flask, jsonify, render_template_string, request
from wx_crypt import WXBizMsgCrypt, WxChannel_Wecom

from .req_msg import ReqMsg


# 参考文档：https://km.woa.com/articles/show/387107?kmref=search&from_page=1&no=2#10128


def _encode_rsp(wx_cpt, rsp_str):
    xml = ET.Element('xml')
    ET.SubElement(xml, 'MsgType').text = 'markdown'
    markdown = ET.SubElement(xml, 'Markdown')
    ET.SubElement(markdown, 'Content').text = rsp_str
    plain = ET.tostring(xml).decode()

    # 加密消息
    params = request.args
    timestamp = params.get("timestamp")
    nonce = params.get("nonce")
    ret, rsp = wx_cpt.EncryptMsg(plain, nonce, timestamp)
    if ret != 0:
        print("err: encrypt fail: " + str(ret))
    return rsp


def _get_package_version():
    try:
        return metadata.version("wecom-bot-svr")
    except metadata.PackageNotFoundError:
        return "unknown"


def _resolve_log_level(log_level):
    if log_level is None:
        return None
    if isinstance(log_level, int):
        return log_level

    level_name = str(log_level).strip().upper()
    if not level_name:
        return None

    level = logging.getLevelName(level_name)
    if isinstance(level, int):
        return level
    raise ValueError(f"invalid log level: {log_level}")


CONFIG_PAGE_TEMPLATE = r"""
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>企业微信机器人配置管理</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f5f7fb;
      --panel: #ffffff;
      --text: #172033;
      --muted: #667085;
      --line: #d9e1ec;
      --primary: #1769e0;
      --primary-dark: #0f56bd;
      --danger: #c0392b;
      --success: #16845b;
      --warning: #a15c00;
      --code-bg: #101828;
      --shadow: 0 16px 40px rgba(16, 24, 40, 0.08);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      background: linear-gradient(180deg, #eef4ff 0%, var(--bg) 260px);
      color: var(--text);
      font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans SC", sans-serif;
    }

    .page {
      width: min(1120px, calc(100% - 32px));
      margin: 0 auto;
      padding: 32px 0;
    }

    .hero {
      display: flex;
      justify-content: space-between;
      gap: 20px;
      align-items: flex-start;
      margin-bottom: 20px;
    }

    h1 {
      margin: 0 0 8px;
      font-size: clamp(24px, 4vw, 34px);
      letter-spacing: -0.03em;
    }

    .subtitle {
      margin: 0;
      color: var(--muted);
      max-width: 680px;
    }

    .status-card,
    .panel {
      background: rgba(255, 255, 255, 0.94);
      border: 1px solid rgba(217, 225, 236, 0.88);
      border-radius: 18px;
      box-shadow: var(--shadow);
    }

    .status-card {
      min-width: 248px;
      padding: 16px;
    }

    .status-line {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 700;
    }

    .dot {
      width: 10px;
      height: 10px;
      border-radius: 999px;
      background: var(--success);
      box-shadow: 0 0 0 4px rgba(22, 132, 91, 0.12);
    }

    .status-meta {
      display: grid;
      gap: 4px;
      margin-top: 12px;
      color: var(--muted);
      font-size: 13px;
    }

    .layout {
      display: grid;
      grid-template-columns: minmax(0, 1.5fr) minmax(320px, 0.9fr);
      gap: 20px;
      align-items: start;
    }

    .panel {
      padding: 22px;
    }

    .section-title {
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: center;
      margin-bottom: 18px;
    }

    .section-title h2 {
      margin: 0;
      font-size: 18px;
    }

    .hint {
      color: var(--muted);
      font-size: 13px;
    }

    .form-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }

    .field {
      display: grid;
      gap: 7px;
    }

    .field.full { grid-column: 1 / -1; }

    label {
      font-weight: 650;
    }

    .required::after {
      content: " *";
      color: var(--danger);
    }

    input {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 11px;
      background: #fff;
      color: var(--text);
      padding: 11px 12px;
      outline: none;
      transition: border-color .18s ease, box-shadow .18s ease;
      font: inherit;
    }

    input:focus {
      border-color: var(--primary);
      box-shadow: 0 0 0 4px rgba(23, 105, 224, 0.12);
    }

    input[aria-invalid="true"] {
      border-color: var(--danger);
      box-shadow: 0 0 0 4px rgba(192, 57, 43, 0.10);
    }

    .input-row {
      display: flex;
      gap: 8px;
    }

    .input-row input { min-width: 0; }

    .ghost-btn,
    .primary-btn,
    .secondary-btn {
      border: 0;
      border-radius: 11px;
      padding: 11px 14px;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
      white-space: nowrap;
      transition: transform .16s ease, background .16s ease, border-color .16s ease;
    }

    .ghost-btn {
      border: 1px solid var(--line);
      background: #fff;
      color: var(--text);
    }

    .primary-btn {
      background: var(--primary);
      color: #fff;
    }

    .primary-btn:hover { background: var(--primary-dark); }
    .ghost-btn:hover,
    .secondary-btn:hover { transform: translateY(-1px); }

    .secondary-btn {
      background: #eef4ff;
      color: var(--primary-dark);
    }

    .error {
      min-height: 18px;
      color: var(--danger);
      font-size: 12px;
    }

    .help {
      color: var(--muted);
      font-size: 12px;
    }

    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      justify-content: flex-end;
      margin-top: 20px;
      padding-top: 18px;
      border-top: 1px solid var(--line);
    }

    .notice {
      display: none;
      margin-bottom: 14px;
      border-radius: 12px;
      padding: 11px 12px;
      font-weight: 650;
    }

    .notice.show { display: block; }
    .notice.success { background: #e9f8f2; color: var(--success); }
    .notice.warn { background: #fff7e8; color: var(--warning); }

    .preview {
      display: grid;
      gap: 16px;
    }

    .kv {
      display: grid;
      gap: 10px;
      margin: 0;
    }

    .kv div {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      padding-bottom: 10px;
      border-bottom: 1px dashed var(--line);
    }

    .kv dt { color: var(--muted); }
    .kv dd { margin: 0; text-align: right; font-weight: 650; overflow-wrap: anywhere; }

    pre {
      margin: 0;
      overflow: auto;
      border-radius: 14px;
      background: var(--code-bg);
      color: #e6edf7;
      padding: 16px;
      font-size: 13px;
    }

    code { font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace; }

    .copy-row {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      margin-bottom: 10px;
    }

    @media (max-width: 860px) {
      .hero,
      .layout {
        grid-template-columns: 1fr;
        display: grid;
      }

      .status-card { min-width: 0; }
    }

    @media (max-width: 640px) {
      .page {
        width: min(100% - 20px, 1120px);
        padding: 18px 0;
      }

      .panel { padding: 16px; }
      .form-grid { grid-template-columns: 1fr; }
      .input-row { flex-direction: column; }
      .actions { justify-content: stretch; }
      .actions button { flex: 1 1 auto; }
      .kv div { display: grid; }
      .kv dd { text-align: left; }
    }
  </style>
</head>
<body>
  <main class="page">
    <header class="hero">
      <div>
        <h1>企业微信机器人配置管理</h1>
        <p class="subtitle">集中维护回调服务启动所需配置，支持敏感信息隐藏、即时校验、保存到本地浏览器与启动参数预览。</p>
      </div>
      <aside class="status-card" aria-label="配置状态">
        <div class="status-line"><span class="dot" id="statusDot"></span><span id="statusText">待检查</span></div>
        <div class="status-meta">
          <span>服务：{{ name }}</span>
          <span>监听：{{ host }}:{{ port }}</span>
          <span>回调：{{ path }}</span>
        </div>
      </aside>
    </header>

    <div class="layout">
      <section class="panel">
        <div class="section-title">
          <h2>基础配置</h2>
          <span class="hint">敏感配置仅保存在当前浏览器 localStorage</span>
        </div>
        <div class="notice" id="notice" role="status"></div>
        <form id="configForm" novalidate>
          <div class="form-grid">
            <div class="field">
              <label class="required" for="token">Token</label>
              <div class="input-row">
                <input id="token" name="token" type="password" autocomplete="off" data-sensitive required minlength="3" placeholder="企业微信回调 Token">
                <button class="ghost-btn" type="button" data-toggle="token">显示</button>
              </div>
              <span class="error" data-error="token"></span>
            </div>

            <div class="field">
              <label class="required" for="aesKey">AESKey</label>
              <div class="input-row">
                <input id="aesKey" name="aesKey" type="password" autocomplete="off" data-sensitive required pattern="^[A-Za-z0-9]{43}$" placeholder="43 位 EncodingAESKey">
                <button class="ghost-btn" type="button" data-toggle="aesKey">显示</button>
              </div>
              <span class="help">需为 43 位字母或数字</span>
              <span class="error" data-error="aesKey"></span>
            </div>

            <div class="field">
              <label for="corpId">CorpID</label>
              <input id="corpId" name="corpId" type="text" autocomplete="off" placeholder="可选，企业 ID">
              <span class="error" data-error="corpId"></span>
            </div>

            <div class="field">
              <label for="botKey">Bot Key</label>
              <div class="input-row">
                <input id="botKey" name="botKey" type="password" autocomplete="off" data-sensitive placeholder="Webhook URL 中的 key">
                <button class="ghost-btn" type="button" data-toggle="botKey">显示</button>
              </div>
              <span class="error" data-error="botKey"></span>
            </div>

            <div class="field">
              <label class="required" for="botName">机器人名称</label>
              <input id="botName" name="botName" type="text" required placeholder="如 jasonzxpan-test" value="{{ name }}">
              <span class="error" data-error="botName"></span>
            </div>

            <div class="field">
              <label class="required" for="host">监听地址</label>
              <input id="host" name="host" type="text" required placeholder="0.0.0.0 或 127.0.0.1" value="{{ host }}">
              <span class="error" data-error="host"></span>
            </div>

            <div class="field">
              <label class="required" for="port">端口</label>
              <input id="port" name="port" type="number" required min="1" max="65535" step="1" value="{{ port }}">
              <span class="error" data-error="port"></span>
            </div>

            <div class="field">
              <label class="required" for="callbackPath">回调路径</label>
              <input id="callbackPath" name="callbackPath" type="text" required pattern="^/.+" value="{{ path }}" placeholder="/wecom_bot">
              <span class="error" data-error="callbackPath"></span>
            </div>
          </div>

          <div class="actions">
            <button class="ghost-btn" type="button" id="resetBtn">重置</button>
            <button class="secondary-btn" type="button" id="fillDemoBtn">填入示例</button>
            <button class="primary-btn" type="submit">保存配置</button>
          </div>
        </form>
      </section>

      <aside class="panel preview">
        <div>
          <div class="section-title">
            <h2>启动参数预览</h2>
          </div>
          <dl class="kv">
            <div><dt>回调地址</dt><dd id="callbackUrl">-</dd></div>
            <div><dt>环境变量</dt><dd id="envCount">0 / 4</dd></div>
            <div><dt>配置完整度</dt><dd id="completeRate">0%</dd></div>
          </dl>
        </div>

        <div>
          <div class="copy-row">
            <span class="hint">Shell 启动前可导出：</span>
            <button class="ghost-btn" type="button" id="copyBtn">复制</button>
          </div>
          <pre><code id="commandPreview"></code></pre>
        </div>
      </aside>
    </div>
  </main>

  <script>
    const defaults = {
      token: "",
      aesKey: "",
      corpId: "{{ corp_id }}",
      botKey: "{{ bot_key }}",
      botName: "{{ name }}",
      host: "{{ host }}",
      port: "{{ port }}",
      callbackPath: "{{ path }}"
    };
    const storageKey = "wecom-bot-svr-config";
    const form = document.querySelector("#configForm");
    const notice = document.querySelector("#notice");
    const fields = [...form.elements].filter(el => el.name);

    function escapeShell(value) {
      return String(value || "").replace(/'/g, "'\\''");
    }

    function getConfig() {
      return Object.fromEntries(fields.map(field => [field.name, field.value.trim()]));
    }

    function setConfig(config) {
      fields.forEach(field => {
        field.value = config[field.name] ?? defaults[field.name] ?? "";
      });
      updatePreview();
    }

    function messageFor(field) {
      if (field.validity.valueMissing) return "该项必填";
      if (field.name === "aesKey" && field.validity.patternMismatch) return "AESKey 必须是 43 位字母或数字";
      if (field.name === "callbackPath" && field.validity.patternMismatch) return "路径必须以 / 开头";
      if (field.name === "port" && (field.validity.rangeUnderflow || field.validity.rangeOverflow)) return "端口范围为 1-65535";
      if (field.validity.tooShort) return `至少需要 ${field.minLength} 个字符`;
      return "";
    }

    function validate(showErrors = true) {
      let valid = true;
      fields.forEach(field => {
        const error = document.querySelector(`[data-error="${field.name}"]`);
        const msg = messageFor(field);
        field.setAttribute("aria-invalid", msg ? "true" : "false");
        if (error && showErrors) error.textContent = msg;
        if (msg) valid = false;
      });
      return valid;
    }

    function showNotice(text, type = "success") {
      notice.textContent = text;
      notice.className = `notice show ${type}`;
      window.clearTimeout(showNotice.timer);
      showNotice.timer = window.setTimeout(() => notice.className = "notice", 2800);
    }

    function updatePreview() {
      const config = getConfig();
      const origin = `${config.host || "0.0.0.0"}:${config.port || ""}`;
      const callbackPath = config.callbackPath || "/wecom_bot";
      const callbackUrl = `http://${origin}${callbackPath}`;
      const envValues = [config.token, config.aesKey, config.corpId, config.botKey].filter(Boolean).length;
      const requiredValues = [config.token, config.aesKey, config.botName, config.host, config.port, config.callbackPath].filter(Boolean).length;
      const completeRate = Math.round((requiredValues / 6) * 100);
      const isValid = validate(false);

      document.querySelector("#callbackUrl").textContent = callbackUrl;
      document.querySelector("#envCount").textContent = `${envValues} / 4`;
      document.querySelector("#completeRate").textContent = `${completeRate}%`;
      document.querySelector("#statusText").textContent = isValid ? "配置可用" : "配置待完善";
      document.querySelector("#statusDot").style.background = isValid ? "var(--success)" : "var(--warning)";

      document.querySelector("#commandPreview").textContent = [
        `export WX_BOT_TOKEN='${escapeShell(config.token)}'`,
        `export WX_BOT_AES_KEY='${escapeShell(config.aesKey)}'`,
        `export WX_BOT_CORP_ID='${escapeShell(config.corpId)}'`,
        `export WX_BOT_KEY='${escapeShell(config.botKey)}'`,
        `python3 demo.py  # ${config.botName || "bot"} listens on ${callbackUrl}`
      ].join("\n");
    }

    document.querySelectorAll("[data-toggle]").forEach(button => {
      button.addEventListener("click", () => {
        const input = document.querySelector(`#${button.dataset.toggle}`);
        const visible = input.type === "text";
        input.type = visible ? "password" : "text";
        button.textContent = visible ? "显示" : "隐藏";
      });
    });

    fields.forEach(field => {
      field.addEventListener("input", updatePreview);
      field.addEventListener("blur", () => validate(true));
    });

    form.addEventListener("submit", event => {
      event.preventDefault();
      if (!validate(true)) {
        showNotice("请先修正表单中的错误项", "warn");
        return;
      }
      localStorage.setItem(storageKey, JSON.stringify(getConfig()));
      showNotice("配置已保存到当前浏览器");
    });

    document.querySelector("#resetBtn").addEventListener("click", () => {
      localStorage.removeItem(storageKey);
      setConfig(defaults);
      showNotice("已恢复为服务当前配置");
    });

    document.querySelector("#fillDemoBtn").addEventListener("click", () => {
      setConfig({
        ...defaults,
        token: "demo-token",
        aesKey: "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFG",
        botKey: "demo-webhook-key"
      });
      showNotice("已填入示例配置，请替换为真实值", "warn");
    });

    document.querySelector("#copyBtn").addEventListener("click", async () => {
      await navigator.clipboard.writeText(document.querySelector("#commandPreview").textContent);
      showNotice("启动参数已复制");
    });

    try {
      setConfig({ ...defaults, ...JSON.parse(localStorage.getItem(storageKey) || "{}") });
    } catch (_) {
      setConfig(defaults);
    }
  </script>
</body>
</html>
"""


class WecomBotServer(object):
    def __init__(self, name, host, port, path, token=None, aes_key=None, corp_id=None, bot_key=None,
                 active_msg_path="/active_send", health_check_path="/health", config_page_path="/config",
                 log_level=None):
        """
        :param name:
        :param host:
        :param port:
        :param path:
        :param token:
        :param aes_key:
        :param corp_id:
        :param bot_key:
        :param active_msg_path: 主动发送消息的路径
        :param health_check_path: 健康检查和运行状态查询路径
        :param config_page_path: 配置管理页面路径，设置为 None 可关闭
        :param log_level: 日志级别，可通过 WX_BOT_LOG_LEVEL 环境变量配置
        """
        self.host = host
        self.port = port
        self.path = path
        self.active_msg_path = active_msg_path
        self.health_check_path = health_check_path
        self.config_page_path = config_page_path
        self._bot_key = bot_key if bot_key is not None else os.getenv("WX_BOT_KEY")
        self._token = token if token is not None else os.getenv("WX_BOT_TOKEN")
        self._aes_key = aes_key if aes_key is not None else os.getenv("WX_BOT_AES_KEY")
        self._corp_id = corp_id if corp_id is not None else os.getenv("WX_BOT_CORP_ID", default="")
        self._app = Flask(name)
        self._message_handler = None
        self._event_handler = None
        self._error_handler = None
        self.name = name
        self.logger = logging.getLogger()
        self._log_level = _resolve_log_level(log_level if log_level is not None else os.getenv("WX_BOT_LOG_LEVEL"))
        if self._log_level is not None:
            self.logger.setLevel(self._log_level)
        self._started_at = datetime.now(timezone.utc)

    def set_message_handler(self, handler):
        self._message_handler = handler

    def set_event_handler(self, handler):
        self._event_handler = handler

    def set_error_handler(self, handler):
        self._error_handler = handler

    def set_flask_error_handler(self, handler):
        self._app.errorhandler(Exception)(handler)

    def run(self):
        if self._message_handler is None:
            raise Exception("message handler is not set")
        if self._event_handler is None:
            raise Exception("event handler is not set")
        self._app.get(self.path)(self.handle_bot_call_get)
        self._app.post(self.path)(self.handle_bot_call_post)
        self._app.post(self.active_msg_path)(self.handle_active_send)
        self._app.get(self.health_check_path)(self.handle_health_check)
        if self.config_page_path:
            self._app.get(self.config_page_path)(self.handle_config_page)
        self._app.run(host=self.host, port=self.port)

    def get_runtime_status(self):
        now = datetime.now(timezone.utc)
        return {
            "status": "ok",
            "name": self.name,
            "version": _get_package_version(),
            "host": self.host,
            "port": self.port,
            "callback_path": self.path,
            "active_msg_path": self.active_msg_path,
            "health_check_path": self.health_check_path,
            "config_page_path": self.config_page_path,
            "log_level": logging.getLevelName(self.logger.getEffectiveLevel()),
            "started_at": self._started_at.isoformat(),
            "uptime_seconds": int((now - self._started_at).total_seconds()),
        }

    def handle_health_check(self):
        return jsonify(self.get_runtime_status())

    def handle_config_page(self):
        return render_template_string(
            CONFIG_PAGE_TEMPLATE,
            name=self.name,
            host=self.host,
            port=self.port,
            path=self.path,
            corp_id=self._corp_id or "",
            bot_key=self._bot_key or "",
        )

    def handle_active_send(self):
        # 避免外网直接访问：判断来源IP如果非本地地址，直接返回
        if request.remote_addr != "127.0.0.1":
            return "Invalid request"

        # 获取请求参数
        params = request.values
        msg_type = params.get("msg_type")
        chat_id = params.get("chat_id")
        if msg_type == "file":
            file_path = params.get("file_path")
            send_ret = self.send_file(chat_id, file_path)
        elif msg_type == "markdown":
            content = params.get("content")
            send_ret = self.send_markdown(chat_id, content)
        elif msg_type == "text":
            content = params.get("content")
            send_ret = self.send_text(chat_id, content)
        elif msg_type == "image":
            base64_image_data = params.get("base64_image_data")
            md5 = params.get("md5")
            send_ret = self.send_encoded_image(chat_id, base64_image_data, md5)
        elif msg_type == "news":
            title = params.get("title")
            description = params.get("description")
            url = params.get("url")
            pic_url = params.get("pic_url")
            send_ret = self.send_news(chat_id, title, description, url, pic_url)
        else:
            return "Invalid msg_type"

        return "发送消息结果：" + send_ret

    def get_crypto_obj(self):
        return WXBizMsgCrypt(self._token, self._aes_key, self._corp_id, channel=WxChannel_Wecom)

    def handle_bot_call_get(self):
        # 获取请求参数
        params = request.args
        msg_signature = params.get("msg_signature")
        timestamp = params.get("timestamp")
        nonce = params.get("nonce")
        encrypted_echo_str = params.get("echostr")
        wx_cpt = self.get_crypto_obj()
        ret, decrypted_echo_str = wx_cpt.VerifyURL(msg_signature, timestamp, nonce, encrypted_echo_str)
        if ret != 0:
            return None
        return decrypted_echo_str

    def handle_bot_call_post(self):
        # 获取请求参数
        params = request.args
        msg_signature = params.get("msg_signature")
        timestamp = params.get("timestamp")
        nonce = params.get("nonce")
        wx_cpt = self.get_crypto_obj()

        # 解密出明文的echostr
        ret, msg = wx_cpt.DecryptMsg(request.data, msg_signature, timestamp, nonce)
        self.logger.info(f"decrypted msg: {msg.decode()}")
        if ret != 0:
            if self._error_handler:
                self._error_handler(ret)
            else:
                return None
            # 获取所有的查询参数

        # 解密后的数据是xml格式，用python的标准库xml.etree.cElementTree可以解析
        xml_tree = ET.fromstring(msg)
        msg = ReqMsg.create_msg(xml_tree)
        if msg.msg_type == 'event':
            rsp_msg = self._event_handler(msg)
        else:  # 消息
            if msg.msg_type == 'text' and msg.chat_type == 'group':
                msg.content = msg.content.replace(f"@{self.name}", "")
            if len(inspect.signature(self._message_handler).parameters) == 2:
                rsp_msg = self._message_handler(msg, self)
            else:  # 兼容旧版本
                rsp_msg = self._message_handler(msg)

        nonce = params.get("nonce")
        ret, rsp = wx_cpt.EncryptMsg(rsp_msg.dump_xml(), nonce, timestamp)
        if ret != 0:
            print("err: encrypt fail: " + str(ret))
        return rsp

    def upload_file(self, file_path):
        filename = os.path.basename(file_path)
        if not self._bot_key:
            self.logger.warning("upload file failed: bot_key is not configured")
            return None
        try:
            # 打开文件并上传
            with open(file_path, 'rb') as file:
                files = {'file': (filename, file)}
                response = requests.post(
                    url=f'https://qyapi.weixin.qq.com/cgi-bin/webhook/upload_media?key={self._bot_key}&type=file',
                    files=files,
                    timeout=10)
                # 检查响应
                response_data = response.json()
                if response.status_code == 200 and response_data.get("errcode") == 0:
                    return response_data.get('media_id')
                self.logger.warning("upload file failed: status_code=%s, response=%s", response.status_code, response_data)
                return None
        except Exception:
            self.logger.exception("upload file failed: file_path=%s", file_path)
            return None

    def proactively_send(self, chat_id, msg_type, msg_type_name, msg_data):
        """"""
        if not self._bot_key:
            self.logger.warning("send %s failed: bot_key is not configured", msg_type_name)
            return f"发送{msg_type_name}失败"
        try:
            payload = {
                "chatid": chat_id,
                "msgtype": msg_type,
            }
            payload.update(msg_data)

            r = requests.post(url=f'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={self._bot_key}',
                              json=payload,
                              timeout=10)
            response_data = r.json()
            if r.status_code == 200 and response_data.get("errcode") == 0:
                return f"发送{msg_type_name}成功"
            self.logger.warning("send %s failed: status_code=%s, response=%s", msg_type_name, r.status_code, response_data)
            return f"发送{msg_type_name}失败"
        except Exception:
            self.logger.exception("send %s failed: chat_id=%s, msg_type=%s", msg_type_name, chat_id, msg_type)
            return f"发送{msg_type_name}失败"

    def send_file(self, chat_id, file_path):
        media_id = self.upload_file(file_path)
        if media_id is None:
            return "上传文件失败"

        return self.proactively_send(chat_id, "file", "文件", {"file": {"media_id": media_id}})

    def send_markdown(self, chat_id, content):
        return self.proactively_send(chat_id, "markdown", "Markdown", {"markdown": {"content": content}})

    def send_text(self, chat_id, content, mentioned_list=None, mentioned_mobile_list=None):
        msg_data = {
            "text": {
                "content": content,
            }
        }
        if mentioned_list is not None:
            msg_data["text"]["mentioned_list"] = mentioned_list
        if mentioned_mobile_list is not None:
            msg_data["text"]["mentioned_mobile_list"] = mentioned_mobile_list
        return self.proactively_send(chat_id, "text", "文本", msg_data)

    def send_encoded_image(self, chat_id, base64_image_data, md5):
        return self.proactively_send(chat_id, "image", "图片", {"image": {"base64": base64_image_data, "md5": md5}})

    def send_news(self, chat_id, title, description, url, pic_url):
        return self.proactively_send(chat_id, "news", "图文", {"news": {"articles": [
            {
                "title": title,
                "description": description,
                "url": url,
                "picurl": pic_url
            }
        ]}})