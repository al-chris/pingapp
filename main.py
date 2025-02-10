import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.properties import StringProperty, ObjectProperty
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.gridlayout import GridLayout
from kivy.animation import Animation
import json
import os
from datetime import datetime, timezone
import threading
from jnius import autoclass, cast
from kivy.utils import platform

from kivy.logger import Logger
from kivy.base import EventLoop


if platform == "android":
    try:
        from android.permissions import request_permissions, Permission, check_permission
        # from android import loadingscreen
        
        # Hide loading screen
        # loadingscreen.hide_loading_screen()
        
        # Request all necessary permissions
        permissions = [
            Permission.INTERNET,
            Permission.WAKE_LOCK,
            Permission.FOREGROUND_SERVICE,
            Permission.POST_NOTIFICATIONS,
            Permission.READ_EXTERNAL_STORAGE,
            Permission.WRITE_EXTERNAL_STORAGE,
            Permission.SYSTEM_ALERT_WINDOW
        ]
        
        for permission in permissions:
            if not check_permission(permission):
                request_permissions([permission])
    except Exception as e:
        print(f"Error setting up Android permissions: {e}")

# Constants
SERVICE_NAME = 'Ping_service'
PACKAGE_DOMAIN = 'com.alchris'
PACKAGE_NAME = 'pinger'

def get_android_external_files_dir():
    """Get the Android external files directory path"""
    try:
        from android import mActivity
        context = mActivity.getApplicationContext()
        return context.getExternalFilesDir(None).getAbsolutePath()
    except:
        return None

def get_log_file_path(filename):
    """Get the appropriate log file path based on platform"""
    try:
        if platform == "android":
            external_dir = get_android_external_files_dir()
            if external_dir:
                return os.path.join(external_dir, filename)
        return os.path.join(os.path.dirname(__file__), filename)
    except Exception as e:
        print(f"Error getting log file path: {e}")
        return None

def log_to_file(message):
    """Helper function to log messages to a debug file"""
    try:
        debug_file = get_log_file_path('debug.log')
        if debug_file:
            os.makedirs(os.path.dirname(debug_file), exist_ok=True)
            with open(debug_file, 'a') as f:
                timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"Error writing to debug log: {e}")

class CustomButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0.8, 0.2, 0.2, 1)
        
    def on_press(self):
        anim = Animation(background_color=(0.6, 0.1, 0.1, 1), duration=0.1)
        anim.start(self)

    def on_release(self):
        anim = Animation(background_color=(0.8, 0.2, 0.2, 1), duration=0.1)
        anim.start(self)

class LogDisplay(ScrollView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, 1)
        self.do_scroll_x = False
        self.bar_width = dp(10)
        self.scroll_type = ['bars', 'content']
        self.bar_color = [0.5, 0.5, 0.5, 0.7]
        self.bar_inactive_color = [0.5, 0.5, 0.5, 0.4]
        
        self.log_layout = GridLayout(
            cols=1,
            spacing=dp(2),
            padding=dp(5),
            size_hint_y=None
        )
        self.log_layout.bind(minimum_height=self.log_layout.setter('height'))
        self.add_widget(self.log_layout)

    def add_log(self, message, success=True):
        label = Label(
            text=message,
            size_hint_y=None,
            markup=True,
            padding=(dp(10), dp(5))
        )
        
        wrap_width = Window.width - dp(50)
        label.text_size = (wrap_width, None)
        
        label.bind(texture_size=lambda instance, size: setattr(instance, 'height', size[1]))
        label.bind(width=lambda instance, width: setattr(instance, 'text_size', (wrap_width, None)))
        
        if "Error" in message:
            label.color = (1, 0.3, 0.3, 1)
        elif not success:
            label.color = (1, 0.6, 0, 1)
        else:
            label.color = (0.3, 1, 0.3, 1)
        
        self.log_layout.add_widget(label)
        Clock.schedule_once(lambda dt: setattr(self, 'scroll_y', 0))

    def clear_logs(self):
        def clear_and_add_header(dt):
            self.log_layout.clear_widgets()
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            self.add_log(f"[{timestamp}] Logs cleared by user: al-chris", True)
        Clock.schedule_once(clear_and_add_header, 0)

