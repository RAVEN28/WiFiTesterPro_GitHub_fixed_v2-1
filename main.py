# Build entry point only.
# The application logic remains in wifi_auto.py unchanged.
from wifi_auto import WiFiTesterApp


if __name__ == "__main__":
    WiFiTesterApp().run()
