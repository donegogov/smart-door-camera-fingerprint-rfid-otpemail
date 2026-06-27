# -*- coding: utf-8 -*-
# sledenje.py
#
# SunFounder Fusion HAT:
#   PAN  = P0
#   TILT = P1
#
# Реални Fusion HAT агли:
#   PAN:  -30° до +30°
#   TILT: -90° горе до -60° долу
#
# Во функцијата postavi(x, y) продолжуваме да користиме логички 0-180:
#   PAN 60  -> Fusion -30°
#   PAN 90  -> Fusion   0°
#   PAN 120 -> Fusion +30°
#
#   TILT 0  -> Fusion -90° горе
#   TILT 15 -> Fusion -75° средина
#   TILT 30 -> Fusion -60° долу

import time
import math
from enum import Enum

import cv2
from fusion_hat.servo import Servo

import config as cfg

import numpy as np


# ============================================================
#                    ВИД НА ДВИЖЕЊЕ
# ============================================================

class MovementPattern(Enum):
    RECTANGLE = "rectangle"
    ELLIPSE = "ellipse"
    CIRCLE = "circle"
    INFINITY = "infinity"


# ОВДЕ ЈА ИЗБИРАШ ФОРМАТА:
MOVEMENT_PATTERN = MovementPattern.ELLIPSE

# Примери:
# MOVEMENT_PATTERN = MovementPattern.RECTANGLE
# MOVEMENT_PATTERN = MovementPattern.ELLIPSE
# MOVEMENT_PATTERN = MovementPattern.CIRCLE
# MOVEMENT_PATTERN = MovementPattern.INFINITY


# Колку секунди трае еден цел круг/елипса/осмица.
# Поголема вредност = побавно.
MOVEMENT_CYCLE_SECONDS = getattr(
    cfg,
    "MOVEMENT_CYCLE_SECONDS",
    10.0
)


# ============================================================
#                         CONFIG
# ============================================================
# Најмалку 5% од сликата мора да биде еден голем moving object.
MOTION_MIN_BLOB_RATIO = getattr(
    cfg,
    "MOTION_MIN_BLOB_RATIO",
    0.05
)

# Ако повеќе од 35% од целата слика се сменило,
# најверојатно се движела камерата.
MOTION_MAX_SCENE_CHANGE = getattr(
    cfg,
    "MOTION_MAX_SCENE_CHANGE",
    0.35
)

# Минимална ширина/висина на moving object.
MOTION_MIN_WIDTH_RATIO = getattr(
    cfg,
    "MOTION_MIN_WIDTH_RATIO",
    0.10
)

MOTION_MIN_HEIGHT_RATIO = getattr(
    cfg,
    "MOTION_MIN_HEIGHT_RATIO",
    0.20
)

# Колку последователни frames мора да има големо движење.
MOTION_CONFIRM_FRAMES = getattr(
    cfg,
    "MOTION_CONFIRM_FRAMES",
    2
)

# Каде да цели во moving object.
# 0.0 е самиот врв, 0.5 е средина.
MOTION_HEAD_FACTOR = getattr(
    cfg,
    "MOTION_HEAD_FACTOR",
    0.18
)

# Максимално дозволено поместување на целата камера.
MOTION_MAX_CAMERA_SHIFT_RATIO = getattr(
    cfg,
    "MOTION_MAX_CAMERA_SHIFT_RATIO",
    0.15
)

_motion_confirm_count = 0
_motion_last_center = None

PCA_PAN_CHANNEL = getattr(
    cfg,
    "PCA_PAN_CHANNEL",
    "P0"
)

PCA_TILT_CHANNEL = getattr(
    cfg,
    "PCA_TILT_CHANNEL",
    "P1"
)

PAN_DIR = getattr(cfg, "PAN_DIR", 1)
TILT_DIR = getattr(cfg, "TILT_DIR", 1)


# Логички агли 0-180.
# Овие вредности ги даваат твоите физички Fusion агли.
PAN_MIN = getattr(cfg, "PAN_MIN", 60)
PAN_MAX = getattr(cfg, "PAN_MAX", 120)

TILT_MIN = getattr(cfg, "TILT_MIN", 0)
TILT_MAX = getattr(cfg, "TILT_MAX", 30)


PAN_CENTER = getattr(
    cfg,
    "PAN_CENTER",
    (PAN_MIN + PAN_MAX) / 2.0
)

