# -*- coding: utf-8 -*-
# kamera.py
#
# Поддржува:
#   1. Raspberry Pi CSI камера преку Picamera2
#   2. USB webcam преку OpenCV + директен V4L2 backend
#
# Важно:
#   USB камерата се отвора со cv2.CAP_V4L2, не преку GStreamer.
#   Thread-от се stop/join, а камерата се release при излез.

import time
from threading import Thread, Event, Lock, current_thread

import cv2
import config as cfg

from picamera2 import Picamera2
from libcamera import Transform


# ============================================================
#                         CONFIG
# ============================================================

CAMERA_WIDTH = getattr(cfg, "CAMERA_WIDTH", 640)
CAMERA_HEIGHT = getattr(cfg, "CAMERA_HEIGHT", 480)
CAMERA_FRAMERATE = getattr(cfg, "CAMERA_FRAMERATE", 20)

CAMERA_HFLIP = bool(getattr(cfg, "CAMERA_HFLIP", False))
CAMERA_VFLIP = bool(getattr(cfg, "CAMERA_VFLIP", False))

# За твојата USB камера:
WEBCAM_SRC = getattr(cfg, "WEBCAM_SRC", "/dev/video0")
WEBCAM_WIDTH = getattr(cfg, "WEBCAM_WIDTH", 1280)
WEBCAM_HEIGHT = getattr(cfg, "WEBCAM_HEIGHT", 720)
WEBCAM_FRAMERATE = getattr(
    cfg,
    "WEBCAM_FRAMERATE",
    CAMERA_FRAMERATE
)

WEBCAM_HFLIP = bool(
    getattr(cfg, "WEBCAM_HFLIP", CAMERA_HFLIP)
)

WEBCAM_VFLIP = bool(
    getattr(cfg, "WEBCAM_VFLIP", CAMERA_VFLIP)
)


def _normaliziraj_camera_source(source):
    """
    '0' го претвора во 0.
    '/dev/video0' останува string.
    """

    if isinstance(source, str):
        source = source.strip()

        if source.isdigit():
            return int(source)

    return source


def _flip_frame(frame, hflip=False, vflip=False):
    if frame is None:
        return None

    if hflip and vflip:
        return cv2.flip(frame, -1)

    if hflip:
        return cv2.flip(frame, 1)

    if vflip:
        return cv2.flip(frame, 0)

    return frame


# ============================================================
#                    PICAMERA2 / CSI CAMERA
# ============================================================

