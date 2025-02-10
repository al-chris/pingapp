from datetime import datetime, timezone
import time
import requests
import os
import json
import random
from jnius import autoclass
from plyer import notification

# Get the PythonService instance
PythonService = autoclass('org.kivy.android.PythonService')
# Enable auto-restart
PythonService.mService.setAutoRestartService(True)

def send_android_notification(title, message):
    """
    Send an Android notification using Plyer
    
    Args:
        title (str): Title of the notification
        message (str): Content of the notification
    """
    try:
        notification.notify(
            title=title,
            message=message,
            app_name='MyAndroidApp',  # Your app name
            timeout=10,  # Display duration in seconds
            toast=False  # False for persistent notification, True for toast
        )
    except Exception as e:
        print(f"Error sending notification: {e}")

def get_formatted_time():
    """Returns current time in UTC format YYYY-MM-DD HH:MM:SS"""
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

def log_message(message, success=True):
    """Write log message to a file that the main app can read"""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        'timestamp': timestamp,
        'message': message,
        'success': success
    }
    
    # Get the service argument which contains the log file path
    log_file = os.environ.get('PYTHON_SERVICE_ARGUMENT', 'service_logs.json')
    # log_file = os.path.join(os.getcwd(), 'service_logs.json')
    
    try:
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception as e:
        print(f"Error writing to log file: {e}")

def main():
    endpoints = ["https://vasset-kezx.onrender.com/api/v1/utils/health-check/"]
    base_interval = 55
    extra_interval_min = 5
    extra_interval_max = 10

    while True:

        user = "al-chris"
        current_time = "2025-02-10 00:55:09"  # Using the provided time
        
        # Example notification
        title = f"Hello {user}!"
        message = (f"Current UTC Time: {current_time}\n"
                f"This is your Android notification.")
        
        send_android_notification(title, message)

        endpoint = endpoints[0]  # Since we only have one endpoint
        try:
            response = requests.get(endpoint)
            if response.ok:
                message = f"✓ Successfully pinged {endpoint}: {response.status_code}"
                log_message(message, True)
            else:
                message = f"⚠ Ping failed for {endpoint}: {response.status_code}"
                log_message(message, False)
        except Exception as e:
            message = f"✗ Error pinging {endpoint}: {str(e)}"
            log_message(message, False)
        
        time.sleep(base_interval + random.randint(extra_interval_min, extra_interval_max))

if __name__ == '__main__':
    main()