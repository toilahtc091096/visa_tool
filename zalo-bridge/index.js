// Cầu nối zca-js <-> visa_tool (Python).
//  - Nghe tin nhắn nhóm Zalo -> POST {PYTHON_BASE_URL}/zalo/inbound
//  - Mở HTTP POST /send để Python gửi tin nhắn ra nhóm / cá nhân
//  - GET /groups: liệt kê id + tên nhóm để điền TRACKER_ZALO_GROUP_ID
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { LoginQRCallbackEventType, ThreadType, Zalo } from "zca-js";

const PORT = Number(process.env.BRIDGE_PORT || 3100);
const HOST = process.env.BRIDGE_HOST || "127.0.0.1";
const SECRET = process.env.ZALO_BRIDGE_SECRET || "";
const PYTHON_BASE_URL = (process.env.PYTHON_BASE_URL || "http://127.0.0.1:10000").replace(/\/$/, "");
const GROUP_IDS = (process.env.TRACKER_ZALO_GROUP_ID || "")
  .split(",")
  .map((item) => item.trim())
  .filter(Boolean);
const CREDENTIALS_PATH = path.resolve(process.env.ZALO_CREDENTIALS_PATH || "credentials.json");
const QR_PATH = path.resolve(process.env.ZALO_QR_PATH || "qr.png");

function log(...args) {
  console.log(`[${new Date().toISOString()}] [zalo-bridge]`, ...args);
}

function saveCredentials(credentials) {
  fs.writeFileSync(CREDENTIALS_PATH, JSON.stringify(credentials, null, 2), "utf8");
  log(`saved credentials -> ${CREDENTIALS_PATH}`);
}

async function login() {
  const zalo = new Zalo({ selfListen: false, checkUpdate: false, logging: false });

  if (fs.existsSync(CREDENTIALS_PATH)) {
    try {
      const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, "utf8"));
      const api = await zalo.login(credentials);
      log("logged in with saved cookie");
      return api;
    } catch (error) {
      log("cookie login failed, fallback to QR:", error?.message || error);
    }
  }

  const api = await zalo.loginQR({ qrPath: QR_PATH }, async (event) => {
    switch (event.type) {
      case LoginQRCallbackEventType.QRCodeGenerated:
        await event.actions.saveToFile(QR_PATH);
        log(`scan QR in ${QR_PATH} with the Zalo app`);
        break;
      case LoginQRCallbackEventType.QRCodeExpired:
        log("QR expired, generating a new one");
        event.actions.retry();
        break;
      case LoginQRCallbackEventType.QRCodeScanned:
        log(`QR scanned by ${event.data.display_name}, confirm on phone`);
        break;
      case LoginQRCallbackEventType.QRCodeDeclined:
        log("QR declined");
        break;
      case LoginQRCallbackEventType.GotLoginInfo:
        saveCredentials(event.data);
        break;
    }
  });
  log("logged in with QR");
  return api;
}

async function forwardToPython(message) {
  const content = message.data?.content;
  if (typeof content !== "string" || !content.trim()) return;

  const payload = {
    thread_id: String(message.threadId),
    sender_id: String(message.data.uidFrom || ""),
    sender_name: String(message.data.dName || ""),
    msg_id: String(message.data.msgId || ""),
    text: content,
  };
  try {
    const resp = await fetch(`${PYTHON_BASE_URL}/zalo/inbound`, {
      method: "POST",
      headers: { "content-type": "application/json", "x-bridge-secret": SECRET },
      body: JSON.stringify(payload),
    });
    const body = await resp.text();
    log(`inbound group=${payload.thread_id} sender=${payload.sender_id} -> ${resp.status} ${body.slice(0, 200)}`);
  } catch (error) {
    log("forward to python failed:", error?.message || error);
  }
}

function readJson(req) {
  return new Promise((resolve, reject) => {
    let raw = "";
    req.on("data", (chunk) => (raw += chunk));
    req.on("end", () => {
      try {
        resolve(raw ? JSON.parse(raw) : {});
      } catch (error) {
        reject(error);
      }
    });
    req.on("error", reject);
  });
}

function reply(res, status, body) {
  res.writeHead(status, { "content-type": "application/json; charset=utf-8" });
  res.end(JSON.stringify(body));
}

function startHttpServer(api) {
  const server = http.createServer(async (req, res) => {
    if (SECRET && req.headers["x-bridge-secret"] !== SECRET) {
      return reply(res, 401, { ok: false, error: "invalid bridge secret" });
    }

    try {
      if (req.method === "POST" && req.url === "/send") {
        const { thread_id: threadId, thread_type: threadType = "group", text } = await readJson(req);
        if (!threadId || !text) return reply(res, 400, { ok: false, error: "thread_id and text are required" });
        const type = threadType === "user" ? ThreadType.User : ThreadType.Group;
        const result = await api.sendMessage({ msg: String(text) }, String(threadId), type);
        return reply(res, 200, { ok: true, result });
      }

      if (req.method === "GET" && req.url === "/groups") {
        const groupIds = Object.keys((await api.getAllGroups()).gridVerMap || {});
        const info = groupIds.length ? await api.getGroupInfo(groupIds) : { gridInfoMap: {} };
        const groups = groupIds.map((id) => ({ id, name: info.gridInfoMap?.[id]?.name || "" }));
        return reply(res, 200, { ok: true, groups });
      }

      if (req.method === "GET" && req.url === "/health") {
        return reply(res, 200, { ok: true });
      }

      return reply(res, 404, { ok: false, error: "not found" });
    } catch (error) {
      log(`${req.method} ${req.url} failed:`, error?.message || error);
      return reply(res, 500, { ok: false, error: String(error?.message || error) });
    }
  });
  server.listen(PORT, HOST, () => log(`http listening on http://${HOST}:${PORT}`));
}

async function main() {
  const api = await login();

  // Lưu lại cookie mới nhất để lần sau không phải quét QR.
  const context = api.getContext();
  saveCredentials({
    cookie: api.getCookie().toJSON().cookies,
    imei: context.imei,
    userAgent: context.userAgent,
  });

  api.listener.on("message", (message) => {
    if (message.type !== ThreadType.Group || message.isSelf) return;
    if (GROUP_IDS.length && !GROUP_IDS.includes(String(message.threadId))) return;
    forwardToPython(message);
  });
  api.listener.on("connected", () => log("listener connected"));
  api.listener.on("closed", (code, reason) => {
    // 3000 = đang mở Zalo Web/bridge khác cùng tài khoản (chỉ 1 listener được phép).
    log(`listener closed code=${code} reason=${reason}`);
  });
  api.listener.on("error", (error) => log("listener error:", error?.message || error));
  api.listener.start({ retryOnClose: true });

  startHttpServer(api);
}

main().catch((error) => {
  log("fatal:", error?.stack || error);
  process.exit(1);
});
