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
from jnius import autoclass
from kivy.utils import platform

if platform == "android":
    from android import loadingscreen
    from android.permissions import request_permissions, Permission
    loadingscreen.hide_loading_screen()
    request_permissions([Permission.WRITE_EXTERNAL_STORAGE])

# Constants
SERVICE_NAME = 'Ping_service'
PACKAGE_DOMAIN = 'com.alchris'
PACKAGE_NAME = 'pinger'

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
    def build(self):

        self.main_layout = MainLayout()
        self.main_layout.control_panel.clear_button.bind(
            on_release=lambda x: self.main_layout.log_display.clear_logs()
        )

        # Start the background service
        self.start_background_service()
        
        # Start the log reader
        Clock.schedule_interval(self.read_service_logs, 1.0)
        
        return self.main_layout

    def start_background_service(self):
        try:
            # Get the service class
            service = autoclass(f'{PACKAGE_DOMAIN}.{PACKAGE_NAME}.Service{SERVICE_NAME}')

            # Get the Python activity
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            
            # Create log file path
            log_file = os.path.join(activity.getExternalFilesDir(None).getAbsolutePath(), 'service_logs.json')
            
            # Start the service
            service.start(activity, 'app_icon', 'Ping Service', 'Monitoring endpoints...', log_file)
            
            # Log service start
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            self.main_layout.log_display.add_log(
                f"[{timestamp}] Background service started", True
            )
        except Exception as e:
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            self.main_layout.log_display.add_log(
                f"[{timestamp}] Error starting service: {str(e)}", False
            )

    def read_service_logs(self, dt):
        try:
            # Get the Python activity
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            log_file = os.path.join(activity.getApplicationContext().getExternalFilesDir(None).getAbsolutePath(), 'service_logs.json')
            # log_file = os.path.join(os.getcwd(), "services", "service_logs.json")
            
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                
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
            print(f"Error reading service logs: {e}")

if __name__ == "__main__":
    PingApp().run()