TILT_CENTER = getattr(
    cfg,
    "TILT_CENTER",
    (TILT_MIN + TILT_MAX) / 2.0
)


SNAKE_PAN_MIN = getattr(
    cfg,
    "SNAKE_PAN_MIN",
    PAN_MIN
)

SNAKE_PAN_MAX = getattr(
    cfg,
    "SNAKE_PAN_MAX",
    PAN_MAX
)

SNAKE_TILT_UP = getattr(
    cfg,
    "SNAKE_TILT_UP",
    TILT_MIN
)

SNAKE_TILT_DOWN = getattr(
    cfg,
    "SNAKE_TILT_DOWN",
    TILT_MAX
)

SNAKE_CENTER_TILT = getattr(
    cfg,
    "SNAKE_CENTER_TILT",
    TILT_CENTER
)


# Брзина само за RECTANGLE режим.
# Степени во секунда.
SNAKE_SPEED = getattr(
    cfg,
    "SNAKE_SPEED",
    25.0
)

SNAKE_EPS = getattr(
    cfg,
    "SNAKE_EPS",
    0.7
)


# Motion detection config
MIN_AREA = getattr(cfg, "MIN_AREA", 800)

THRESHOLD_SENSITIVITY = getattr(
    cfg,
    "THRESHOLD_SENSITIVITY",
    25
)

BLUR_SIZE = getattr(
    cfg,
    "BLUR_SIZE",
    7
)

HEAD_FACTOR = getattr(
    cfg,
    "HEAD_FACTOR",
    0.35
)

verbose = getattr(
    cfg,
    "verbose",
    getattr(cfg, "VERBOSE", False)
)


# ============================================================
#                        SERVO INIT
# ============================================================

pan_servo = Servo(PCA_PAN_CHANNEL)
tilt_servo = Servo(PCA_TILT_CHANNEL)


# ============================================================
#                    ВНАТРЕШНИ ВРЕДНОСТИ
# ============================================================

_pan_radius = abs(
    SNAKE_PAN_MAX - SNAKE_PAN_MIN
) / 2.0

_tilt_radius = abs(
    SNAKE_TILT_DOWN - SNAKE_TILT_UP
) / 2.0

_pan_path_center = (
    SNAKE_PAN_MIN + SNAKE_PAN_MAX
) / 2.0

_tilt_path_center = (
    SNAKE_TILT_UP + SNAKE_TILT_DOWN
) / 2.0


# Rectangle/snake патеката останува како претходно:
# средина лево -> средина десно -> горе десно
# -> горе лево -> долу лево -> долу десно итн.
_RECTANGLE_POINTS = [
    (SNAKE_PAN_MIN, SNAKE_CENTER_TILT),
    (SNAKE_PAN_MAX, SNAKE_CENTER_TILT),

    (SNAKE_PAN_MAX, SNAKE_TILT_UP),
    (SNAKE_PAN_MIN, SNAKE_TILT_UP),

    (SNAKE_PAN_MIN, SNAKE_TILT_DOWN),
    (SNAKE_PAN_MAX, SNAKE_TILT_DOWN),

    (SNAKE_PAN_MAX, SNAKE_TILT_UP),
    (SNAKE_PAN_MIN, SNAKE_TILT_UP),

    (SNAKE_PAN_MIN, SNAKE_TILT_DOWN),
    (SNAKE_PAN_MAX, SNAKE_TILT_DOWN),
]


# Почетна позиција зависно од избраната форма.
if MOVEMENT_PATTERN == MovementPattern.RECTANGLE:
    _cur_x = float(SNAKE_PAN_MIN)
    _cur_y = float(SNAKE_CENTER_TILT)

elif MOVEMENT_PATTERN == MovementPattern.ELLIPSE:
    _cur_x = float(SNAKE_PAN_MAX)
    _cur_y = float(_tilt_path_center)

elif MOVEMENT_PATTERN == MovementPattern.CIRCLE:
    _circle_radius = min(_pan_radius, _tilt_radius)

    _cur_x = float(
        _pan_path_center + _circle_radius
    )
    _cur_y = float(_tilt_path_center)

else:
    # INFINITY почнува од средина.
    _cur_x = float(_pan_path_center)
    _cur_y = float(_tilt_path_center)


_rectangle_index = 1
_path_phase = 0.0
_last_tick_time = time.monotonic()

_last_pan_write = None
_last_tilt_write = None


# ============================================================
#                         HELPERS
# ============================================================

