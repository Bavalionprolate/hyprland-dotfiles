import os
from ignis.utils import Utils
from ignis.app import IgnisApp
import argparse

STATE_FILE = os.path.expanduser("~/.cache/ignis_control_center_state")
os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)

def read_state() -> bool:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            state = f.read().strip()
        return state == "open"
    return False

def write_state(opened: bool):

    with open(STATE_FILE, "w") as f:
        f.write("open" if opened else "closed")
    print(f"Control Center state updated to {'open' if opened else 'closed'}")

def close():
    if read_state():
        Utils.exec_sh_async("ignis close ignis_CONTROL_CENTER")
        write_state(False)

def toggle_control_center(button=None):
    if read_state():
        close()
    else:
        Utils.exec_sh_async("ignis open ignis_CONTROL_CENTER")
        write_state(True)

def main():
    parser = argparse.ArgumentParser(description="Управление Control Center")
    parser.add_argument(
        '-toggle',
        action='store_true',
        help="Открыть или закрыть Control Center"
    )
    parser.add_argument(
        '-close',
        action='store_true',
        help="Закрыть Control Center"
    )
    args = parser.parse_args()

    if args.toggle:
        toggle_control_center()
    elif args.close:
        close()

if __name__ == "__main__":
    main()
