"""Bio site token (Authorization of bio.visaforchina.cn) for each house, through
the /web page and a Tampermonkey script on the staff's own browser.

1. /web "Lấy token": POST /web/bio/start {house} -> a one-time ticket, the page
   opens BIO_LOGIN_URL#visa_tool=<ticket> in a new tab.
2. The userscript on bio.visaforchina.cn reads the ticket, gets the house
   account (GET /web/bio/ticket/<ticket>) and fills the login form. The person
   does the site's check and logs in.
3. The script sends the token it sees (Authorization header / Admin-Token
   cookie / token= in the URL) to POST /web/bio/ticket/<ticket>/token; the
   server checks it on the online list API and stores it in the house's token
   file (utils/token_store, read by /run when the curl has no authorization).

The account (BIO_LOGIN_URL, BIO_USERNAME, BIO_PASSWORD) is in each house's own
.env; the 10000 instance asks the house instance over 127.0.0.1 (/bio/*).
"""

from __future__ import annotations

import os
import re
import secrets
import threading
import time
from typing import Any

import requests

from constants import CHECK_OLD_LIST_BASE_URL

TICKET_TTL = 15 * 60  # seconds a ticket (open login tab) stays usable
SCRIPT_VERSION = "1.4"


# ---------- house side (each instance, its own .env) ----------
def login_config() -> dict[str, str]:
    return {
        "login_url": os.getenv("BIO_LOGIN_URL", "").strip(),
        "username": os.getenv("BIO_USERNAME", "").strip(),
        "password": os.getenv("BIO_PASSWORD", "").strip(),
    }


def normalize_authorization(value: Any) -> str:
    text = str(value or "").strip()
    if text.lower().startswith("bearer "):
        text = text[7:].strip()
    return text


def extract_token(value: Any) -> str:
    """Token from what a person pastes: the page address (token=...), a curl
    (Authorization header or Admin-Token cookie) or the token itself."""
    text = str(value or "").strip()
    for pattern in (r"[?&#]token=([A-Za-z0-9._\-]+)", r"Authorization:\s*(?:Bearer\s+)?([A-Za-z0-9._\-]+)",
                    r"Admin-Token=([A-Za-z0-9._\-]+)", r"(eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+)"):
        m = re.search(pattern, text, re.I)
        if m:
            return m.group(1)
    return ""


def check_authorization(authorization: str, timeout: float = 20) -> tuple[bool, str]:
    """Ask the online list API with this token. (valid, message)."""
    token = normalize_authorization(authorization)
    if not token:
        return False, "Token rỗng"
    try:
        resp = requests.post(
            f"{CHECK_OLD_LIST_BASE_URL}/application/online/list",
            params={"pageNum": 1, "pageSize": 1},
            headers={"Authorization": token, "Content-Type": "application/json",
                     "Accept": "application/json, text/plain, */*"},
            json={},
            timeout=timeout,
        )
    except requests.RequestException as exc:
        return False, f"Không gọi được trang bio: {exc}"
    try:
        data = resp.json()
    except ValueError:
        return False, f"Trang bio trả HTTP {resp.status_code}, không phải JSON"
    code = data.get("code") if isinstance(data, dict) else None
    if resp.status_code == 200 and code in (200, "200"):
        return True, "Token hợp lệ"
    msg = (data.get("msg") or data.get("message") or "") if isinstance(data, dict) else ""
    return False, f"Token không dùng được (HTTP {resp.status_code}, code {code}) {msg}".strip()


# ---------- tickets (10000 instance, in memory) ----------
_tickets: dict[str, dict[str, Any]] = {}
_lock = threading.Lock()


def _purge(now: float) -> None:
    for key in [k for k, t in _tickets.items() if now - t["created"] > TICKET_TTL * 4]:
        _tickets.pop(key, None)


