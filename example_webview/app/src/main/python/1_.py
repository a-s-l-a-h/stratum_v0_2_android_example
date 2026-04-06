import stratum
# FIX 1: Import the factory function `create_WebView`
from stratum.android.webkit import WebView, create_WebView
import json
import threading
import time

global_webview = None
global_activity = None

# ── 1. The Python Backend Processor ──────────────────────────────────────────

def process_js_messages(json_result):
    """Triggered by Android's ValueCallback interface. NOW IT WORKS!"""

    # Android wraps JS strings in quotes, e.g. "[]" becomes '"[]"'
    if not json_result or json_result == "null" or json_result == '"{}"' or json_result == '"[]"':
        return

    try:
        if json_result.startswith('"') and json_result.endswith('"'):
            json_result = json.loads(json_result)

        messages = json.loads(json_result)

        if not isinstance(messages, list) or len(messages) == 0:
            return

        for msg in messages:
            print(f"Stratum: Received from JS -> {msg}")

            # --- DO PYTHON WORK ---
            processed = f"Python Reversed: '{msg[::-1].upper()}'"

            # Send response back to JavaScript
            safe_string = json.dumps(processed)
            script = f"window.receiveFromPython({safe_string});"
            global_webview.evaluateJavascript(script, lambda x: None)

    except Exception as e:
        print(f"Stratum JSON parse error: {e}")

# ── 2. The Background Poller ─────────────────────────────────────────────────

def start_python_bridge():
    """Runs a background thread to poll JS without freezing the UI"""
    def background_poller():
        while True:
            time.sleep(0.1)

            def main_thread_action():
                if global_webview:
                    global_webview.evaluateJavascript("window.popStratumMessages();", process_js_messages)

            if global_activity:
                global_activity.runOnUiThread(main_thread_action)

    t = threading.Thread(target=background_poller, daemon=True)
    t.start()

# ── 3. The App UI ────────────────────────────────────────────────────────────

def onCreate():
    global global_webview, global_activity

    global_activity = stratum.getActivity()

    # FIX 2: Use the factory function to create the WebView
    global_webview = create_WebView(global_activity)

    settings = global_webview.getSettings()
    settings.setJavaScriptEnabled(True)

    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
        <style>
            body { font-family: sans-serif; background: #0f0f13; color: #fff; padding: 20px; margin: 0; display: flex; flex-direction: column; height: 100vh; box-sizing: border-box;}
            h2 { color: #bb86fc; text-align: center; margin-top: 0;}
            #chat { flex: 1; background: #1a1a24; border-radius: 12px; padding: 15px; overflow-y: auto; margin-bottom: 15px;}
            .input-area { display: flex; gap: 10px; }
            input { flex: 1; padding: 15px; border-radius: 8px; border: none; background: #2d2d3a; color: white; font-size: 16px; outline: none;}
            button { padding: 15px 25px; background: #03dac6; color: #000; border: none; border-radius: 8px; font-weight: bold; font-size: 16px; cursor: pointer;}
            button:active { transform: scale(0.95); background: #01a394;}

            .msg { margin: 10px 0; padding: 10px 14px; border-radius: 8px; max-width: 80%; word-wrap: break-word; font-size: 15px;}
            .msg-js { background: #3700b3; align-self: flex-end; margin-left: auto; border-bottom-right-radius: 0;}
            .msg-py { background: #03dac6; color: #000; align-self: flex-start; margin-right: auto; border-bottom-left-radius: 0;}
            .flex-container { display: flex; flex-direction: column; }
        </style>
    </head>
    <body>
        <h2>🐍 Stratum Bridge</h2>

        <div id="chat" class="flex-container">
            <div class="msg msg-py">Python Backend is ready! Type something...</div>
        </div>

        <div class="input-area">
            <input type="text" id="inp" placeholder="Send to Python..." onkeypress="handleKey(event)">
            <button onclick="sendMsg()">Send</button>
        </div>

        <script>
            window.stratumQueue = [];

            window.popStratumMessages = function() {
                if (window.stratumQueue.length === 0) return "[]";
                var batch = window.stratumQueue;
                window.stratumQueue = [];
                return JSON.stringify(batch);
            };

            function handleKey(e) { if(e.key === 'Enter') sendMsg(); }

            function sendMsg() {
                var inp = document.getElementById('inp');
                var txt = inp.value.trim();
                if(!txt) return;

                var chat = document.getElementById('chat');
                chat.innerHTML += "<div class='msg msg-js'>" + txt + "</div>";
                chat.scrollTop = chat.scrollHeight;

                window.stratumQueue.push(txt);
                inp.value = '';
            }

            window.receiveFromPython = function(msg) {
                var chat = document.getElementById('chat');
                chat.innerHTML += "<div class='msg msg-py'>" + msg + "</div>";
                chat.scrollTop = chat.scrollHeight;
            };
        </script>
    </body>
    </html>
    """

    global_webview.loadDataWithBaseURL("", html_content, "text/html", "UTF-8", "")
    stratum.setContentView(global_activity, global_webview)

    start_python_bridge()

def onDestroy():
    global global_webview, global_activity
    global_webview = None
    global_activity = None