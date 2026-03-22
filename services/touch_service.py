"""Maps touchscreen taps to a callback."""
import struct
import threading
import os
import time

EV_KEY = 0x01
BTN_TOUCH = 0x14a
INPUT_EVENT_FORMAT = "llHHi"
INPUT_EVENT_SIZE = struct.calcsize(INPUT_EVENT_FORMAT)


def _touch_loop(event_device, callback):
    """Blocking loop that reads touch events and calls callback on tap."""
    try:
        fd = os.open(event_device, os.O_RDONLY)
    except OSError:
        return

    with os.fdopen(fd, "rb") as f:
        while True:
            try:
                data = f.read(INPUT_EVENT_SIZE)
                if len(data) < INPUT_EVENT_SIZE:
                    continue
                _, _, ev_type, ev_code, ev_value = struct.unpack(INPUT_EVENT_FORMAT, data)

                # BTN_TOUCH released (value=0) = tap completed
                if ev_type == EV_KEY and ev_code == BTN_TOUCH and ev_value == 0:
                    callback()
            except Exception:
                time.sleep(1)


def start_touch_listener(callback, event_device="/dev/input/event0"):
    """Start touch listener in a daemon thread. Calls callback on each tap."""
    t = threading.Thread(target=_touch_loop, args=(event_device, callback), daemon=True)
    t.start()
