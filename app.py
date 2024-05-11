from __future__ import annotations
import re
import pytz
import psutil
from datetime import datetime
from typing import Tuple, Dict
from flask import Flask, render_template

app = Flask(__name__)

def convert_to_metric(bytes_value: int) -> Tuple[float, str]:
    metric_units = ('KB', 'MB', 'GB', 'TB')
    if bytes_value < 1024:
        return bytes_value, 'B'
    result = bytes_value
    for unit in metric_units:
        result /= 1024
        if 1 <= result < 1000:
            return result, unit
    return result, metric_units[-1]

def format_dict_keys_and_values(source_dict: Dict[str, int|float]) -> Dict[str, str]:
    dict_formatted_values = {}
    for k,v in source_dict.items():
        k_title = k.title()
        if k == 'percent':
            dict_formatted_values[k_title] = f'{v:0.1f}%'
        else:
            converted_size, units = convert_to_metric(bytes_value=v)
            dict_formatted_values[k_title] = f'{converted_size:.1f} {units}'
    return dict_formatted_values

def latest_cron_status() -> list[str]:
    cron_statuses = []
    try:
        with open('/var/log/godaddy_update_cron_last_status.log','r') as log:
            cron_status = log.read()
            match = re.search(r'(.*?)Exit status: ([0|1])', cron_status)
            if match:
                status = match.group(2)
                if status == "0":
                    cron_statuses.append(match.group(1) + " - OK")
                else:
                    cron_statuses.append(match.group(1) + " - Down")
            else:
                cron_statuses.append(cron_status)

    except Exception as e:
        return list(str(e))
    else:
        return cron_statuses


@app.route("/")
def home_page():
    current_datetime = datetime.now(pytz.timezone('US/Eastern'))
    ## cpu
    cpu_usage = [
        f'CPU Core {i+1}: {perc:.1f}%'
        for i, perc 
        in enumerate(psutil.cpu_percent(interval=1, percpu=True))
    ]
    ## memory
    memory = [f'{k}: {v}' for k,v in psutil.virtual_memory()._asdict().items()]
    memory = psutil.virtual_memory()._asdict()
    memory = format_dict_keys_and_values(memory)
    memory_formatted = [f'{k}: {v}' for k,v in memory.items()]
    ## disk
    disk = psutil.disk_usage(
            '/media/carboni/0d90e20d-8496-43aa-837c-f6cadd09b9fe'
        )._asdict()
    disk = format_dict_keys_and_values(disk)
    disk_formatted = [f'{k}: {v}' for k,v in disk.items()]
    ## cron jobs
    dynamic_dns = latest_cron_status()
    ## combined
    stats = {
        'cpu': cpu_usage,
        'memory': memory_formatted,
        'disk': disk_formatted,
        'time': current_datetime,
        'cron': dynamic_dns
    }
    return render_template('show_stats.html', **stats)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