class PiVideoStream:
    def __init__(
        self,
        resolution=(CAMERA_WIDTH, CAMERA_HEIGHT),
        framerate=CAMERA_FRAMERATE,
        stream="main",
        rotation=0,
        hflip=CAMERA_HFLIP,
        vflip=CAMERA_VFLIP
    ):
        self.stream = stream
        self.array = None
        self.stopped = False

        self._thread = None
        self._stop_event = Event()
        self._frame_lock = Lock()

        self.camera = Picamera2(camera_num=0)

        properties = self.camera.camera_properties

        full_res = properties.get(
            "PixelArraySize",
            None
        )

        best_mode = None

        try:
            modes = self.camera.sensor_modes

            if modes:
                best_mode = max(
                    modes,
                    key=lambda mode: (
                        mode["size"][0] *
                        mode["size"][1]
                    )
                )

                if full_res is None:
                    full_res = best_mode["size"]

        except Exception as error:
            print(
                "[KAMERA] Ne mozam da procitam sensor modes:",
                error
            )

        config_args = {
            "main": {
                "size": resolution,
                "format": "RGB888"
            },
            "transform": Transform(
                hflip=int(bool(hflip)),
                vflip=int(bool(vflip))
            ),
            "controls": {
                "FrameRate": float(framerate)
            }
        }

        if best_mode is not None:
            config_args["raw"] = {
                "size": best_mode["size"]
            }

        camera_config = (
            self.camera.create_video_configuration(
                **config_args
            )
        )

        self.camera.configure(camera_config)

        # Full FoV само за CSI camera.
        if full_res is not None:
            try:
                self.camera.set_controls({
                    "ScalerCrop": (
                        0,
                        0,
                        int(full_res[0]),
                        int(full_res[1])
                    )
                })

            except Exception as error:
                print(
                    "[KAMERA] ScalerCrop ne moze da se postavi:",
                    error
                )

        self.camera.start()

        # Дај ѝ малку време да добие прв frame.
        time.sleep(0.25)

    def start(self):
        if self._thread is not None and self._thread.is_alive():
            return self

        self.stopped = False
        self._stop_event.clear()

        self._thread = Thread(
            target=self.update,
            name="PiVideoStream",
            daemon=False
        )

        self._thread.start()

        return self

    def update(self):
        while not self._stop_event.is_set():
            try:
                frame = self.camera.capture_array(
                    self.stream
                )

                if frame is not None:
                    with self._frame_lock:
                        self.array = frame

            except Exception as error:
                if self._stop_event.is_set():
                    break

                print(
                    "[KAMERA] Picamera2 frame error:",
                    error
                )

                time.sleep(0.05)

    def read(self):
        with self._frame_lock:
            return self.array

    def stop(self):
        if self.stopped:
            return

        self.stopped = True
        self._stop_event.set()

        if (
            self._thread is not None and
            self._thread.is_alive() and
            self._thread is not current_thread()
        ):
            self._thread.join(timeout=2.0)

        try:
            self.camera.stop()
        except Exception:
            pass

        if (
            self._thread is not None and
            self._thread.is_alive() and
            self._thread is not current_thread()
        ):
            self._thread.join(timeout=1.0)

        try:
            self.camera.close()
        except Exception:
            pass

        self._thread = None

        print("[KAMERA] Picamera2 zatvorena.")


# ============================================================
#                       USB WEBCAM
# ============================================================

