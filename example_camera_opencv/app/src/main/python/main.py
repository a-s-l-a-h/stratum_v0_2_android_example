import stratum
import sys
import traceback
import time

try:
    import cv2
    import numpy as np
    OPENCV_OK = True
    print("[OPENCV] cv2 + numpy SUCCESSFULLY LOADED")
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

        print("[INIT] Building UI Layers...")
        try:
            # 1. FrameLayout (Root container)
            self.frame_layout = stratum.create_android_widget_FrameLayout(activity)

            # 2. TextureView (Bottom Layer: receives camera stream, hidden from us)
            self.texture_view = stratum.create_android_view_TextureView(activity)
            self.texture_view.setSurfaceTextureListener({
                "onSurfaceTextureAvailable":   self.on_surface_available,
                "onSurfaceTextureSizeChanged": self.on_surface_size_changed,
                "onSurfaceTextureDestroyed":   self.on_surface_destroyed,
                "onSurfaceTextureUpdated":     self.on_surface_updated,
            })

            # 3. ImageView (Top Layer: displays OpenCV frames)
            self.image_view = stratum.create_android_widget_ImageView(activity)

            # Add to stack
            self.frame_layout.addView(self.texture_view)
            self.frame_layout.addView(self.image_view)

            stratum.setContentView(activity, self.frame_layout)
            print("[INIT] Dual-Layer UI OK")
        except Exception as e:
            print(f"[FATAL INIT] {e}")
            traceback.print_exc()

    # ── Safe Constructor Helpers ──────────────────────────────────────────────
    def _create_handler(self, looper):
        cls = stratum.android_os_Handler
        for i in range(10):
            if hasattr(cls, f"new_{i}"):
                try:
                    return getattr(cls, f"new_{i}")(looper)
                except Exception:
                    pass
        raise RuntimeError("Could not find Handler(Looper) constructor")

    def _create_surface(self, st):
        cls = stratum.android_view_Surface
        for i in range(10):
            if hasattr(cls, f"new_{i}"):
                try:
                    return getattr(cls, f"new_{i}")(st)
                except Exception:
                    pass
        raise RuntimeError("Could not find Surface(SurfaceTexture) constructor")

    def _create_array_list(self):
        cls = stratum.java_util_ArrayList
        for i in range(10):
            if hasattr(cls, f"new_{i}"):
                try:
                    res = getattr(cls, f"new_{i}")()
                    if res is not None:
                        return res
                except Exception:
                    pass
        raise RuntimeError("Could not find ArrayList() constructor")

    # ── Camera Setup ──────────────────────────────────────────────────────────
    def on_surface_available(self, st, w, h):
        print(f"[CB] surfaceAvailable {w}x{h}")
        try:
            sys_svc = self.activity.getSystemService("camera")
            cam_mgr = stratum.cast_to(sys_svc, "android.hardware.camera2.CameraManager")

            # Safely create Handler
            looper = stratum.android_os_Looper.getMainLooper_static()
            self.handler = self._create_handler(looper)

            cam_mgr.openCamera("0", {
                "onOpened":       self.on_camera_opened,
                "onDisconnected": self.on_camera_disconnected,
                "onError":        self.on_camera_error,
            }, self.handler)
        except Exception as e:
            traceback.print_exc()

    def on_camera_opened(self, raw_device):
        print("[CB] cameraOpened")
        try:
            self.camera_device = stratum.cast_to(raw_device, "android.hardware.camera2.CameraDevice")

            # Safely create Surface
            st = self.texture_view.getSurfaceTexture()
            surface = self._create_surface(st)

            self.builder = self.camera_device.createCaptureRequest(1)
            self.builder.addTarget(surface)

            # Safely create ArrayList
            lst = self._create_array_list()
            lst.add(surface)
            lst_if = stratum.cast_to(lst, "java.util.List")

            self.camera_device.createCaptureSession(lst_if, {
                "onConfigured":      self.on_session_configured,
                "onConfigureFailed": self.on_session_failed,
            }, self.handler)
        except Exception as e:
            traceback.print_exc()

    def on_session_configured(self, raw_session):
        try:
            self.capture_session = stratum.cast_to(raw_session, "android.hardware.camera2.CameraCaptureSession")
            req = self.builder.build()
            self.capture_session.setRepeatingRequest(req, None, self.handler)
            print("\n=======================================================")
            print(">>> PREVIEW LIVE — OPENCV HIJACKING FRAMES NOW <<<")
            print("=======================================================\n")
        except Exception as e:
            traceback.print_exc()

    def on_session_failed(self, raw): print("[CB] sessionFailed")
    def on_camera_disconnected(self, raw): print("[CB] disconnected")
    def on_camera_error(self, raw, code): print(f"[CB] error code={code}")
    def on_surface_size_changed(self, st, w, h): pass
    def on_surface_destroyed(self, st):
        self.shutdown()
        return True

    # ── OpenCV Processing Frame-by-Frame ──────────────────────────────────────
    def on_surface_updated(self, st):
        self._frame_count += 1
        if not OPENCV_OK:
            return

        # Process every 2nd frame (30fps -> 15fps) to keep it smooth
        if self._frame_count % 2 != 0:
            return

        try:
            self._process_and_draw()
        except Exception as e:
            print(f"[OPENCV ERROR] {e}")
            traceback.print_exc()

    def _process_and_draw(self):
        t0 = time.time()

        # 1. Grab raw Bitmap from the hidden TextureView
        bmp = self.texture_view.getBitmap()
        if bmp is None: return
        w, h = bmp.getWidth(), bmp.getHeight()

        # 2. Extract Pixels to Python Bytes
        size = w * h * 4
        in_buf = stratum.java_nio_ByteBuffer.allocate_static(size)
        bmp.copyPixelsToBuffer(in_buf)
        raw_bytes = in_buf.array()

        # 3. Convert to NumPy
        arr = np.frombuffer(raw_bytes, dtype=np.uint8).reshape((h, w, 4))
        bgr = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)

        # 4. OpenCV Edge Detection
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 50, 150)

        kernel = np.ones((2, 2), np.uint8)

        # Dilate the edges to make them thicker
        dilated_edges = cv2.dilate(edges, kernel, iterations=1)
        # --------------------------------------------------------

        # Make background B&W, draw Neon Green edges
        bgr_gray = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        # IMPORTANT: Use the new 'dilated_edges' to draw the thicker lines
        bgr_gray[dilated_edges > 0] = [0, 255, 0]

        # FPS Counter
        fps = 1.0 / (t0 - self.last_time) if self.last_time else 0
        self.last_time = t0
        cv2.putText(bgr_gray, f"OPENCV FPS: {fps:.1f}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2.0, (0, 0, 255), 5)

        # 5. Push Processed Bytes back to Java via wrap_static
        result_rgba = cv2.cvtColor(bgr_gray, cv2.COLOR_BGR2RGBA)
        out_buf = stratum.java_nio_ByteBuffer.wrap_static(result_rgba.tobytes())

        cfg = bmp.getConfig()
        out_bmp = bmp.copy(cfg, True)
        out_bmp.copyPixelsFromBuffer(out_buf)

        # 6. Apply the OpenCV Bitmap to the top-layer ImageView!
        self.image_view.setImageBitmap(out_bmp)

    def shutdown(self):
        if self.capture_session:
            try: self.capture_session.close()
            except: pass
        if self.camera_device:
            try: self.camera_device.close()
            except: pass

# ─── Android App Lifecycle ───────────────────────────────────────────────────
app = None

def onCreate():
    global app
    app = CameraApp(stratum.getActivity())

def onResume():
    global app
    if app and app.camera_device is None:
        st = app.texture_view.getSurfaceTexture()
        if st:
            app.on_surface_available(st, 0, 0)

def onPause(): pass
def onStop(): pass
def onDestroy():
    global app
    if app:
        app.shutdown()
        app = None