def _clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def _vo_fusion_agol(angle_0_180):
    """
    Претвора логички 0-180 во Fusion HAT -90..90.

    0   -> -90
    90  -> 0
    180 -> +90
    """
    return float(angle_0_180) - 90.0


def _write_servos(x, y):
    """
    Праќа агли до Fusion HAT.

    x и y се во логичкиот 0-180 систем.
    """

    global _last_pan_write
    global _last_tilt_write

    x = _clamp(
        float(x),
        PAN_MIN,
        PAN_MAX
    )

    y = _clamp(
        float(y),
        TILT_MIN,
        TILT_MAX
    )

    pan_angle = (
        _vo_fusion_agol(x) * PAN_DIR
    )

    tilt_angle = (
        _vo_fusion_agol(y) * TILT_DIR
    )

    pan_angle = int(
        round(
            _clamp(
                pan_angle,
                -90,
                90
            )
        )
    )

    tilt_angle = int(
        round(
            _clamp(
                tilt_angle,
                -90,
                90
            )
        )
    )

    # Не праќај иста вредност постојано.
    # Така има помалку зуење од сервата.
    if pan_angle != _last_pan_write:
        pan_servo.angle(pan_angle)
        _last_pan_write = pan_angle

    if tilt_angle != _last_tilt_write:
        tilt_servo.angle(tilt_angle)
        _last_tilt_write = tilt_angle

    if verbose:
        print(
            "PAN logical=%.2f fusion=%d | "
            "TILT logical=%.2f fusion=%d"
            % (
                x,
                pan_angle,
                y,
                tilt_angle
            )
        )

    return (
        int(round(x)),
        int(round(y))
    )


def _movement_position(pattern, phase):
    """
    Враќа x/y позиција за:
      ELLIPSE
      CIRCLE
      INFINITY

    phase оди од 0.0 до 1.0.
    """

    angle = (
        phase *
        2.0 *
        math.pi
    )

    if pattern == MovementPattern.ELLIPSE:
        x = (
            _pan_path_center +
            _pan_radius *
            math.cos(angle)
        )

        y = (
            _tilt_path_center +
            _tilt_radius *
            math.sin(angle)
        )

    elif pattern == MovementPattern.CIRCLE:
        radius = min(
            _pan_radius,
            _tilt_radius
        )

        x = (
            _pan_path_center +
            radius *
            math.cos(angle)
        )

        y = (
            _tilt_path_center +
            radius *
            math.sin(angle)
        )

    elif pattern == MovementPattern.INFINITY:
        # Хоризонтална осмица / infinity знак.
        x = (
            _pan_path_center +
            _pan_radius *
            math.sin(angle)
        )

        y = (
            _tilt_path_center +
            _tilt_radius *
            math.sin(2.0 * angle)
        )

    else:
        x = PAN_CENTER
        y = TILT_CENTER

    x = _clamp(
        x,
        PAN_MIN,
        PAN_MAX
    )

    y = _clamp(
        y,
        TILT_MIN,
        TILT_MAX
    )

    return x, y


# ============================================================
#                     ЈАВНИ ФУНКЦИИ
# ============================================================

def postavi(x, y):
    """
    Директно поставување на pan и tilt.

    x и y се во логички 0-180 систем.

    Примери:
        postavi(90, 15)  # центар
        postavi(60, 15)  # pan Fusion -30
        postavi(120, 15) # pan Fusion +30
        postavi(90, 0)   # tilt Fusion -90
        postavi(90, 30)  # tilt Fusion -60
    """

    global _cur_x
    global _cur_y
    global _last_tick_time

    _cur_x = _clamp(
        float(x),
        PAN_MIN,
        PAN_MAX
    )

    _cur_y = _clamp(
        float(y),
        TILT_MIN,
        TILT_MAX
    )

    _last_tick_time = time.monotonic()

    return _write_servos(
        _cur_x,
        _cur_y
    )


def zatvori_serva():
    """
    Ги враќа сервата во твојата реална средина:

      PAN  logical 90 -> Fusion 0°
      TILT logical 15 -> Fusion -75°
    """

    try:
        postavi(
            PAN_CENTER,
            TILT_CENTER
        )

    except Exception as error:
        if verbose:
            print(
                "zatvori_serva error:",
                error
            )


