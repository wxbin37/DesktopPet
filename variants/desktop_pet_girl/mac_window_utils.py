"""macOS native window helpers."""
import platform
from ctypes import c_bool, c_char_p, c_long, c_ulong, c_void_p, cdll


IS_MAC = platform.system() == "Darwin"


if IS_MAC:
    objc = cdll.LoadLibrary("/usr/lib/libobjc.A.dylib")
    objc.sel_registerName.argtypes = [c_char_p]
    objc.sel_registerName.restype = c_void_p
    objc.objc_msgSend.restype = c_void_p


def _sel(name):
    return objc.sel_registerName(name.encode("utf-8"))


def _send(obj, selector, restype=c_void_p, argtypes=None, *args):
    objc.objc_msgSend.restype = restype
    objc.objc_msgSend.argtypes = [c_void_p, c_void_p] + list(argtypes or [])
    return objc.objc_msgSend(c_void_p(obj), _sel(selector), *args)


def apply_strong_topmost(widget):
    """Keep a PyQt widget above normal windows, spaces, and fullscreen apps."""
    if not IS_MAC:
        return False

    try:
        view = int(widget.winId())
        if not view:
            return False

        window = _send(view, "window")
        if not window:
            return False

        ns_status_window_level = 25
        can_join_all_spaces = 1 << 0
        stationary = 1 << 4
        full_screen_auxiliary = 1 << 8
        collection_behavior = (
            can_join_all_spaces | stationary | full_screen_auxiliary
        )

        _send(window, "setLevel:", None, [c_long], ns_status_window_level)
        _send(
            window,
            "setCollectionBehavior:",
            None,
            [c_ulong],
            collection_behavior,
        )
        hides_selector = _sel("setHidesOnDeactivate:")
        can_set_hides = _send(
            window,
            "respondsToSelector:",
            c_bool,
            [c_void_p],
            hides_selector,
        )
        if can_set_hides:
            _send(window, "setHidesOnDeactivate:", None, [c_bool], False)
        return True
    except Exception as exc:
        print(f"macOS 强置顶设置失败: {exc}")
        return False


def set_ignores_mouse_events(widget, enabled):
    """Let mouse clicks pass through the desktop pet window on macOS."""
    if not IS_MAC:
        return False

    try:
        view = int(widget.winId())
        if not view:
            return False

        window = _send(view, "window")
        if not window:
            return False

        _send(window, "setIgnoresMouseEvents:", None, [c_bool], bool(enabled))
        return True
    except Exception as exc:
        print(f"macOS 鼠标穿透设置失败: {exc}")
        return False
