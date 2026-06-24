import inspect
import logging
import os
import re
import xml.etree.cElementTree as ET
from datetime import datetime, timezone

import requests
from flask import Flask, jsonify, render_template_string, request
from wx_crypt import WXBizMsgCrypt, WxChannel_Wecom

from .req_msg import ReqMsg
from .version import get_version


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


CONFIG_PAGE_TEMPLATE = r"""
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ config.name or "企业微信机器人" }} · 配置管理</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f8fb;
      --surface: #ffffff;
      --surface-soft: #f1f5f9;
      --text: #172033;
      --muted: #64748b;
      --line: #d9e2ec;
      --accent: #1677ff;
      --accent-dark: #0958d9;
      --ok: #15803d;
      --warn: #b45309;
      --danger: #b91c1c;
      --shadow: 0 18px 50px rgba(15, 23, 42, 0.08);
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.5;
    }

    button,
    input {
      font: inherit;
    }

    .page {
      width: min(1180px, calc(100% - 32px));
      margin: 0 auto;
      padding: 28px 0 40px;
    }

    .topbar {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 20px;
      margin-bottom: 22px;
    }

    .eyebrow {
      margin: 0 0 6px;
      color: var(--muted);
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 0;
    }

    h1 {
      margin: 0;
      font-size: clamp(24px, 4vw, 34px);
      letter-spacing: 0;
      line-height: 1.15;
    }

    .subtitle {
      margin: 10px 0 0;
      color: var(--muted);
      max-width: 720px;
    }

    .status-pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      min-height: 34px;
      padding: 6px 12px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: var(--surface);
      color: var(--muted);
      white-space: nowrap;
      box-shadow: 0 8px 22px rgba(15, 23, 42, 0.04);
    }

    .dot {
      width: 9px;
      height: 9px;
      border-radius: 50%;
      background: var(--warn);
    }

    .status-pill.ready .dot {
      background: var(--ok);
    }

    .layout {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 360px;
      gap: 20px;
      align-items: start;
    }

    .panel {
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
    }

    .panel-header {
      padding: 20px 22px 14px;
      border-bottom: 1px solid var(--line);
    }

    .panel-title {
      margin: 0;
      font-size: 17px;
      font-weight: 750;
      letter-spacing: 0;
    }

    .panel-note {
      margin: 6px 0 0;
      color: var(--muted);
      font-size: 13px;
    }

    form {
      padding: 22px;
    }

    .section {
      margin-bottom: 26px;
    }

    .section:last-child {
      margin-bottom: 0;
    }

    .section-title {
      margin: 0 0 14px;
      font-size: 14px;
      font-weight: 800;
      color: #334155;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }

    .field {
      min-width: 0;
    }

    .field.full {
      grid-column: 1 / -1;
    }

    label {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 7px;
      color: #334155;
      font-size: 13px;
      font-weight: 700;
    }

    .required {
      color: var(--danger);
    }

    .input-wrap {
      display: flex;
      align-items: stretch;
      min-height: 42px;
      border: 1px solid var(--line);
      border-radius: 7px;
      background: #fff;
      transition: border-color 0.16s, box-shadow 0.16s;
      overflow: hidden;
    }

    .input-wrap:focus-within {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(22, 119, 255, 0.12);
    }

    input {
      width: 100%;
      min-width: 0;
      border: 0;
      outline: 0;
      padding: 10px 12px;
      background: transparent;
      color: var(--text);
    }

    input::placeholder {
      color: #9aa8ba;
    }

    .toggle {
      width: 44px;
      min-width: 44px;
      border: 0;
      border-left: 1px solid var(--line);
      background: var(--surface-soft);
      color: #475569;
      cursor: pointer;
    }

    .toggle:hover {
      color: var(--accent-dark);
      background: #eaf2ff;
    }

    .error {
      min-height: 18px;
      margin: 5px 0 0;
      color: var(--danger);
      font-size: 12px;
    }

    .field.invalid .input-wrap {
      border-color: #fca5a5;
    }

    .actions {
      display: flex;
      gap: 10px;
      justify-content: flex-end;
      border-top: 1px solid var(--line);
      padding-top: 18px;
      margin-top: 8px;
    }

    .btn {
      min-height: 40px;
      border-radius: 7px;
      border: 1px solid var(--line);
      padding: 8px 14px;
      background: #fff;
      color: #334155;
      font-weight: 750;
      cursor: pointer;
    }

    .btn:hover {
      border-color: #b7c4d4;
      background: #f8fafc;
    }

    .btn.primary {
      border-color: var(--accent);
      background: var(--accent);
      color: #fff;
    }

    .btn.primary:hover {
      border-color: var(--accent-dark);
      background: var(--accent-dark);
    }

    .side {
      display: grid;
      gap: 16px;
      position: sticky;
      top: 16px;
    }

    .side .panel {
      box-shadow: 0 14px 40px rgba(15, 23, 42, 0.06);
    }

    .side-body {
      padding: 18px;
    }

    .metric {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 10px;
      align-items: center;
      padding: 10px 0;
      border-bottom: 1px solid var(--line);
      color: var(--muted);
      font-size: 13px;
    }

    .metric:first-child {
      padding-top: 0;
    }

    .metric:last-child {
      border-bottom: 0;
      padding-bottom: 0;
    }

    .metric strong {
      color: var(--text);
      font-size: 13px;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      padding: 3px 8px;
      border-radius: 999px;
      background: #fff7ed;
      color: var(--warn);
      font-size: 12px;
      font-weight: 800;
    }

    .badge.ok {
      background: #ecfdf5;
      color: var(--ok);
    }

    .badge.danger {
      background: #fef2f2;
      color: var(--danger);
    }

    pre {
      margin: 0;
      padding: 14px;
      min-height: 176px;
      overflow: auto;
      border-radius: 7px;
      border: 1px solid var(--line);
      background: #0f172a;
      color: #dbeafe;
      font-size: 12px;
      line-height: 1.6;
      white-space: pre-wrap;
      word-break: break-word;
    }

    .toast {
      position: fixed;
      right: 20px;
      bottom: 20px;
      max-width: min(360px, calc(100% - 40px));
      padding: 12px 14px;
      border-radius: 7px;
      background: #102033;
      color: #fff;
      box-shadow: var(--shadow);
      opacity: 0;
      transform: translateY(10px);
      pointer-events: none;
      transition: opacity 0.18s, transform 0.18s;
      z-index: 20;
    }

    .toast.show {
      opacity: 1;
      transform: translateY(0);
    }

    @media (max-width: 900px) {
      .layout {
        grid-template-columns: 1fr;
      }

      .side {
        position: static;
      }
    }

    @media (max-width: 640px) {
      .page {
        width: min(100% - 20px, 1180px);
        padding-top: 18px;
      }

      .topbar {
        display: grid;
      }

      .status-pill {
        width: 100%;
        justify-content: center;
      }

      form,
      .panel-header,
      .side-body {
        padding-left: 14px;
        padding-right: 14px;
      }

      .grid {
        grid-template-columns: 1fr;
      }

      .actions {
        flex-direction: column-reverse;
      }

      .btn {
        width: 100%;
      }
    }
  </style>
</head>
<body>
  <main class="page">
    <header class="topbar">
      <div>
        <p class="eyebrow">WeCom Bot Callback Server</p>
        <h1>配置管理</h1>
        <p class="subtitle">集中维护企业微信机器人回调服务的运行参数、密钥和启动预览。</p>
      </div>
      <div class="status-pill" id="readyPill"><span class="dot"></span><span id="readyText">待校验</span></div>
    </header>

    <div class="layout">
      <section class="panel">
        <div class="panel-header">
          <h2 class="panel-title">服务配置</h2>
          <p class="panel-note">保存后会更新当前进程内的配置；监听地址、端口和路由变更通常需要重启后完全生效。</p>
        </div>

        <form id="configForm" novalidate>
          <div class="section">
            <h3 class="section-title">机器人身份</h3>
            <div class="grid">
              <div class="field" data-field="name">
                <label for="name">机器人名称 <span class="required">*</span></label>
                <div class="input-wrap"><input id="name" name="name" autocomplete="off" placeholder="dev-helper"></div>
                <p class="error"></p>
              </div>

              <div class="field" data-field="corp_id">
                <label for="corp_id">CorpID</label>
                <div class="input-wrap"><input id="corp_id" name="corp_id" autocomplete="off" placeholder="wwxxxxxxxxxxxxxxxx"></div>
                <p class="error"></p>
              </div>

              <div class="field full" data-field="bot_key">
                <label for="bot_key">Bot Key</label>
                <div class="input-wrap">
                  <input id="bot_key" name="bot_key" type="password" autocomplete="off" placeholder="Webhook URL 中的 key 参数">
                  <button class="toggle" type="button" data-toggle="bot_key" aria-label="显示或隐藏 Bot Key">眼</button>
                </div>
                <p class="error"></p>
              </div>
            </div>
          </div>

          <div class="section">
            <h3 class="section-title">回调安全</h3>
            <div class="grid">
              <div class="field" data-field="token">
                <label for="token">Token <span class="required">*</span></label>
                <div class="input-wrap">
                  <input id="token" name="token" type="password" autocomplete="off" placeholder="企业微信回调 Token">
                  <button class="toggle" type="button" data-toggle="token" aria-label="显示或隐藏 Token">眼</button>
                </div>
                <p class="error"></p>
              </div>

              <div class="field" data-field="aes_key">
                <label for="aes_key">AESKey <span class="required">*</span></label>
                <div class="input-wrap">
                  <input id="aes_key" name="aes_key" type="password" autocomplete="off" placeholder="43 位 EncodingAESKey">
                  <button class="toggle" type="button" data-toggle="aes_key" aria-label="显示或隐藏 AESKey">眼</button>
                </div>
                <p class="error"></p>
              </div>
            </div>
          </div>

          <div class="section">
            <h3 class="section-title">监听设置</h3>
            <div class="grid">
              <div class="field" data-field="host">
                <label for="host">监听地址 <span class="required">*</span></label>
                <div class="input-wrap"><input id="host" name="host" autocomplete="off" placeholder="0.0.0.0"></div>
                <p class="error"></p>
              </div>

              <div class="field" data-field="port">
                <label for="port">端口 <span class="required">*</span></label>
                <div class="input-wrap"><input id="port" name="port" inputmode="numeric" autocomplete="off" placeholder="5001"></div>
                <p class="error"></p>
              </div>

              <div class="field full" data-field="path">
                <label for="path">回调路径 <span class="required">*</span></label>
                <div class="input-wrap"><input id="path" name="path" autocomplete="off" placeholder="/wecom_bot"></div>
                <p class="error"></p>
              </div>
            </div>
          </div>

          <div class="actions">
            <button class="btn" type="button" id="resetBtn">重置</button>
            <button class="btn primary" type="submit">保存配置</button>
          </div>
        </form>
      </section>

      <aside class="side">
        <section class="panel">
          <div class="panel-header">
            <h2 class="panel-title">配置状态</h2>
          </div>
          <div class="side-body" id="statusList"></div>
        </section>

        <section class="panel">
          <div class="panel-header">
            <h2 class="panel-title">启动参数预览</h2>
          </div>
          <div class="side-body">
            <pre id="preview"></pre>
          </div>
        </section>
      </aside>
    </div>
  </main>

  <div class="toast" id="toast"></div>

  <script>
    const initialPayload = {{ payload | tojson }};
    const apiPath = initialPayload.api_path;
    const fields = ["name", "host", "port", "path", "token", "aes_key", "corp_id", "bot_key"];
    const form = document.getElementById("configForm");
    const readyPill = document.getElementById("readyPill");
    const readyText = document.getElementById("readyText");
    const statusList = document.getElementById("statusList");
    const preview = document.getElementById("preview");
    const toast = document.getElementById("toast");
    let savedConfig = { ...initialPayload.config };
    let toastTimer = null;

    function getValues() {
      return fields.reduce((data, field) => {
        data[field] = document.getElementById(field).value.trim();
        return data;
      }, {});
    }

    function setValues(data) {
      fields.forEach((field) => {
        document.getElementById(field).value = data[field] ?? "";
      });
      validateAndRender();
    }

    function validate(data) {
      const errors = {};
      const pathPattern = /^\/[A-Za-z0-9/_\-.]*$/;
      const hostPattern = /^[A-Za-z0-9._:-]+$/;
      const aesPattern = /^[A-Za-z0-9_-]{43}$/;
      const port = Number(data.port);

      if (!data.name) errors.name = "请输入机器人名称";
      if (!data.host) errors.host = "请输入监听地址";
      else if (!hostPattern.test(data.host)) errors.host = "监听地址包含不支持的字符";
      if (!data.port) errors.port = "请输入端口";
      else if (!Number.isInteger(port) || port < 1 || port > 65535) errors.port = "端口范围为 1-65535";
      if (!data.path) errors.path = "请输入回调路径";
      else if (!pathPattern.test(data.path)) errors.path = "路径需以 / 开头，可包含字母、数字、_、-、. 和 /";
      if (!data.token) errors.token = "请输入 Token";
      if (!data.aes_key) errors.aes_key = "请输入 AESKey";
      else if (!aesPattern.test(data.aes_key)) errors.aes_key = "AESKey 需为 43 位字母、数字、_ 或 -";
      if (data.corp_id && !/^[A-Za-z0-9_-]+$/.test(data.corp_id)) errors.corp_id = "CorpID 仅支持字母、数字、_ 和 -";
      if (data.bot_key && !/^[A-Za-z0-9_-]+$/.test(data.bot_key)) errors.bot_key = "Bot Key 仅支持字母、数字、_ 和 -";

      return errors;
    }

    function showErrors(errors) {
      fields.forEach((field) => {
        const node = document.querySelector(`[data-field="${field}"]`);
        const error = node.querySelector(".error");
        const message = errors[field] || "";
        node.classList.toggle("invalid", Boolean(message));
        error.textContent = message;
      });
    }

    function renderStatus(data, errors) {
      const isReady = Object.keys(errors).length === 0;
      readyPill.classList.toggle("ready", isReady);
      readyText.textContent = isReady ? "配置可启动" : "配置需完善";

      const items = [
        ["Token", data.token ? "已配置" : "缺失", data.token ? "ok" : "danger"],
        ["AESKey", data.aes_key ? "已配置" : "缺失", data.aes_key ? "ok" : "danger"],
        ["CorpID", data.corp_id ? "已配置" : "可选", data.corp_id ? "ok" : ""],
        ["Bot Key", data.bot_key ? "已配置" : "可选", data.bot_key ? "ok" : ""],
        ["监听", `${data.host || "-"}:${data.port || "-"}`, errors.host || errors.port ? "danger" : "ok"],
        ["回调路径", data.path || "-", errors.path ? "danger" : "ok"],
      ];

      statusList.innerHTML = items.map(([label, value, type]) => `
        <div class="metric">
          <span>${label}</span>
          <strong><span class="badge ${type}">${value}</span></strong>
        </div>
      `).join("");
    }

    function mask(value, visible = 4) {
      if (!value) return "";
      if (value.length <= visible) return "*".repeat(value.length);
      return `${"*".repeat(Math.max(4, value.length - visible))}${value.slice(-visible)}`;
    }

    function shellQuote(value) {
      return `'${String(value || "").replaceAll("'", "'\\''")}'`;
    }

    function renderPreview(data) {
      const callbackUrl = `http://${data.host || "0.0.0.0"}:${data.port || "5001"}${data.path || "/wecom_bot"}`;
      const envLines = [
        `WX_BOT_TOKEN=${shellQuote(mask(data.token))}`,
        `WX_BOT_AES_KEY=${shellQuote(mask(data.aes_key))}`,
        data.corp_id ? `WX_BOT_CORP_ID=${shellQuote(data.corp_id)}` : null,
        data.bot_key ? `WX_BOT_KEY=${shellQuote(mask(data.bot_key))}` : null,
      ].filter(Boolean).join(" \\\n  ");

      preview.textContent = `${envLines} \\\npython3 demo.py\n\n回调地址: ${callbackUrl}\n构造参数: WecomBotServer(${shellQuote(data.name)}, ${shellQuote(data.host)}, ${data.port || "5001"}, path=${shellQuote(data.path)})`;
    }

    function validateAndRender() {
      const data = getValues();
      const errors = validate(data);
      showErrors(errors);
      renderStatus(data, errors);
      renderPreview(data);
      return { data, errors };
    }

    function showToast(message) {
      toast.textContent = message;
      toast.classList.add("show");
      clearTimeout(toastTimer);
      toastTimer = setTimeout(() => toast.classList.remove("show"), 2600);
    }

    async function saveConfig(data) {
      const response = await fetch(apiPath, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      const payload = await response.json();
      if (!response.ok) {
        showErrors(payload.errors || {});
        throw new Error(payload.message || "配置保存失败");
      }
      savedConfig = { ...payload.config };
      setValues(savedConfig);
      return payload;
    }

    fields.forEach((field) => {
      document.getElementById(field).addEventListener("input", validateAndRender);
    });

    document.querySelectorAll("[data-toggle]").forEach((button) => {
      button.addEventListener("click", () => {
        const input = document.getElementById(button.dataset.toggle);
        const showing = input.type === "text";
        input.type = showing ? "password" : "text";
        button.textContent = showing ? "眼" : "隐";
      });
    });

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const { data, errors } = validateAndRender();
      if (Object.keys(errors).length > 0) {
        showToast("请先修正表单中的错误");
        return;
      }
      try {
        await saveConfig(data);
        showToast("配置已保存到当前服务进程");
      } catch (error) {
        showToast(error.message);
      }
    });

    document.getElementById("resetBtn").addEventListener("click", async () => {
      try {
        const response = await fetch(`${apiPath}?reset=1`, { method: "POST" });
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.message || "重置失败");
        savedConfig = { ...payload.config };
        setValues(savedConfig);
        showToast("配置已重置");
      } catch (error) {
        setValues(savedConfig);
        showToast(error.message || "已恢复为上次保存的配置");
      }
    });

    setValues(savedConfig);
  </script>
</body>
</html>
"""