def snake_reset(start_x=None, start_y=None):
    """
    Го ресетира движењето според избраната форма.
    """

    global _cur_x
    global _cur_y

    global _rectangle_index
    global _path_phase
    global _last_tick_time

    _rectangle_index = 1
    _path_phase = 0.0
    _last_tick_time = time.monotonic()

    if start_x is not None:
        _cur_x = float(start_x)

    elif MOVEMENT_PATTERN == MovementPattern.RECTANGLE:
        _cur_x = float(SNAKE_PAN_MIN)

    elif MOVEMENT_PATTERN == MovementPattern.ELLIPSE:
        _cur_x = float(SNAKE_PAN_MAX)

    elif MOVEMENT_PATTERN == MovementPattern.CIRCLE:
        radius = min(
            _pan_radius,
            _tilt_radius
        )

        _cur_x = float(
            _pan_path_center + radius
        )

    else:
        _cur_x = float(
            _pan_path_center
        )

    if start_y is not None:
        _cur_y = float(start_y)

    elif MOVEMENT_PATTERN == MovementPattern.RECTANGLE:
        _cur_y = float(
            SNAKE_CENTER_TILT
        )

    else:
        _cur_y = float(
            _tilt_path_center
        )

    _cur_x = _clamp(
        _cur_x,
        PAN_MIN,
        PAN_MAX
    )

    _cur_y = _clamp(
        _cur_y,
        TILT_MIN,
        TILT_MAX
    )

    return _write_servos(
        _cur_x,
        _cur_y
    )


def snake_tick():
    """
    Non-blocking движење.

    Во главниот loop само повикувај:

        snake_tick()

    Формата автоматски ја зема од:

        MOVEMENT_PATTERN
    """

    global _cur_x
    global _cur_y

    global _rectangle_index
    global _path_phase
    global _last_tick_time

    now = time.monotonic()

    dt = now - _last_tick_time
    _last_tick_time = now

    # Ако главниот код бил блокиран подолго,
    # спречува ненадеен голем скок.
    dt = _clamp(
        dt,
        0.0,
        0.08
    )

    # --------------------------------------------------------
    # RECTANGLE / SNAKE
    # --------------------------------------------------------

    if MOVEMENT_PATTERN == MovementPattern.RECTANGLE:
        if not _RECTANGLE_POINTS:
            return _write_servos(
                _cur_x,
                _cur_y
            )

        target_x, target_y = (
            _RECTANGLE_POINTS[
                _rectangle_index
            ]
        )

        dx = float(target_x) - _cur_x
        dy = float(target_y) - _cur_y

        distance = math.sqrt(
            dx * dx + dy * dy
        )

        step = float(SNAKE_SPEED) * dt

        if distance <= max(
            step,
            SNAKE_EPS
        ):
            _cur_x = float(target_x)
            _cur_y = float(target_y)

            _rectangle_index = (
                _rectangle_index + 1
            ) % len(_RECTANGLE_POINTS)

        elif distance > 0:
            ratio = step / distance

            _cur_x += dx * ratio
            _cur_y += dy * ratio

    # --------------------------------------------------------
    # ELLIPSE / CIRCLE / INFINITY
    # --------------------------------------------------------

    else:
        cycle_seconds = max(
            1.0,
            float(
                MOVEMENT_CYCLE_SECONDS
            )
        )

        _path_phase += (
            dt / cycle_seconds
        )

        _path_phase %= 1.0

        _cur_x, _cur_y = (
            _movement_position(
                MOVEMENT_PATTERN,
                _path_phase
            )
        )

    return _write_servos(
        _cur_x,
        _cur_y
    )


def snake_loop(delay=0.02):
    """
    Самостоен тест на движењето.

    Ctrl+C за прекин.
    """

    snake_reset()

    print(
        "Movement pattern:",
        MOVEMENT_PATTERN.value
    )

    try:
        while True:
            snake_tick()
            time.sleep(delay)

    except KeyboardInterrupt:
        print("\nStop.")
        zatvori_serva()