def new_ticket(username: str, house: str, login_url: str) -> str:
    now = time.time()
    ticket = secrets.token_urlsafe(24)
    with _lock:
        _purge(now)
        _tickets[ticket] = {"username": username, "house": house, "login_url": login_url, "created": now,
                            "state": "waiting", "message": "Đang chờ đăng nhập trên tab bio", "updated": now}
    return ticket


def get_ticket(ticket: str, active_only: bool = True) -> dict[str, Any] | None:
    with _lock:
        t = _tickets.get(str(ticket or ""))
        if not t:
            return None
        if active_only and (t["state"] == "done" or time.time() - t["created"] > TICKET_TTL):
            return None
        return dict(t)


def set_ticket_state(ticket: str, state: str, message: str) -> None:
    with _lock:
        t = _tickets.get(ticket)
        if t:
            t.update(state=state, message=message, updated=time.time())


def ticket_status(ticket: str) -> dict[str, Any] | None:
    t = get_ticket(ticket, active_only=False)
    if not t:
        return None
    if t["state"] == "waiting" and time.time() - t["created"] > TICKET_TTL:
        t["state"], t["message"] = "expired", "Hết thời gian chờ (15 phút), bấm Lấy token lại"
    return {k: t[k] for k in ("house", "state", "message", "username")}


# ---------- the userscript ----------
def userscript(base_url: str) -> str:
    base = base_url.rstrip("/")
    host = base.split("://", 1)[-1].split("/", 1)[0].split(":", 1)[0]
    scheme = base.split("://", 1)[0] if "://" in base else "http"
    # Match patterns with a port are not matched by every Tampermonkey / Chrome version:
    # match the host on any port, the script itself checks the exact /web address.
    return (_USERSCRIPT.replace("__ORIGIN_NOPORT__", f"{scheme}://{host}")
            .replace("__BASE__", base).replace("__HOST__", host)
            .replace("__VERSION__", SCRIPT_VERSION))