class ControlPanel(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(50)
        self.padding = dp(10)
        self.spacing = dp(10)

        self.clear_button = CustomButton(
            text='Clear Logs',
            size_hint=(0.3, 1),
            font_size=dp(16),
            bold=True
        )
        self.add_widget(self.clear_button)

        self.status_label = Label(
            text='Status: Running',
            size_hint=(0.7, 1),
            halign='right'
        )
        self.add_widget(self.status_label)

class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(10)
        self.spacing = dp(10)
        
        self.content = BoxLayout(
            orientation='vertical',
            spacing=dp(10),
            size_hint=(1, 1)
        )

        self.header = Label(
            text='[b]Endpoint Monitoring System[/b]',
            markup=True,
            size_hint_y=None,
            height=dp(40)
        )
        self.content.add_widget(self.header)

        self.log_display = LogDisplay()
        self.content.add_widget(self.log_display)

        self.control_panel = ControlPanel()
        self.content.add_widget(self.control_panel)
        
        self.add_widget(self.content)

class PingApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Add this to track if build has been called
        self._built = False
        
    def build(self):
        try:
            Logger.info("PingApp: Starting build()")
            self._built = True
            
            # Create main layout
            self.main_layout = MainLayout()
            
            # Bind clear button
            self.main_layout.control_panel.clear_button.bind(
                on_release=lambda x: self.main_layout.log_display.clear_logs()
            )

            # Schedule service start after a short delay
            Clock.schedule_once(self.start_background_service, 2)
            
            # Start the log reader
            Clock.schedule_interval(self.read_service_logs, 1.0)
            
            # Add error checking
            if not self.main_layout:
                Logger.error("PingApp: Main layout is None!")
                return BoxLayout()  # Return a default widget if main_layout fails
                
            Logger.info("PingApp: build() completed successfully")
            return self.main_layout
            
        except Exception as e:
            Logger.error(f"PingApp: Error in build(): {e}")
            # Return a default widget in case of error
            return BoxLayout()

    def on_start(self):
        try:
            Logger.info("PingApp: on_start() called")
            super().on_start()
            
            # Add this to ensure the window is shown
            # EventLoop.window.show()
            
        except Exception as e:
            Logger.error(f"PingApp: Error in on_start(): {e}")

    def on_pause(self):
        # This is important for Android lifecycle
        Logger.info("PingApp: on_pause() called")
        return True  # Prevents app from being stopped

    def on_resume(self):
        Logger.info("PingApp: on_resume() called")
        # Refresh the display if needed
        if hasattr(self, 'main_layout'):
            Clock.schedule_once(lambda dt: self.main_layout.log_display.clear_logs(), 0.1)

    def start_background_service(self, dt=None):
        try:
            log_to_file("Attempting to start background service...")

            from services.ping_service import send_android_notification

            send_android_notification(title="Al-Chris", message="Attempting to start background service...")
            
            if platform != "android":
                log_to_file("Not on Android platform")
                return

            # Get the service class
            service = autoclass(f'{PACKAGE_DOMAIN}.{PACKAGE_NAME}.Service{SERVICE_NAME}')

            
            from android import mActivity
            
            # Get the Python activity
            context = mActivity.getApplicationContext()
            
            # Get the log file path using our new function
            log_file = get_log_file_path('service_logs.json')
            if not log_file:
                raise Exception("Could not determine log file path")
                
            log_to_file(f"Log file path: {log_file}")
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            # Start the service
            service.start(mActivity, '', 'Ping Service', 'Monitoring endpoints...', log_file)
            
            # Log service start
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            self.main_layout.log_display.add_log(
                f"[{timestamp}] Background service started", True
            )
            log_to_file("Service start command issued successfully")

            return service
            
        except Exception as e:
            error_msg = f"Error starting service: {str(e)}"
            log_to_file(error_msg)
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            self.main_layout.log_display.add_log(
                f"[{timestamp}] {error_msg}", False
            )

    def stop_service(self, dt=None):
        if platform == "android":
            from android import mActivity
            context = mActivity.getApplicationContext()


            SERVICE_NAME = f'{PACKAGE_DOMAIN}.{PACKAGE_NAME}.Service{SERVICE_NAME}'

            Service = autoclass(SERVICE_NAME)

            Intent = autoclass('android.content.Intent')
            service_intent = Intent(mActivity, Service)


            mActivity.stopService(service_intent)


    def read_service_logs(self, dt):
        try:
            if platform != "android":
                return
            
            log_file = get_log_file_path('service_logs.json')
            if not log_file:
                return
            
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                
                if lines:  # Only clear if we have lines to process
                    # Clear the file
                    with open(log_file, 'w') as f:
                        pass
                    
                    # Process each line
                    for line in lines:
                        try:
                            log_entry = json.loads(line.strip())
                            message = f"[{log_entry['timestamp']}] {log_entry['message']}"
                            self.main_layout.log_display.add_log(message, log_entry['success'])
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            log_to_file(f"Error reading service logs: {e}")

if __name__ == "__main__":
    try:
        Logger.info("Main: Starting PingApp")
        app = PingApp()
        app.run()
    except Exception as e:
        Logger.error(f"Main: App crashed: {e}")
        log_to_file(f"App crashed: {e}")