def _stabiliziraj_motion_frame(gray1, gray2):
    """
    Се обидува да го компензира глобалното движење од pan/tilt.

    Ако камерата малку се поместила, вториот frame се враќа назад
    за да се споредува истата сцена.
    """

    height, width = gray1.shape[:2]

    # Работи на помала слика за да не го товари многу Raspberry Pi.
    detection_width = min(width, 320)
    scale = detection_width / float(width)

    small_width = max(64, int(width * scale))
    small_height = max(48, int(height * scale))

    small1 = cv2.resize(
        gray1,
        (small_width, small_height),
        interpolation=cv2.INTER_AREA
    )

    small2 = cv2.resize(
        gray2,
        (small_width, small_height),
        interpolation=cv2.INTER_AREA
    )

    small1 = cv2.GaussianBlur(small1, (7, 7), 0)
    small2 = cv2.GaussianBlur(small2, (7, 7), 0)

    try:
        shift, response = cv2.phaseCorrelate(
            np.float32(small1),
            np.float32(small2)
        )

        shift_x = shift[0] / scale
        shift_y = shift[1] / scale

    except Exception as error:
        if verbose:
            print("[MOTION] stabilization error:", error)

        return gray2, 0.0, 0.0, False

    maximum_x = width * MOTION_MAX_CAMERA_SHIFT_RATIO
    maximum_y = height * MOTION_MAX_CAMERA_SHIFT_RATIO

    camera_moved_too_much = (
        abs(shift_x) > maximum_x or
        abs(shift_y) > maximum_y
    )

    if camera_moved_too_much:
        return gray2, shift_x, shift_y, True

    # phaseCorrelate кажува колку се поместил frame2.
    # За да го порамниме, го враќаме во обратна насока.
    transform = np.float32([
        [1, 0, -shift_x],
        [0, 1, -shift_y]
    ])

    aligned = cv2.warpAffine(
        gray2,
        transform,
        (width, height),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REPLICATE
    )

    return aligned, shift_x, shift_y, False