class WecomBotServer(object):
    def __init__(self, name, host, port, path, token=None, aes_key=None, corp_id=None, bot_key=None,
                 active_msg_path="/active_send", status_path="/status", config_path="/config",
                 config_api_path="/config/api"):
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
        :param status_path: 运行状态检查路径，传入 None 可关闭
        :param config_path: 配置管理页面路径，传入 None 可关闭
        :param config_api_path: 配置管理接口路径，传入 None 可关闭
        """
        self.host = host
        self.port = port
        self.path = path
        self.active_msg_path = active_msg_path
        self.status_path = status_path
        self.config_path = config_path
        self.config_api_path = config_api_path
        self._bot_key = bot_key if bot_key is not None else os.getenv("WX_BOT_KEY")
        self._token = token if token is not None else os.getenv("WX_BOT_TOKEN")
        self._aes_key = aes_key if aes_key is not None else os.getenv("WX_BOT_AES_KEY")
        self._corp_id = corp_id if corp_id is not None else os.getenv("WX_BOT_CORP_ID", default="")
        self._initial_config = None
        self._app = Flask(name)
        self._message_handler = None
        self._event_handler = None
        self._error_handler = None
        self.name = name
        self.logger = logging.getLogger()
        self._initialized_at = datetime.now(timezone.utc)
        self._routes_registered = False
        self._initial_config = self._get_config_values()

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
        self._register_routes()
        self._app.run(host=self.host, port=self.port)

    def _register_routes(self):
        if self._routes_registered:
            return
        self._app.get(self.path)(self.handle_bot_call_get)
        self._app.post(self.path)(self.handle_bot_call_post)
        self._app.post(self.active_msg_path)(self.handle_active_send)
        if self.status_path is not None:
            self._app.get(self.status_path)(self.handle_status)
        if self.config_path is not None:
            self._app.get(self.config_path)(self.handle_config_page)
        if self.config_api_path is not None:
            self._app.get(self.config_api_path)(self.handle_config_api_get)
            self._app.post(self.config_api_path)(self.handle_config_api_post)
        self._routes_registered = True

    def _get_config_status(self):
        return {
            "token": bool(self._token),
            "aes_key": bool(self._aes_key),
            "corp_id": self._corp_id != "",
            "bot_key": bool(self._bot_key),
        }

    def _get_missing_required_config(self):
        config = self._get_config_status()
        required_config = ("token", "aes_key")
        return [key for key in required_config if not config[key]]

    def get_status(self):
        now = datetime.now(timezone.utc)
        missing_required_config = self._get_missing_required_config()
        return {
            "status": "ok",
            "name": self.name,
            "version": get_version(),
            "initialized_at": self._initialized_at.isoformat(),
            "current_time": now.isoformat(),
            "uptime_seconds": int((now - self._initialized_at).total_seconds()),
            "host": self.host,
            "port": self.port,
            "paths": {
                "callback": self.path,
                "active_send": self.active_msg_path,
                "status": self.status_path,
                "config": self.config_path,
                "config_api": self.config_api_path,
            },
            "handlers": {
                "message": self._message_handler is not None,
                "event": self._event_handler is not None,
                "error": self._error_handler is not None,
            },
            "config": self._get_config_status(),
            "config_errors": missing_required_config,
            "ready": len(missing_required_config) == 0,
        }

    def handle_status(self):
        return jsonify(self.get_status())

    def _get_config_values(self):
        return {
            "name": self.name,
            "host": self.host,
            "port": self.port,
            "path": self.path,
            "token": self._token or "",
            "aes_key": self._aes_key or "",
            "corp_id": self._corp_id or "",
            "bot_key": self._bot_key or "",
        }

    @staticmethod
    def _normalize_path(value):
        if value == "":
            return value
        return value if value.startswith("/") else f"/{value}"

    def _validate_config_values(self, values):
        errors = {}
        path_pattern = re.compile(r"^/[A-Za-z0-9/_\-.]*$")
        host_pattern = re.compile(r"^[A-Za-z0-9._:-]+$")
        aes_pattern = re.compile(r"^[A-Za-z0-9_-]{43}$")

        if not values["name"]:
            errors["name"] = "请输入机器人名称"
        if not values["host"]:
            errors["host"] = "请输入监听地址"
        elif not host_pattern.match(values["host"]):
            errors["host"] = "监听地址包含不支持的字符"
        try:
            port = int(values["port"])
            if port < 1 or port > 65535:
                errors["port"] = "端口范围为 1-65535"
        except (TypeError, ValueError):
            errors["port"] = "端口范围为 1-65535"
        if not values["path"]:
            errors["path"] = "请输入回调路径"
        elif not path_pattern.match(values["path"]):
            errors["path"] = "路径需以 / 开头，可包含字母、数字、_、-、. 和 /"
        if not values["token"]:
            errors["token"] = "请输入 Token"
        if not values["aes_key"]:
            errors["aes_key"] = "请输入 AESKey"
        elif not aes_pattern.match(values["aes_key"]):
            errors["aes_key"] = "AESKey 需为 43 位字母、数字、_ 或 -"
        if values["corp_id"] and not re.match(r"^[A-Za-z0-9_-]+$", values["corp_id"]):
            errors["corp_id"] = "CorpID 仅支持字母、数字、_ 和 -"
        if values["bot_key"] and not re.match(r"^[A-Za-z0-9_-]+$", values["bot_key"]):
            errors["bot_key"] = "Bot Key 仅支持字母、数字、_ 和 -"
        return errors

    def _coerce_config_values(self, raw_values):
        current = self._get_config_values()
        values = {}
        for key in current:
            value = raw_values.get(key, current[key])
            values[key] = str(value).strip()
        values["path"] = self._normalize_path(values["path"])
        return values

    def _apply_config_values(self, values):
        self.name = values["name"]
        self.host = values["host"]
        self.port = int(values["port"])
        self.path = values["path"]
        self._token = values["token"]
        self._aes_key = values["aes_key"]
        self._corp_id = values["corp_id"]
        self._bot_key = values["bot_key"]

    def _config_payload(self):
        return {
            "config": self._get_config_values(),
            "status": self.get_status(),
            "api_path": self.config_api_path,
        }

    def handle_config_page(self):
        return render_template_string(CONFIG_PAGE_TEMPLATE, config=self._get_config_values(), payload=self._config_payload())

    def handle_config_api_get(self):
        return jsonify(self._config_payload())

    def handle_config_api_post(self):
        if request.args.get("reset") == "1":
            self._apply_config_values(self._initial_config)
            return jsonify(self._config_payload())

        values = self._coerce_config_values(request.get_json(silent=True) or {})
        errors = self._validate_config_values(values)
        if errors:
            return jsonify({"message": "配置校验失败", "errors": errors, "config": values}), 400

        self._apply_config_values(values)
        return jsonify(self._config_payload())

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
        if ret != 0:
            self.logger.warning(
                "decrypt message failed: ret=%s, has_msg_signature=%s, has_timestamp=%s, has_nonce=%s, body_size=%s",
                ret,
                msg_signature is not None,
                timestamp is not None,
                nonce is not None,
                len(request.data),
            )
            if self._error_handler:
                self._error_handler(ret)
            return ""
        self.logger.info(f"decrypted msg: {msg.decode()}")

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
        try:
            # 打开文件并上传
            with open(file_path, 'rb') as file:
                files = {'file': (filename, file)}
                response = requests.post(
                    url=f'https://qyapi.weixin.qq.com/cgi-bin/webhook/upload_media?key={self._bot_key}&type=file',
                    files=files)
                # 检查响应
                if response.status_code != 200 and response.json().get("errcode") == 0:
                    return None
                return response.json()['media_id']
        except:
            return None

    def proactively_send(self, chat_id, msg_type, msg_type_name, msg_data):
        """"""
        try:
            payload = {
                "chatid": chat_id,
                "msgtype": msg_type,
            }
            payload.update(msg_data)

            r = requests.post(url=f'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={self._bot_key}',
                              json=payload)
            if r.status_code == 200 and r.json().get("errcode") == 0:
                return f"发送{msg_type_name}成功"
            else:
                return f"发送{msg_type_name}失败"
        except:
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
