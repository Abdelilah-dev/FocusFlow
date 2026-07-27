import sys
import os

def resource_path(*parts):
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, *parts)


def app_data_path(*parts):
    base = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "FocusFlow")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, *parts)


def get_asset_path(*parts):
    appdata = app_data_path(*parts)
    if os.path.exists(appdata):
        return appdata
    return resource_path(*parts)