_USERSCRIPT = r"""// ==UserScript==
// @name         Visa tool - lấy token bio
// @namespace    visa-tool
// @version      __VERSION__
// @description  Tự điền tài khoản của nhà và gửi token bio.visaforchina.cn về trang /web
// @match        https://*.visaforchina.cn/*
// @match        __ORIGIN_NOPORT__/*
// @grant        GM_xmlhttpRequest
// @grant        GM_setValue
// @grant        GM_getValue
// @grant        GM_deleteValue
// @grant        unsafeWindow
// @connect      __HOST__
// @run-at       document-start
// @updateURL    __BASE__/web/visa-token.user.js
// @downloadURL  __BASE__/web/visa-token.user.js
// ==/UserScript==

(function () {
  'use strict';
  const BASE = '__BASE__';
  const VERSION = '__VERSION__';
  const TTL = 15 * 60 * 1000;

  // On the /web page: tell it the script is installed, and take the ticket of
  // "Mở trang đăng nhập" (data-visa-tool-ticket) into the script's own storage,
  // shared with the bio tab (the bio site may drop the #visa_tool= of the link).
  if (location.href.startsWith(BASE + '/web')) {
    const root = document.documentElement;
    root.setAttribute('data-visa-token-script', VERSION);
    setInterval(() => {
      const t = root.getAttribute('data-visa-tool-ticket');
      if (t && root.getAttribute('data-visa-tool-ticket-ack') !== t) {
        GM_setValue('visa_tool_ticket', { ticket: t, at: Date.now() });
        root.setAttribute('data-visa-tool-ticket-ack', t);
      }
    }, 200);
    return;
  }

  // ---- *.visaforchina.cn only (the VPS host is matched on every port) ----
  if (!/(^|\.)visaforchina\.cn$/.test(location.hostname)) return;
  const KEY = 'visa_tool_ticket';
  const m = location.hash.match(/visa_tool=([A-Za-z0-9_-]+)/);
  let state = GM_getValue(KEY, null);
  if (m && (!state || state.ticket !== m[1])) state = { ticket: m[1], at: Date.now() };
  if (!state || Date.now() - state.at > TTL) return;   // not opened from /web: do nothing
  // Session state, kept across the bio site's page loads. Only a token from a NEW login
  // in this session is sent: tokens already there (another house maybe) never are.
  //   baseline: tokens seen before the login; sawLogin: the login form was shown.
  if (!state.init) state = { ticket: state.ticket, at: state.at, init: true, baseline: [], sawLogin: false, redirected: false };
  const save = () => GM_setValue(KEY, state);
  const ticket = state.ticket;
  const addBaseline = (t) => { if (t && !state.baseline.includes(t)) { state.baseline.push(t); save(); } };

  function readCookie(name) {
    const c = document.cookie.split('; ').find((x) => x.startsWith(name + '='));
    return c ? decodeURIComponent(c.slice(name.length + 1)) : '';
  }
  const clean = (t) => String(t || '').replace(/^Bearer\s+/i, '').trim();

  // First page of the session: remember the old token(s) and log the old session out,
  // so the site has to show its login form.
  if (!state.cleared) {
    addBaseline(clean(readCookie('Admin-Token')));
    addBaseline(clean(new URLSearchParams(location.search).get('token')));
    const past = 'expires=Thu, 01 Jan 1970 00:00:00 GMT';
    const host = location.hostname;
    for (const domain of ['', '; domain=' + host, '; domain=.visaforchina.cn']) {
      for (const path of ['/', location.pathname.replace(/[^/]*$/, '') || '/']) {
        document.cookie = 'Admin-Token=; ' + past + '; path=' + path + domain;
      }
    }
    for (const store of [localStorage, sessionStorage]) {
      try {
        for (const k of Object.keys(store)) if (/token/i.test(k)) { addBaseline(clean(store.getItem(k))); store.removeItem(k); }
      } catch (e) {}
    }
    state.cleared = true; save();
  }

  // Authorization header the site's own requests send
  let seenAuth = '';
  try {
    const W = unsafeWindow;
    const origSet = W.XMLHttpRequest.prototype.setRequestHeader;
    W.XMLHttpRequest.prototype.setRequestHeader = function (k, v) {
      try { if (String(k).toLowerCase() === 'authorization' && v) seenAuth = String(v); } catch (e) {}
      return origSet.apply(this, arguments);
    };
    const origFetch = W.fetch;
    if (origFetch) {
      W.fetch = function (input, init) {
        try {
          const h = (init && init.headers) || (input && input.headers);
          let v = '';
          if (h && typeof h.get === 'function') v = h.get('Authorization') || '';
          else if (h) v = h.Authorization || h.authorization || '';
          if (v) seenAuth = String(v);
        } catch (e) {}
        return origFetch.apply(this, arguments);
      };
    }
  } catch (e) {}

  function call(method, path, body) {
    return new Promise((resolve, reject) => {
      GM_xmlhttpRequest({
        method, url: BASE + path, headers: { 'Content-Type': 'application/json' },
        data: body ? JSON.stringify(body) : undefined, timeout: 60000,
        onload: (r) => { let d = {}; try { d = JSON.parse(r.responseText); } catch (e) {} resolve({ status: r.status, data: d.detail || d }); },
        onerror: () => reject(new Error('Không gọi được server ' + BASE)),
        ontimeout: () => reject(new Error('Server không trả lời')),
      });
    });
  }

  let banner;
  function say(text, color) {
    if (!document.body) return;
    if (!banner) {
      banner = document.createElement('div');
      banner.style.cssText = 'position:fixed;z-index:2147483647;left:50%;top:12px;transform:translateX(-50%);max-width:92%;'
        + 'padding:12px 18px;border-radius:8px;font:600 15px/1.4 system-ui,sans-serif;color:#fff;box-shadow:0 6px 20px rgba(0,0,0,.3);white-space:pre-wrap';
      document.body.appendChild(banner);
    }
    banner.style.background = color || '#1f6feb';
    banner.textContent = 'Visa tool: ' + text;
  }

  const visible = (el) => !!(el && (el.offsetWidth || el.offsetHeight || el.getClientRects().length));
  const passwordBox = () => [...document.querySelectorAll('input')].filter(visible).find((i) => i.type === 'password');
  function setValue(el, value) {
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
    setter.call(el, value);
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
  }
  // Fill the visible password box and the text/email box before it (once each).
  function fill(acc) {
    const inputs = [...document.querySelectorAll('input')].filter(visible);
    const pwd = inputs.find((i) => i.type === 'password');
    if (!pwd) return false;
    const before = inputs.slice(0, inputs.indexOf(pwd)).filter((i) => ['text', 'email', 'tel', ''].includes(i.type));
    const user = before[before.length - 1];
    if (user && !user.dataset.visaToolFilled) { setValue(user, acc.username); user.dataset.visaToolFilled = '1'; }
    if (!pwd.dataset.visaToolFilled) { setValue(pwd, acc.password); pwd.dataset.visaToolFilled = '1'; }
    return true;
  }

  function currentToken() {
    return clean(seenAuth || readCookie('Admin-Token') || new URLSearchParams(location.search).get('token'));
  }

  const sent = new Set();
  let sending = false, finished = false;
  async function trySend() {
    if (finished || sending) return;
    if (passwordBox()) {                        // login form on screen: not logged in yet
      if (!state.sawLogin) { state.sawLogin = true; save(); }
      addBaseline(currentToken());              // whatever token is around now is not the new one
      return;
    }
    const token = currentToken();
    if (!token || !token.startsWith('eyJ') || sent.has(token)) return;
    if (!state.sawLogin || state.baseline.includes(token)) return;   // old session: never sent
    sending = true; sent.add(token);
    say('Đã đăng nhập, đang gửi token mới về server…');
    try {
      const r = await call('POST', '/web/bio/ticket/' + ticket + '/token', { authorization: token });
      if (r.status === 200 && r.data.ok) {
        finished = true; GM_deleteValue(KEY);
        say('Đã cập nhật token nhà ' + (r.data.house || '') + ' ✓ — có thể tiếp tục dùng tab này', '#116b3a');
        setTimeout(() => { if (banner) banner.remove(); banner = null; }, 8000);   // the tab stays open
      } else {
        say((r.data.error || 'Token chưa dùng được') + '\nNếu chưa đăng nhập xong thì cứ tiếp tục đăng nhập.', '#a4161a');
      }
    } catch (e) { sent.delete(token); say(e.message, '#a4161a'); }
    sending = false;
  }

  async function start() {
    let acc = null;
    say('đang lấy tài khoản của nhà từ server…');
    try {
      const r = await call('GET', '/web/bio/ticket/' + ticket);
      if (r.status !== 200 || !r.data.ok) {
        say((r.data.error || 'Phiên lấy token không còn hiệu lực') + '. Bấm "Lấy token" trên /web lại.', '#a4161a');
        GM_deleteValue(KEY);
        return;
      }
      acc = r.data;
    } catch (e) { say(e.message, '#a4161a'); return; }
    say(state.sawLogin ? 'Nhà ' + acc.house + ': chờ đăng nhập xong…'
                       : 'Nhà ' + acc.house + ': đã điền tài khoản. Hãy làm bước xác minh rồi bấm đăng nhập.');
    let tries = 0;
    const filler = setInterval(() => { if (fill(acc) || ++tries > 120) clearInterval(filler); }, 500);
    setInterval(trySend, 1500);
    // No login form (the site kept the old session): go to the login page once, then ask.
    setTimeout(() => {
      if (state.sawLogin || passwordBox()) return;
      if (!state.redirected && acc.login_url) {
        state.redirected = true; save();
        location.href = acc.login_url;
      } else {
        say('Không thấy form đăng nhập. Bấm Đăng xuất trên trang bio rồi đăng nhập lại tài khoản nhà ' + acc.house + '.', '#a4161a');
      }
    }, 4000);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
"""
