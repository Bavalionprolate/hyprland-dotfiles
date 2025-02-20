import subprocess

# Команды для управления службой
start_command = ["sudo", "systemctl", "start", "v2raya"]
stop_command = ["sudo", "systemctl", "stop", "v2raya"]
status_command = ["systemctl", "is-active", "v2raya"]

def start_vpn():
    """Функция для включения VPN"""
    result = subprocess.run(start_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode == 0

def stop_vpn():
    """Функция для выключения VPN"""
    result = subprocess.run(stop_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode == 0

def check_vpn_status():
    """Функция для проверки состояния VPN"""
    result = subprocess.run(status_command, stdout=subprocess.PIPE)
    status = result.stdout.decode().strip()
    return status == "active"

def toggle_vpn():
    """Функция для переключения состояния VPN"""
    if check_vpn_status():
        return stop_vpn()
    else:
        return start_vpn()