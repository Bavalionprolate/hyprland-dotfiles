import subprocess
import json
import re

def get_bluetooth_status():
  output = subprocess.check_output("bluetoothctl devices Connected", shell=True)
  output = output.decode('utf-8')
  lines = output.split('\n')
  devices = []
  for line in lines:
      if line.startswith('Device'):
          devices.append(line.split(' ')[1])
  return devices

def get_battery_status(device):
    output = subprocess.check_output(f"bluetoothctl info {device}", shell=True)
    output = output.decode('utf-8')
    lines = output.split('\n')
    for line in lines:
        if 'Battery Percentage' in line:
            battery_status = re.findall(r'\d+', line)[-1]
            return int(battery_status)
    return None


def get_battery_icon(battery_status):
   if battery_status >= 90:
       return '󰥈'
   elif battery_status >= 80:
       return '󰥅'
   elif battery_status >= 70:
       return '󰥄'
   elif battery_status >= 60:
       return '󰥃'
   elif battery_status >= 50:
       return '󰥂'
   elif battery_status >= 40:
       return '󰥁'
   elif battery_status >= 30:
       return '󰥀'
   elif battery_status >= 20:
       return '󰤿'
   elif battery_status >= 10:
       return '󰤾'
   else:
       return '󰤼'

def main():
    devices = get_bluetooth_status()
    if len(devices) > 1:
        print(json.dumps({
            'text': '󰂱',
            'tooltip': 'More than one device found'
        }))
    elif devices:
        if devices:
            for device in devices:
                battery_status = get_battery_status(device)
                if battery_status:
                    print(json.dumps({
                    'text': f'{battery_status} {get_battery_icon(battery_status)}',
                    'tooltip': f'Bluetooth device: {device}\nBattery status: {battery_status}'
                    }))

                else:
                    print(json.dumps({
                        'text': '',
                        'tooltip': f'Bluetooth device: {device}\nNo battery status available'
                    }))
        else:
            print(json.dumps({
                'text': '',
                'tooltip': ''
            }))

if __name__ == "__main__":
  main()