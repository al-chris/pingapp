import sys
import traceback
from datetime import datetime, timezone
import time
import requests
import os
import json
import random
from jnius import autoclass, cast
from plyer import notification

def get_android_external_files_dir():
    """Get the Android external files directory path"""
    try:
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity = PythonActivity.mActivity
        context = cast('android.content.Context', activity)
        return context.getExternalFilesDir(None).getAbsolutePath()
    except:
        return None

def get_log_file_path(filename):
    """Get the appropriate log file path based on platform"""
    try:
        external_dir = get_android_external_files_dir()
        if external_dir:
            # We're on Android
            return os.path.join(external_dir, filename)
        else:
            # We're on desktop/development environment
            return os.path.join(os.path.dirname(__file__), filename)
    except Exception as e:
        print(f"Error getting log file path: {e}")
        return None

def log_to_file(message):
    """Helper function to log messages to a debug file"""
    try:
        debug_file = get_log_file_path('service_debug.log')
        if debug_file:
            os.makedirs(os.path.dirname(debug_file), exist_ok=True)
            with open(debug_file, 'a') as f:
                timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"Service debug log error: {e}")

def send_android_notification(title, message):
    """
    Send an Android notification using standard Android API
    
    Args:
        title (str): Title of the notification
        message (str): Content of the notification
    """
    try:
        # Import required Android classes
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        NotificationBuilder = autoclass('android.app.Notification$Builder')
        NotificationManager = autoclass('android.app.NotificationManager')
        NotificationChannel = autoclass('android.app.NotificationChannel')
        Context = autoclass('android.content.Context')
        Intent = autoclass('android.content.Intent')
        PendingIntent = autoclass('android.app.PendingIntent')
        String = autoclass('java.lang.String')
        
        # Get the current activity and context
        activity = PythonActivity.mActivity
        context = cast('android.content.Context', activity)
        
        # Create notification channel (required for Android 8.0 and above)
        channel_id = String('default')
        channel_name = String('Default Channel')
        channel_description = String('Default notifications channel')
        importance = NotificationManager.IMPORTANCE_DEFAULT
        
        channel = NotificationChannel(channel_id, channel_name, importance)
        channel.setDescription(channel_description)
        
        # Get the notification manager and create the channel
        notification_manager = cast(
            'android.app.NotificationManager',
            context.getSystemService(Context.NOTIFICATION_SERVICE)
        )
        notification_manager.createNotificationChannel(channel)
        
        # Create an intent
        intent = Intent(context, PythonActivity)
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK)
        
        # Create a PendingIntent with FLAG_IMMUTABLE
        pending_intent = PendingIntent.getActivity(
            context,
            0,
            intent,
            PendingIntent.FLAG_IMMUTABLE
        )
        
        # Build the notification
        notification_builder = NotificationBuilder(context, channel_id)
        notification_builder.setContentTitle(String(title))
        notification_builder.setContentText(String(message))
        notification_builder.setSmallIcon(context.getApplicationInfo().icon)
        notification_builder.setAutoCancel(True)
        notification_builder.setContentIntent(pending_intent)
        
        # Show the notification
        notification_manager.notify(1, notification_builder.build())
        
    except Exception as e:
        print(f"Error sending notification: {e}")

def get_formatted_time():
    """Returns current time in UTC format YYYY-MM-DD HH:MM:SS"""
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

def log_message(message, success=True):
    """Write log message to a file that the main app can read"""
    try:
        timestamp = get_formatted_time()
        log_entry = {
            'timestamp': timestamp,
            'message': message,
            'success': success
        }
        
        # Get the service logs file path
        log_file = get_log_file_path('service_logs.json')
        
        if not log_file:
            print("Error: Could not determine log file path")
            return
            
        # Ensure directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception as e:
        print(f"Error writing to log file: {e}")

def main():
    try:
        log_to_file("Service main() started")
        
        # Get the PythonService instance after the service has started
        PythonService = autoclass('org.kivy.android.PythonService')
        if PythonService and PythonService.mService:
            PythonService.mService.setAutoRestartService(True)
            log_to_file("Auto-restart service enabled")
        
        # Log service start
        log_message("Service started", True)
        
        # Try to send initial notification
        try:
            send_android_notification(
                "Service Started",
                "Endpoint monitoring service is now running"
            )
        except Exception as e:
            log_to_file(f"Failed to send initial notification: {e}")
        
        endpoints = ["https://vasset-kezx.onrender.com/api/v1/utils/health-check/"]
        base_interval = 55
        extra_interval_min = 5
        extra_interval_max = 10

        while True:
            try:
                current_time = get_formatted_time()
                log_to_file(f"Service running at {current_time}")
                
                for endpoint in endpoints:
                    try:
                        response = requests.get(endpoint, timeout=30)
                        if response.ok:
                            message = f"✓ Successfully pinged {endpoint}: {response.status_code}"
                            log_message(message, True)
                        else:
                            message = f"⚠ Ping failed for {endpoint}: {response.status_code}"
                            log_message(message, False)
                    except Exception as e:
                        message = f"✗ Error pinging {endpoint}: {str(e)}"
                        log_message(message, False)
                
                sleep_time = base_interval + random.randint(extra_interval_min, extra_interval_max)
                time.sleep(sleep_time)
                
            except Exception as e:
                log_to_file(f"Error in service main loop: {e}\n{traceback.format_exc()}")
                time.sleep(60)  # Wait a minute before retrying
                
    except Exception as e:
        log_to_file(f"Service main() crashed: {e}\n{traceback.format_exc()}")

# if __name__ == '__main__':
#     try:
#         log_to_file("Service starting from __main__")
#         main()
#     except Exception as e:
#         log_to_file(f"Service crashed from __main__: {e}\n{traceback.format_exc()}")

try:
    log_to_file("Service starting from ping_service")
    main()
except Exception as e:
    log_to_file(f"Service crashed from ping_service: {e}\n{traceback.format_exc()}")