class WebcamVideoStream:
    def __init__(
        self,
        CAM_SRC=WEBCAM_SRC,
        CAM_WIDTH=WEBCAM_WIDTH,
        CAM_HEIGHT=WEBCAM_HEIGHT,
        CAM_FRAMERATE=WEBCAM_FRAMERATE,
        hflip=WEBCAM_HFLIP,
        vflip=WEBCAM_VFLIP
    ):
        self.camera_source = _normaliziraj_camera_source(
            CAM_SRC
        )

        self.width = int(CAM_WIDTH)
        self.height = int(CAM_HEIGHT)
        self.framerate = int(CAM_FRAMERATE)

        self.hflip = bool(hflip)
        self.vflip = bool(vflip)

        self.stream = None
        self.frame = None
        self.grabbed = False
        self.stopped = False

        self._thread = None
        self._stop_event = Event()
        self._frame_lock = Lock()
        self._capture_lock = Lock()

        self._consecutive_failures = 0

        self._open_camera()

    def _try_open(
        self,
        width,
        height,
        fourcc=None
    ):
        """
        Отвора директно преку Linux V4L2.
        Со ова не се користи GStreamer pipeline.
        """

        capture = cv2.VideoCapture(
            self.camera_source,
            cv2.CAP_V4L2
        )

        if not capture.isOpened():
            capture.release()
            return None, None

        # Намали latency и стари frames.
        try:
            capture.set(
                cv2.CAP_PROP_BUFFERSIZE,
                1
            )
        except Exception:
            pass

        if fourcc:
            capture.set(
                cv2.CAP_PROP_FOURCC,
                cv2.VideoWriter_fourcc(*fourcc)
            )

        capture.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            int(width)
        )

        capture.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            int(height)
        )

        capture.set(
            cv2.CAP_PROP_FPS,
            int(self.framerate)
        )

        # Почекај USB камерата да почне да дава frames.
        frame = None
        grabbed = False

        for _ in range(25):
            grabbed, frame = capture.read()

            if grabbed and frame is not None:
                break

            time.sleep(0.04)

        if not grabbed or frame is None:
            capture.release()
            return None, None

        frame = _flip_frame(
            frame,
            self.hflip,
            self.vflip
        )

        return capture, frame

    def _open_camera(self):
        """
        Пробај повеќе стандардни USB webcam формати.

        Прво MJPG бидејќи обично поддржува 720p/1080p.
        Ако не работи, пробува YUYV и 640x480 fallback.
        """

        attempts = [
            # width, height, format
            (self.width, self.height, "MJPG"),
            (self.width, self.height, "YUYV"),
            (self.width, self.height, None),

            # Безбеден fallback
            (640, 480, "MJPG"),
            (640, 480, "YUYV"),
            (640, 480, None),
        ]

        for width, height, fourcc in attempts:
            print(
                "[KAMERA] Probuvam USB camera:",
                self.camera_source,
                "%dx%d" % (width, height),
                fourcc or "default format"
            )

            capture, frame = self._try_open(
                width,
                height,
                fourcc
            )

            if capture is not None and frame is not None:
                self.stream = capture
                self.frame = frame
                self.grabbed = True

                real_width = int(
                    capture.get(
                        cv2.CAP_PROP_FRAME_WIDTH
                    )
                )

                real_height = int(
                    capture.get(
                        cv2.CAP_PROP_FRAME_HEIGHT
                    )
                )

                real_fps = capture.get(
                    cv2.CAP_PROP_FPS
                )

                real_fourcc_number = int(
                    capture.get(
                        cv2.CAP_PROP_FOURCC
                    )
                )

                real_fourcc = "".join([
                    chr(
                        (real_fourcc_number >> (8 * i))
                        & 0xFF
                    )
                    for i in range(4)
                ])

                print(
                    "[KAMERA] USB camera otvorena:",
                    "%dx%d" % (
                        real_width,
                        real_height
                    ),
                    "fps=%.1f" % real_fps,
                    "format=%s" % real_fourcc
                )

                return

            time.sleep(0.15)

        raise RuntimeError(
            "Ne mozam da ja otvoram USB kamerata %r. "
            "Proveri dali e /dev/video0 i dali drug proces ja koristi."
            % self.camera_source
        )

    def start(self):
        if self._thread is not None and self._thread.is_alive():
            return self

        if self.stream is None or not self.stream.isOpened():
            raise RuntimeError(
                "USB kamerata ne e otvorena."
            )

        self.stopped = False
        self._stop_event.clear()

        self._thread = Thread(
            target=self.update,
            name="WebcamVideoStream",
            daemon=False
        )

        self._thread.start()

        return self

    def update(self):
        while not self._stop_event.is_set():
            try:
                with self._capture_lock:
                    if (
                        self.stream is None or
                        not self.stream.isOpened()
                    ):
                        break

                    grabbed, frame = self.stream.read()

                if grabbed and frame is not None:
                    frame = _flip_frame(
                        frame,
                        frame = cv2.flip(frame, 0)
                    )

                    with self._frame_lock:
                        self.grabbed = True
                        self.frame = frame

                    self._consecutive_failures = 0

                else:
                    self._consecutive_failures += 1

                    if self._consecutive_failures == 10:
                        print(
                            "[KAMERA] USB camera ne dava frames."
                        )

                    time.sleep(0.03)

            except Exception as error:
                if self._stop_event.is_set():
                    break

                print(
                    "[KAMERA] USB read error:",
                    error
                )

                time.sleep(0.05)

    def read(self):
        with self._frame_lock:
            return self.frame

    def stop(self):
        """
        Прво го известува thread-от да заврши,
        потоа прави join и release на VideoCapture.
        """

        if self.stopped:
            return

        self.stopped = True
        self._stop_event.set()

        if (
            self._thread is not None and
            self._thread.is_alive() and
            self._thread is not current_thread()
        ):
            self._thread.join(timeout=2.0)

        with self._capture_lock:
            if self.stream is not None:
                try:
                    self.stream.release()
                except Exception:
                    pass

                self.stream = None

        if (
            self._thread is not None and
            self._thread.is_alive() and
            self._thread is not current_thread()
        ):
            self._thread.join(timeout=1.0)

        self._thread = None

        with self._frame_lock:
            self.grabbed = False
            self.frame = None

        print("[KAMERA] USB camera zatvorena.")