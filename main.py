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
import random
import requests
import time
from datetime import datetime, timezone
import threading

kivy.require('2.1.0')

class CustomButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0.8, 0.2, 0.2, 1)
        
    def on_press(self):
        # Create animation for button press
        anim = Animation(background_color=(0.6, 0.1, 0.1, 1), duration=0.1)
        anim.start(self)

    def on_release(self):
        # Animate back to original color
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
        """Clear all logs immediately"""
        def clear_and_add_header(dt):
            self.log_layout.clear_widgets()
            # Add a header to show logs were cleared
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            self.add_log(f"[{timestamp}] Logs cleared by user: al-chris", True)
        
        # Execute immediately on the next frame
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
        
        # Bind the clear button to the new clear_logs method
        self.main_layout.control_panel.clear_button.bind(
            on_release=lambda x: self.main_layout.log_display.clear_logs()
        )
        
        # Start with an initial log message
        Clock.schedule_once(
            lambda dt: self.main_layout.log_display.add_log(
                f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}] System started - Monitoring endpoints...",
                True
            )
        )
        
        # Start the ping function in a separate thread
        threading.Thread(target=self.run_ping_function, daemon=True).start()
        
        return self.main_layout

    def run_ping_function(self):
        endpoints = ["https://vasset-kezx.onrender.com/api/v1/utils/health-check/"]
        self.ping_endpoints(endpoints)

    def update_log(self, message: str, success: bool = True):
        """Update the log in the UI thread."""
        Clock.schedule_once(lambda dt: self.main_layout.log_display.add_log(message, success))

    def ping_endpoints(
        self, 
        endpoints: list[str], 
        base_interval: int = 55, 
        extra_interval_min: int = 5, 
        extra_interval_max: int = 10, 
        base_pings: int = 1000
    ) -> None:
        for _ in range(base_pings):
            endpoint = random.choice(endpoints)
            try:
                response = requests.get(endpoint)
                timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                
                if response.ok:
                    message = f"[{timestamp}] ✓ Successfully pinged {endpoint}: {response.status_code}"
                    self.update_log(message, True)
                else:
                    message = f"[{timestamp}] ⚠ Ping failed for {endpoint}: {response.status_code}"
                    self.update_log(message, False)
                    
            except Exception as e:
                timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                message = f"[{timestamp}] ✗ Error pinging {endpoint}: {str(e)}"
                self.update_log(message, False)
                
            time.sleep(base_interval + random.randint(extra_interval_min, extra_interval_max))

if __name__ == "__main__":
    PingApp().run()