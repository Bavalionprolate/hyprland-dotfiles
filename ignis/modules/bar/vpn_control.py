import subprocess

start_command = ["sudo", "systemctl", "start", "v2raya"]
stop_command = ["sudo", "systemctl", "stop", "v2raya"]
status_command = ["systemctl", "is-active", "v2raya"]

def start_vpn():
    result = subprocess.run(start_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode == 0

def stop_vpn():
    result = subprocess.run(stop_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode == 0

def check_vpn_status():
    result = subprocess.run(status_command, stdout=subprocess.PIPE)
    status = result.stdout.decode().strip()
    return status == "active"

def toggle_vpn():
    if check_vpn_status():
        return stop_vpn()
    else:
        return start_vpn()