def motion_centar(gray1, gray2):
    """
    Детектира само големи, стабилни движења.

    Игнорира:
      - ситни движења;
      - camera shake;
      - pan/tilt промена на целата слика;
      - сенки и мали промени;
      - еднократен noise.

    Враќа:
        (cx, head_y)

    head_y е точка во горниот дел од moving object,
    каде што приближно би требало да биде главата.
    """

    global _motion_confirm_count
    global _motion_last_center

    if gray1 is None or gray2 is None:
        _motion_confirm_count = 0
        _motion_last_center = None
        return None

    if gray1.shape != gray2.shape:
        _motion_confirm_count = 0
        _motion_last_center = None
        return None

    # Осигурај grayscale.
    if len(gray1.shape) == 3:
        gray1 = cv2.cvtColor(
            gray1,
            cv2.COLOR_BGR2GRAY
        )

    if len(gray2.shape) == 3:
        gray2 = cv2.cvtColor(
            gray2,
            cv2.COLOR_BGR2GRAY
        )

    height, width = gray1.shape[:2]
    frame_area = width * height

    # Компензација на движење од камерата.
    aligned_gray2, shift_x, shift_y, camera_moved_too_much = (
        _stabiliziraj_motion_frame(
            gray1,
            gray2
        )
    )

    if camera_moved_too_much:
        if verbose:
            print(
                "[MOTION] camera movement ignored:",
                "dx=%.1f dy=%.1f" % (
                    shift_x,
                    shift_y
                )
            )

        _motion_confirm_count = 0
        _motion_last_center = None
        return None

    blur_size = int(BLUR_SIZE)

    if blur_size < 3:
        blur_size = 3

    # GaussianBlur бара непарен број.
    if blur_size % 2 == 0:
        blur_size += 1

    frame1_blur = cv2.GaussianBlur(
        gray1,
        (blur_size, blur_size),
        0
    )

    frame2_blur = cv2.GaussianBlur(
        aligned_gray2,
        (blur_size, blur_size),
        0
    )

    difference = cv2.absdiff(
        frame1_blur,
        frame2_blur
    )

    # Поголем threshold за да не реагира на ситни промени.
    threshold_value = max(
        int(THRESHOLD_SENSITIVITY),
        35
    )

    _, motion_mask = cv2.threshold(
        difference,
        threshold_value,
        255,
        cv2.THRESH_BINARY
    )

    # Отстрани мал noise.
    small_kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (3, 3)
    )

    motion_mask = cv2.morphologyEx(
        motion_mask,
        cv2.MORPH_OPEN,
        small_kernel,
        iterations=2
    )

    # Спои делови од ист човек/голем објект.
    large_kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (11, 11)
    )

    motion_mask = cv2.morphologyEx(
        motion_mask,
        cv2.MORPH_CLOSE,
        large_kernel,
        iterations=2
    )

    motion_mask = cv2.dilate(
        motion_mask,
        large_kernel,
        iterations=1
    )

    # Игнорирај border создаден од стабилизацијата.
    border_x = min(
        width // 4,
        int(abs(shift_x)) + 8
    )

    border_y = min(
        height // 4,
        int(abs(shift_y)) + 8
    )

    if border_x > 0:
        motion_mask[:, :border_x] = 0
        motion_mask[:, width - border_x:] = 0

    if border_y > 0:
        motion_mask[:border_y, :] = 0
        motion_mask[height - border_y:, :] = 0

    changed_pixels = cv2.countNonZero(
        motion_mask
    )

    changed_ratio = (
        changed_pixels /
        float(frame_area)
    )

    # Ако премногу од сликата се сменило,
    # тоа е camera movement, светло или цела сцена.
    if changed_ratio > MOTION_MAX_SCENE_CHANGE:
        if verbose:
            print(
                "[MOTION] whole scene change ignored:",
                "%.1f%%" % (
                    changed_ratio * 100.0
                )
            )

        _motion_confirm_count = 0
        _motion_last_center = None
        return None

    contours_result = cv2.findContours(
        motion_mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if len(contours_result) == 3:
        _, contours, _ = contours_result
    else:
        contours, _ = contours_result

    minimum_area = max(
        float(MIN_AREA),
        frame_area * MOTION_MIN_BLOB_RATIO
    )

    minimum_width = width * MOTION_MIN_WIDTH_RATIO
    minimum_height = height * MOTION_MIN_HEIGHT_RATIO

    best_contour = None
    best_box = None
    best_area = 0.0

    for contour in contours:
        contour_area = cv2.contourArea(
            contour
        )

        if contour_area < minimum_area:
            continue

        x, y, box_width, box_height = cv2.boundingRect(
            contour
        )

        if box_width < minimum_width:
            continue

        if box_height < minimum_height:
            continue

        # Игнорирај многу тенки хоризонтални промени,
        # најчесто сенка, светло или camera tearing.
        aspect_ratio = (
            box_width /
            float(max(1, box_height))
        )

        if aspect_ratio > 3.5:
            continue

        if contour_area > best_area:
            best_area = contour_area
            best_contour = contour
            best_box = (
                x,
                y,
                box_width,
                box_height
            )

    if best_contour is None or best_box is None:
        _motion_confirm_count = 0
        _motion_last_center = None
        return None

    x, y, box_width, box_height = best_box

    center_x = int(
        x + box_width / 2
    )

    center_y = int(
        y + box_height / 2
    )

    current_center = (
        center_x,
        center_y
    )

    # Барај истото големо движење во повеќе frames.
    if _motion_last_center is None:
        _motion_confirm_count = 1

    else:
        previous_x, previous_y = _motion_last_center

        distance = math.sqrt(
            (center_x - previous_x) ** 2 +
            (center_y - previous_y) ** 2
        )

        maximum_confirmation_distance = (
            math.sqrt(
                width * width +
                height * height
            ) * 0.25
        )

        if distance <= maximum_confirmation_distance:
            _motion_confirm_count += 1
        else:
            _motion_confirm_count = 1

    _motion_last_center = current_center

    if _motion_confirm_count < MOTION_CONFIRM_FRAMES:
        if verbose:
            print(
                "[MOTION] waiting confirmation:",
                _motion_confirm_count,
                "/",
                MOTION_CONFIRM_FRAMES
            )

        return None

    # Не дозволувај counter-от бесконечно да расте.
    _motion_confirm_count = MOTION_CONFIRM_FRAMES

    # Цели кон горниот дел од објектот, односно кон глава.
    head_x = center_x

    head_y = int(
        y +
        box_height *
        MOTION_HEAD_FACTOR
    )

    head_y = max(
        0,
        min(
            height - 1,
            head_y
        )
    )

    if verbose:
        print(
            "[MOTION] GOLEM object:",
            "box=(%d,%d,%d,%d)" % (
                x,
                y,
                box_width,
                box_height
            ),
            "area=%d" % int(best_area),
            "scene=%.1f%%" % (
                changed_ratio * 100.0
            ),
            "target-head=(%d,%d)" % (
                head_x,
                head_y
            ),
            "camera-shift=(%.1f,%.1f)" % (
                shift_x,
                shift_y
            )
        )

    return (
        head_x,
        head_y
    )


# ============================================================
#                  DIRECT FILE TEST
# ============================================================

#if __name__ == "__main__":
#    snake_loop()