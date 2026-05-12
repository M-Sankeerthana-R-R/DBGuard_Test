# Root: project-root/monitor/slow_query_checker.py

import os
import datetime

THRESHOLD_SECONDS = 2  # Adjust as needed
SLOW_LOG_FILE = 'monitor/slow_queries.txt'

def check_slow_query(client_id, query, exec_time):
    if exec_time > THRESHOLD_SECONDS:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] SLOW QUERY by {client_id} ({exec_time:.2f}s):\n{query}\n\n"
        
        os.makedirs(os.path.dirname(SLOW_LOG_FILE), exist_ok=True)
        with open(SLOW_LOG_FILE, 'a') as f:
            f.write(log_entry)
