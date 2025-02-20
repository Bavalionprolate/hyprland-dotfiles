import argparse
import os
from ignis.utils import Utils
from ignis.app import IgnisApp 

STATE_FILE = os.path.expanduser("~/.cache/ignis_control_center_state")

def read_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            state = f.read().strip()
        return state == "open"
    return False

def write_state(state):
    with open(STATE_FILE, "w") as f:
        f.write("open" if state else "closed")

def close(button=None):
    control_center_open = read_state()

    if control_center_open:
        Utils.exec_sh_async("ignis close ignis_CONTROL_CENTER")
        write_state(False)
        print("Control Center закрыт")

def toggle_control_center(button=None):
    control_center_open = read_state()

    if control_center_open:
        close()
    else:
        Utils.exec_sh_async("ignis open ignis_CONTROL_CENTER")
        write_state(True)
        print("Control Center открыт")


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

# Запуск через терминал
if __name__ == "__main__":
    main()
