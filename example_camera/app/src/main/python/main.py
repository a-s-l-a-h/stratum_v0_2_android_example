import stratum
import sys
import traceback

def log_state(tag, obj):
    print(f"\n--- [STATE CHECK: {tag}] ---")
    if obj is None:
        print(" -> Object is None")
        return
    print(f" -> Python Type: {type(obj)}")
    if hasattr(obj, "class_name"):
        print(f" -> Underlying Java Class: {obj.class_name()}")
    else:
        print(" -> Not a Stratum object")
    print("-----------------------------\n")


class CameraApp:
    def __init__(self, activity):
        self.activity = activity
        self.camera_device = None
        self.capture_session = None
        self.builder = None
        self.handler = None

        print("[INIT] Building UI and TextureView...")
        try:
            self.texture_view = stratum.create_android_view_TextureView(activity)

            texture_listener = {
                "onSurfaceTextureAvailable": self.on_surface_available,
                "onSurfaceTextureSizeChanged": self.on_surface_size_changed,
                "onSurfaceTextureDestroyed": self.on_surface_destroyed,
                "onSurfaceTextureUpdated": self.on_surface_updated,
            }
            self.texture_view.setSurfaceTextureListener(texture_listener)

            stratum.setContentView(activity, self.texture_view)
            print("[INIT] TextureView successfully attached to Activity.")
        except Exception as e:
            print(f"[FATAL INIT ERROR] {e}")
            traceback.print_exc()

    # ── Camera Inspection ──────────────────────────────────────────────────
    def log_camera_info(self, camera_manager):
        try:
            cam_ids = camera_manager.getCameraIdList()
            print(f"[CAMERA INFO] Detected {len(cam_ids)} cameras: {cam_ids}")
            for cid in cam_ids:
                chars = camera_manager.getCameraCharacteristics(cid)
                facing_key = stratum.android_hardware_camera2_CameraCharacteristics.sf_get_LENS_FACING()
                facing = chars.get(facing_key)
                facing_str = "BACK" if facing == 1 else "FRONT" if facing == 0 else "EXTERNAL"
                print(f"  -> Camera '{cid}' : {facing_str}")
        except Exception as e:
            print(f"[WARNING] Could not read camera info: {e}")

    # ── Surface Auto-Discovery ─────────────────────────────────────────────
    def create_surface_from_texture(self, surface_texture):
        cls = stratum.android_view_Surface
        for i in range(10):
            method_name = f"new_{i}"
            if hasattr(cls, method_name):
                try:
                    method = getattr(cls, method_name)
                    surface = method(surface_texture)
                    if surface is not None:
                        print(f"[SURFACE] SUCCESS: Created Surface using {method_name}")
                        return surface
                except Exception:
                    pass
        raise RuntimeError("FATAL: Could not find a valid Surface(SurfaceTexture) constructor.")

    # ── SurfaceTextureListener callbacks ──────────────────────────────────
    def on_surface_available(self, surface_texture, width, height):
        print(f"\n[CALLBACK] onSurfaceTextureAvailable ({width}x{height})")
        try:
            sys_service = self.activity.getSystemService("camera")
            camera_manager = stratum.cast_to(sys_service, "android.hardware.camera2.CameraManager")
            self.log_camera_info(camera_manager)

            looper = stratum.android_os_Looper.getMainLooper_static()
            if hasattr(stratum.android_os_Handler, "new_2"):
                self.handler = stratum.android_os_Handler.new_2(looper)
            elif hasattr(stratum.android_os_Handler, "new_1"):
                self.handler = stratum.android_os_Handler.new_1(looper)
            else:
                self.handler = stratum.android_os_Handler.new_0(looper)

            camera_callbacks = {
                "onOpened":       self.on_camera_opened,
                "onDisconnected": self.on_camera_disconnected,
                "onError":        self.on_camera_error,
            }
            print("[ACTION] Requesting openCamera('0')...")
            camera_manager.openCamera("0", camera_callbacks, self.handler)
        except Exception as e:
            print(f"[FATAL ERROR in on_surface_available] {e}")
            traceback.print_exc()

    def on_surface_size_changed(self, surface_texture, width, height):
        pass

    def on_surface_destroyed(self, surface_texture):
        print("[CALLBACK] onSurfaceTextureDestroyed")
        return True

    def on_surface_updated(self, surface_texture):
        pass

    def start_camera(self):
        """Called by Java after permission is granted on first launch."""
        surface_texture = self.texture_view.getSurfaceTexture()
        if surface_texture is not None:
            # Surface is already available, just missed the callback — retry
            self.on_surface_available(surface_texture, 0, 0)

    # ── CameraDevice.StateCallback ─────────────────────────────────────────
    def on_camera_opened(self, raw_camera_device):
        print("\n[CALLBACK] on_camera_opened")
        try:
            log_state("RAW CAMERA DEVICE", raw_camera_device)
            self.camera_device = stratum.cast_to(raw_camera_device, "android.hardware.camera2.CameraDevice")
            if not hasattr(self.camera_device, "createCaptureRequest"):
                print(f"[FATAL] Cast failed! Dir: {dir(self.camera_device)}")
                return
            print("[ACTION] Camera Device Cast Successful! Building capture session...")

            surface_texture = self.texture_view.getSurfaceTexture()
            surface = self.create_surface_from_texture(surface_texture)

            self.builder = self.camera_device.createCaptureRequest(1)
            self.builder.addTarget(surface)

            session_callbacks = {
                "onConfigured":      self.on_session_configured,
                "onConfigureFailed": self.on_session_failed,
            }

            print("[ACTION] Creating Java ArrayList...")
            surface_list = self.create_java_array_list()

            print("[ACTION] Adding Surface to ArrayList...")
            print("[ACTION] Adding Surface to ArrayList...")
            surface_list.add(surface)

            # --- THE FIX ---
            # Upcast the ArrayList to the List interface so nanobind accepts it
            print("[ACTION] Upcasting ArrayList to List interface...")
            list_interface = stratum.cast_to(surface_list, "java.util.List")

            # Pass the upcasted list_interface instead of surface_list
            self.camera_device.createCaptureSession(list_interface, session_callbacks, self.handler)
            print("[ACTION] createCaptureSession() requested.")
        except Exception as e:
            print(f"[FATAL ERROR in on_camera_opened] {e}")
            traceback.print_exc()

    def on_camera_disconnected(self, raw_camera_device):
        print("[CALLBACK] Camera Disconnected.")

    def on_camera_error(self, raw_camera_device, error_code):
        print(f"[CALLBACK] Camera Error! Code: {error_code}")

    def create_java_array_list(self):
        cls = stratum.java_util_ArrayList
        print(f"[ARRAYLIST] Searching for empty constructor in: {dir(cls)}")
        for i in range(10):
            method_name = f"new_{i}"
            if hasattr(cls, method_name):
                try:
                    java_list = getattr(cls, method_name)()
                    if java_list is not None:
                        print(f"[ARRAYLIST] SUCCESS: Created ArrayList using {method_name}")
                        return java_list
                except Exception:
                    pass
        raise RuntimeError("FATAL: Could not find an empty constructor for ArrayList.")

    # ── CameraCaptureSession.StateCallback ────────────────────────────────
    def on_session_configured(self, raw_session):
        print("\n[CALLBACK] on_session_configured")
        try:
            log_state("RAW CAPTURE SESSION", raw_session)
            self.capture_session = stratum.cast_to(raw_session, "android.hardware.camera2.CameraCaptureSession")
            if not hasattr(self.capture_session, "setRepeatingRequest"):
                print(f"[FATAL] Cast failed! Dir: {dir(self.capture_session)}")
                return
            print("[ACTION] Session Cast Successful! Starting preview stream...")
            request = self.builder.build()
            self.capture_session.setRepeatingRequest(request, None, self.handler)
            print("\n*********************************************")
            print(">> SUCCESS! CAMERA PREVIEW SHOULD BE LIVE <<")
            print("*********************************************\n")
        except Exception as e:
            print(f"[FATAL ERROR in on_session_configured] {e}")
            traceback.print_exc()

    def on_session_failed(self, raw_session):
        print("[CALLBACK] on_session_failed - Session configuration was rejected by Android.")

    # ── Cleanup ────────────────────────────────────────────────────────────
    def shutdown(self):
        print("[SHUTDOWN] Cleaning up camera resources...")
        if self.capture_session:
            try: self.capture_session.close()
            except Exception: pass
        if self.camera_device:
            try: self.camera_device.close()
            except Exception: pass


# ─── MAIN LIFECYCLE ───────────────────────────────────────────────────────────
app = None

def onCreate():
    global app
    print("\n\n=======================================================")
    print(" Stratum: Booting  Camera App...")
    print("=======================================================\n")
    try:
        activity = stratum.getActivity()
        app = CameraApp(activity)
    except Exception as e:
        print(f"[FATAL BOOT ERROR] {e}")
        traceback.print_exc()

def onResume():
    global app
    if app is None:
        return
    # If camera not yet opened (e.g. permission was just granted),
    # check if surface is already available and retry
    if app.camera_device is None:
        surface_texture = app.texture_view.getSurfaceTexture()
        if surface_texture is not None:
            print("[onResume] Camera not open but surface ready — retrying...")
            app.on_surface_available(surface_texture, 0, 0)
def onPause():  pass
def onStop():   pass
def onDestroy():
    global app
    if app:
        app.shutdown()
        app = None

def start_camera():
    global app
    if app:
        app.start_camera()