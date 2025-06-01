# PingApp

A simple Python/Kivy app to keep a render server awake, designed with Android support.

## Features

- Keeps the device/server awake using scheduled pings
- Built with [Kivy](https://kivy.org/) for cross-platform UI
- Android-specific permission handling (e.g., WAKE_LOCK, FOREGROUND_SERVICE)
- Log file support for debugging
- Custom UI components (buttons, log display)
- Modular structure for easy extension

## Getting Started

### Prerequisites

- Python 3.8+
- [Kivy](https://kivy.org/doc/stable/gettingstarted/installation.html)
- On Android: [python-for-android](https://github.com/kivy/python-for-android) or [Buildozer](https://github.com/kivy/buildozer)
- Jnius for Android bindings (`pyjnius`)
- (Optional) Other Kivy dependencies for mobile deployment

### Installation

#### On Desktop

```bash
# Clone the repo
git clone https://github.com/al-chris/pingapp.git
cd pingapp

# Install dependencies
pip install kivy pyjnius
```

#### On Android

1. Use [Buildozer](https://github.com/kivy/buildozer) to compile the app for Android.
2. Ensure required permissions are set in your buildozer.spec:
    ```
    android.permissions = INTERNET, WAKE_LOCK, FOREGROUND_SERVICE, POST_NOTIFICATIONS, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, SYSTEM_ALERT_WINDOW
    ```
3. Build and deploy:
    ```bash
    buildozer android debug deploy run
    ```

## Usage

Run the main app locally:

```bash
python main.py
```

- On Android, the app will request permissions at runtime.
- Log files are stored in the app’s directory (or Android’s external files directory).

## Project Structure

- `main.py` – Main application logic, Android integration, custom widgets
- (If present) `.kv` files – Kivy layout definitions
- `debug.log` – Log output for debugging

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

Currently unlicensed. Please contact the repository owner for more information.

## Acknowledgments

- [Kivy](https://kivy.org/)
- [Pyjnius](https://github.com/kivy/pyjnius)
- [Buildozer](https://github.com/kivy/buildozer)

---
