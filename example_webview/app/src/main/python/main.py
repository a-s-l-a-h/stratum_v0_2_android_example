import stratum
from stratum.android.webkit import WebView, create_WebView
import json
import threading
import time




# ── Globals ───────────────────────────────────────────────────────────────────
global_webview  = None
global_activity = None
_stop_event     = threading.Event()   # set on onDestroy — stops poller cleanly
_in_flight      = False               # True while evaluateJavascript pending
_in_flight_lock = threading.Lock()

# ── 1. Message processor (ValueCallback — runs on Android main thread) ────────

def process_js_messages(json_result):
    global _in_flight
    with _in_flight_lock:
        _in_flight = False            # poll slot is free again

    if not json_result:
        return
    # Android double-wraps JS strings: "[]" becomes '"[]"'
    try:
        if json_result.startswith('"') and json_result.endswith('"'):
            json_result = json.loads(json_result)
        if json_result in ("[]", "{}", "null", ""):
            return

        messages = json.loads(json_result)
        if not isinstance(messages, list) or not messages:
            return

        for msg in messages:
            print(f" message : {msg}")
            response = msg[::-1].upper()
            safe     = json.dumps(f"respone: '{response}'")
            _send_to_js(f"window.receiveFromPython({safe});")

    except Exception as e:
        print(f"Bridge error: {e}")


def _send_to_js(script):
    """Thread-safe: always dispatches evaluateJavascript on main thread."""
    wv = global_webview
    ac = global_activity
    if wv and ac:
        ac.runOnUiThread(lambda: wv.evaluateJavascript(script, lambda x: None))


# ── 2. Poller (background thread) ─────────────────────────────────────────────

def _poller():
    """
    Fixed 50ms interval — simple, reliable, same as original but tighter.
    Skips if previous poll still in flight — no stacking, no memory buildup.
    Stops cleanly when _stop_event is set.
    """
    global _in_flight

    INTERVAL = 0.05   # 50ms — fast enough to feel instant, light on CPU

    while not _stop_event.is_set():
        _stop_event.wait(timeout=INTERVAL)   # sleeps INTERVAL, wakes early on destroy

        if _stop_event.is_set():
            break

        wv = global_webview
        ac = global_activity
        if not wv or not ac:
            continue

        # Skip if previous poll hasn't returned yet — prevents stacking
        with _in_flight_lock:
            if _in_flight:
                continue
            _in_flight = True

        # Capture locals — avoids closure holding global refs across GC
        webview_ref  = wv
        activity_ref = ac

        def do_poll(w=webview_ref, a=activity_ref):
            w.evaluateJavascript(
                "window.stratumQueue&&window.stratumQueue.length>0"
                "?window.popStratumMessages():'[]';",
                process_js_messages
            )

        ac.runOnUiThread(do_poll)


def start_python_bridge():
    _stop_event.clear()
    t = threading.Thread(target=_poller, daemon=True, name="stratum-poller")
    t.start()


# ── 3. App UI ─────────────────────────────────────────────────────────────────

def onCreate():
    global global_webview, global_activity

    global_activity = stratum.getActivity()
    global_webview  = create_WebView(global_activity)

    settings = global_webview.getSettings()
    settings.setJavaScriptEnabled(True)

    html_content = """<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: sans-serif;
            background: #0f0f13;
            color: #fff;
            display: flex;
            flex-direction: column;
            height: 100vh;
            padding: 16px;
            gap: 12px;
        }
        h2 { color: #bb86fc; text-align: center; font-size: 18px; }
        #chat {
            flex: 1;
            background: #1a1a24;
            border-radius: 12px;
            padding: 12px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        .msg {
            padding: 10px 14px;
            border-radius: 8px;
            max-width: 80%;
            word-wrap: break-word;
            font-size: 15px;
            line-height: 1.4;
        }
        .msg-js {
            background: #3700b3;
            align-self: flex-end;
            border-bottom-right-radius: 2px;
        }
        .msg-py {
            background: #03dac6;
            color: #000;
            align-self: flex-start;
            border-bottom-left-radius: 2px;
        }
        .input-area { display: flex; gap: 8px; }
        input {
            flex: 1;
            padding: 14px;
            border-radius: 8px;
            border: none;
            background: #2d2d3a;
            color: #fff;
            font-size: 16px;
            outline: none;
        }
        button {
            padding: 14px 22px;
            background: #03dac6;
            color: #000;
            border: none;
            border-radius: 8px;
            font-weight: bold;
            font-size: 16px;
            cursor: pointer;
            transition: background 0.15s;
        }
        button:active { background: #01a394; }
    </style>
</head>
<body>
    <h2>Simple WebView</h2>

    <div id="chat">
        <div class="msg msg-py">.</div>
    </div>

    <div class="input-area">
        <input id="inp" type="text" placeholder="Send ..."
               onkeypress="if(event.key==='Enter')sendMsg()">
        <button onclick="sendMsg()">Send</button>
    </div>

    <script>
        window.stratumQueue = [];

        window.popStratumMessages = function() {
            if (!window.stratumQueue.length) return '[]';
            var batch = window.stratumQueue.splice(0);  // splice — no new array alloc
            return JSON.stringify(batch);
        };

        function sendMsg() {
            var inp = document.getElementById('inp');
            var txt = inp.value.trim();
            if (!txt) return;
            addMsg(txt, 'msg-js');
            window.stratumQueue.push(txt);
            inp.value = '';
        }

        function addMsg(text, cls) {
            var chat = document.getElementById('chat');
            var div  = document.createElement('div');
            div.className = 'msg ' + cls;
            div.textContent = text;          // textContent — XSS safe
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }

        window.receiveFromPython = function(msg) {
            addMsg(msg, 'msg-py');
        };
    </script>
</body>
</html>"""

    global_webview.loadDataWithBaseURL("", html_content, "text/html", "UTF-8", "")
    stratum.setContentView(global_activity, global_webview)
    start_python_bridge()


def onDestroy():
    global global_webview, global_activity
    _stop_event.set()          # tells poller thread to exit cleanly
    global_webview  = None     # releases WebView ref — no leak
    global_activity = None     # releases Activity ref — no leak