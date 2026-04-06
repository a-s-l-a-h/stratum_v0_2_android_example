import stratum
import traceback
import time

try:
    import cv2
    import numpy as np
    OPENCV_OK = True
    print("[OPENCV] LOADED OK")
except Exception as e:
    OPENCV_OK = False
    print(f"[OPENCV] FAIL: {e}")


class CameraApp:
    def __init__(self, activity):
        self.activity = activity
        self.camera_device = None
        self.capture_session = None
        self.builder = None
        self.handler = None
        self._frame_count = 0
        self.last_time = time.time()

        self.current_cam = "0"
        self.all_cams    = ["0", "1"]

        try:
            self._build_ui(activity)
        except Exception as e:
            print(f"[FATAL INIT] {e}")
            traceback.print_exc()

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self, activity):
        # Root: vertical LinearLayout
        #
        #   root  (LinearLayout VERTICAL)
        #   ├── texture_view   MATCH_PARENT / 0dp weight=1   ← camera fills space
        #   ├── image_view     same size as texture_view (overlaid via FrameLayout trick)
        #   └── btn_switch     MATCH_PARENT / WRAP_CONTENT    ← natural button height
        #
        # The simplest way to guarantee the button is visible and below the camera:
        # put everything in a VERTICAL LinearLayout.
        # camera area = FrameLayout with weight=1 (fills remaining space above button).
        # button = plain Button with WRAP_CONTENT height → gets its natural size.
        #
        # The camera FrameLayout has weight=1 via LinearLayout.LayoutParams.
        # If LayoutParams fails we fall back: give btn a fixed height via setMinHeight.

        root = stratum.create_android_widget_LinearLayout(activity)
        root.setOrientation(1)   # VERTICAL

        # Camera area: FrameLayout stacks texture + opencv overlay
        cam_frame = stratum.create_android_widget_FrameLayout(activity)

        self.texture_view = stratum.create_android_view_TextureView(activity)
        self.texture_view.setSurfaceTextureListener({
            "onSurfaceTextureAvailable":   self.on_surface_available,
            "onSurfaceTextureSizeChanged": self.on_surface_size_changed,
            "onSurfaceTextureDestroyed":   self.on_surface_destroyed,
            "onSurfaceTextureUpdated":     self.on_surface_updated,
        })

        self.image_view = stratum.create_android_widget_ImageView(activity)

        cam_frame.addView(self.texture_view)
        cam_frame.addView(self.image_view)

        # Switch button
        self.btn = stratum.create_android_widget_Button(activity)
        self.btn.setText("[ Switch Camera ]")
        self.btn.setTextSize(20.0)
        self.btn.setGravity(17)   # CENTER

        def on_switch(v):
            self._switch()
        self.btn.setOnClickListener(on_switch)

        # Add to root
        root.addView(cam_frame)
        root.addView(self.btn)

        # Give cam_frame weight=1 so it fills everything above the button.
        # Try LinearLayout.LayoutParams(MATCH_PARENT, 0dp, weight=1.0)
        lp_set = False
        try:
            lp_cls = stratum.android_widget_LinearLayout_LayoutParams
            for i in range(10):
                fn = getattr(lp_cls, f"new_{i}", None)
                if fn is None:
                    continue
                try:
                    lp = fn(-1, 0, 1.0)   # width=-1 (MATCH_PARENT), height=0, weight=1
                    if lp is not None:
                        cam_frame.setLayoutParams(lp)
                        lp_set = True
                        print("[INIT] LayoutParams weight=1 applied — button will be visible below camera")
                        break
                except Exception:
                    pass
        except Exception as e:
            print(f"[INIT] LayoutParams attempt failed: {e}")

        if not lp_set:
            # Fallback: if we cannot set weight, give the button a large min-height
            # so Android is forced to allocate space for it. The camera will shrink.
            print("[INIT] LayoutParams not available — using setMinHeight fallback")
            self.btn.setMinHeight(160)
            self.btn.setMinimumHeight(160)

        stratum.setContentView(activity, root)
        print("[INIT] UI built")

    # ── switch ────────────────────────────────────────────────────────────────
    def _switch(self):
        self._close_camera()
        idx = self.all_cams.index(self.current_cam) if self.current_cam in self.all_cams else 0
        self.current_cam = self.all_cams[(idx + 1) % len(self.all_cams)]
        self.btn.setText(f"[ Camera {self.current_cam} — tap to switch ]")
        print(f"[SWITCH] now using camera {self.current_cam}")
        st = self.texture_view.getSurfaceTexture()
        if st:
            self.on_surface_available(st, 0, 0)

    # ── helpers ───────────────────────────────────────────────────────────────
    def _make_handler(self, looper):
        cls = stratum.android_os_Handler
        for i in range(10):
            fn = getattr(cls, f"new_{i}", None)
            if fn:
                try: return fn(looper)
                except Exception: pass
        raise RuntimeError("Handler ctor not found")

    def _make_surface(self, st):
        cls = stratum.android_view_Surface
        for i in range(10):
            fn = getattr(cls, f"new_{i}", None)
            if fn:
                try: return fn(st)
                except Exception: pass
        raise RuntimeError("Surface ctor not found")

    def _make_list(self):
        cls = stratum.java_util_ArrayList
        for i in range(10):
            fn = getattr(cls, f"new_{i}", None)
            if fn:
                try:
                    r = fn()
                    if r is not None: return r
                except Exception: pass
        raise RuntimeError("ArrayList ctor not found")

    # ── camera ────────────────────────────────────────────────────────────────
    def on_surface_available(self, st, w, h):
        print(f"[CB] surface available {w}x{h}")
        try:
            mgr = stratum.cast_to(
                self.activity.getSystemService("camera"),
                "android.hardware.camera2.CameraManager")
            looper = stratum.android_os_Looper.getMainLooper_static()
            self.handler = self._make_handler(looper)
            mgr.openCamera(self.current_cam, {
                "onOpened":       self.on_opened,
                "onDisconnected": lambda d: None,
                "onError":        lambda d, c: print(f"[CAM ERR] {c}"),
            }, self.handler)
        except Exception:
            traceback.print_exc()

    def on_opened(self, raw):
        try:
            self.camera_device = stratum.cast_to(
                raw, "android.hardware.camera2.CameraDevice")
            st = self.texture_view.getSurfaceTexture()
            st.setDefaultBufferSize(1280, 720)
            surface  = self._make_surface(st)
            self.builder = self.camera_device.createCaptureRequest(1)
            self.builder.addTarget(surface)
            lst = self._make_list()
            lst.add(surface)
            self.camera_device.createCaptureSession(
                stratum.cast_to(lst, "java.util.List"), {
                    "onConfigured":      self.on_configured,
                    "onConfigureFailed": lambda s: print("[CAM] config failed"),
                }, self.handler)
        except Exception:
            traceback.print_exc()

    def on_configured(self, raw):
        try:
            self.capture_session = stratum.cast_to(
                raw, "android.hardware.camera2.CameraCaptureSession")
            self.capture_session.setRepeatingRequest(
                self.builder.build(), None, self.handler)
            print(f"[CAM] live — camera {self.current_cam}")
        except Exception:
            traceback.print_exc()

    def on_surface_size_changed(self, st, w, h): pass
    def on_surface_destroyed(self, st):
        self.shutdown(); return True

    # ── opencv ────────────────────────────────────────────────────────────────
    def on_surface_updated(self, st):
        self._frame_count += 1
        if not OPENCV_OK or self._frame_count % 2 != 0:
            return
        try:
            self._draw()
        except Exception as e:
            print(f"[OCV] {e}")

    def _draw(self):
        t0  = time.time()
        bmp = self.texture_view.getBitmap()
        if bmp is None: return

        bmp_w = bmp.getWidth()
        bmp_h = bmp.getHeight()

        buf = stratum.java_nio_ByteBuffer.allocate_static(bmp_w * bmp_h * 4)
        bmp.copyPixelsToBuffer(buf)
        arr = np.frombuffer(buf.array(), dtype=np.uint8).reshape((bmp_h, bmp_w, 4))
        bgr = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)

        # ── PORTRAIT CROP FIX ─────────────────────────────────────────────
        # The bitmap has screen dimensions (portrait, e.g. 1080×2160).
        # The camera sends 1280×720 landscape frames scaled to fill that —
        # stretching them vertically. Only the central 16:9 band is valid.
        # We crop that band and scale it to fill the full portrait screen,
        # which is exactly what the stock camera does.
        band_h = int(bmp_w * 9 / 16)          # correct 16:9 height at screen width
        top    = max(0, (bmp_h - band_h) // 2)
        bot    = min(bmp_h, top + band_h)
        clean  = bgr[top:bot, :, :]            # clean 16:9 landscape crop
        full   = cv2.resize(clean, (bmp_w, bmp_h))  # scale to fill portrait screen

        # Edge detection
        gray    = cv2.cvtColor(full, cv2.COLOR_BGR2GRAY)
        blur    = cv2.GaussianBlur(gray, (5, 5), 0)
        edges   = cv2.Canny(blur, 50, 150)
        dilated = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)
        out     = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        out[dilated > 0] = [0, 255, 0]

        fps = 1.0 / max(t0 - self.last_time, 0.001)
        self.last_time = t0
        cv2.putText(out, f"CAM:{self.current_cam}  FPS:{fps:.1f}",
                    (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 2.0, (0, 0, 255), 4)

        rgba    = cv2.cvtColor(out, cv2.COLOR_BGR2RGBA)
        out_buf = stratum.java_nio_ByteBuffer.wrap_static(rgba.tobytes())
        out_bmp = bmp.copy(bmp.getConfig(), True)
        out_bmp.copyPixelsFromBuffer(out_buf)
        self.image_view.setImageBitmap(out_bmp)

    # ── shutdown ──────────────────────────────────────────────────────────────
    def _close_camera(self):
        for obj in [self.capture_session, self.camera_device]:
            if obj:
                try: obj.close()
                except Exception: pass
        self.capture_session = None
        self.camera_device   = None
        self.builder         = None

    def shutdown(self):
        self._close_camera()


# ─── lifecycle ────────────────────────────────────────────────────────────────
app = None

def onCreate():
    global app
    app = CameraApp(stratum.getActivity())

def onResume():
    global app
    if app and app.camera_device is None:
        st = app.texture_view.getSurfaceTexture()
        if st: app.on_surface_available(st, 0, 0)

def onPause(): pass
def onStop():  pass
def onDestroy():
    global app
    if app: app.shutdown(); app = None