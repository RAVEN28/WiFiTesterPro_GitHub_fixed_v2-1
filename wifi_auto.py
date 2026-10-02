"""
WiFi Tester Pro - Professional Edition (v2.1)
================================================
تطبيق احترافي متكامل لتحليل شبكات الواي فاي واختبار كلمات المرور.

الميزات الاحترافية الكاملة:
- عرض كامل لتفاصيل كل شبكة (SSID, BSSID, Signal, Security, Channel, Band)
- مؤشرات إشارة ملونة بأشرطة مرئية
- إحصائيات مباشرة (Total / Secured / Open / Best)
- معلومات الشبكة المتصلة (IP, Speed, Signal, MAC)
- ترتيب ذكي حسب قوة الإشارة
- تحديث تلقائي (Auto-Scan)
- تصدير السجل إلى Download
- إدارة ملفات الباسوردات (إنشاء / استيراد / حذف / اختيار)
- واجهة Material Design داكنة عصرية
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.progressbar import ProgressBar
from kivy.uix.popup import Popup
from kivy.graphics import Color, RoundedRectangle
from kivy.clock import Clock, mainthread
from kivy.utils import platform, get_color_from_hex
from kivy.core.window import Window
from kivy.metrics import dp, sp
from datetime import datetime
import os
import threading
import re


# ======================================================
#  🎨 الألوان
# ======================================================

COLORS = {
    "bg":        "#0F1419",
    "surface":   "#1A1F26",
    "surface2":  "#242A32",
    "surface3":  "#2E353F",
    "primary":   "#00D9A3",
    "primary_d": "#00A87E",
    "accent":    "#00B4D8",
    "danger":    "#FF4D6D",
    "warning":   "#FFB700",
    "success":   "#00E676",
    "text":      "#E8EAED",
    "text_dim":  "#8A929C",
    "border":    "#2A3038",
    "sig_excellent": "#00E676",
    "sig_good":      "#00D9A3",
    "sig_fair":      "#FFB700",
    "sig_weak":      "#FF8C42",
    "sig_poor":      "#FF4D6D",
    "sec_wpa3":  "#9D4EDD",
    "sec_wpa2":  "#00B4D8",
    "sec_wep":   "#FFB700",
    "sec_open":  "#FF4D6D",
}


# ======================================================
#  📱 جسر Android
# ======================================================

ANDROID = (platform == "android")

if ANDROID:
    from jnius import autoclass, cast
    from android.permissions import request_permissions, Permission
    from android import activity

    Context               = autoclass("android.content.Context")
    WifiManager           = autoclass("android.net.wifi.WifiManager")
    WifiNetworkSuggestion = autoclass("android.net.wifi.WifiNetworkSuggestion")
    PythonActivity        = autoclass("org.kivy.android.PythonActivity")
    Build                 = autoclass("android.os.Build$VERSION")
    Settings              = autoclass("android.provider.Settings")
    Intent                = autoclass("android.content.Intent")
    VERSION               = autoclass("android.os.Build$VERSION")


# ======================================================
#  🔓 الأذونات
# ======================================================

def request_android_permissions():
    if not ANDROID:
        return
    perms = [
        Permission.ACCESS_WIFI_STATE,
        Permission.CHANGE_WIFI_STATE,
        Permission.ACCESS_FINE_LOCATION,
        Permission.ACCESS_COARSE_LOCATION,
        Permission.ACCESS_NETWORK_STATE,
        Permission.CHANGE_NETWORK_STATE,
    ]
    try:
        perms.append("android.permission.NEARBY_WIFI_DEVICES")
    except Exception:
        pass
    request_permissions(perms)


def has_location_permission():
    if not ANDROID:
        return True
    try:
        activity_obj = PythonActivity.mActivity
        return activity_obj.checkSelfPermission(
            "android.permission.ACCESS_FINE_LOCATION"
        ) == 0
    except Exception:
        return False


# ======================================================
#  🔧 أدوات مساعدة
# ======================================================

def signal_to_percent(level):
    if level <= -90:
        return 0
    if level >= -30:
        return 100
    return int(2 * (level + 100))


def signal_color(level):
    if level >= -50:
        return COLORS["sig_excellent"]
    elif level >= -60:
        return COLORS["sig_good"]
    elif level >= -70:
        return COLORS["sig_fair"]
    elif level >= -80:
        return COLORS["sig_weak"]
    else:
        return COLORS["sig_poor"]


def signal_quality(level):
    if level >= -50:
        return "EXCELLENT"
    elif level >= -60:
        return "GOOD"
    elif level >= -70:
        return "FAIR"
    elif level >= -80:
        return "WEAK"
    else:
        return "POOR"


def signal_bars(level):
    if level >= -50:
        return "▂▄▆█"
    elif level >= -60:
        return "▂▄▆_"
    elif level >= -70:
        return "▂▄__"
    elif level >= -80:
        return "▂___"
    else:
        return "____"


def freq_to_band(freq):
    if freq <= 0:
        return "?", "Unknown"
    if 2400 <= freq <= 2500:
        return "2.4 GHz", "2.4G"
    if 5150 <= freq <= 5850:
        return "5 GHz", "5G"
    if 5925 <= freq <= 7125:
        return "6 GHz", "6G"
    return "?", f"{freq} MHz"


def freq_to_channel(freq):
    if 2412 <= freq <= 2484:
        if freq == 2484:
            return 14
        return (freq - 2407) // 5
    if 5000 <= freq <= 5900:
        return (freq - 5000) // 5
    if 5955 <= freq <= 7115:
        return (freq - 5955) // 5 + 1
    return 0


def security_type(capabilities):
    if not capabilities:
        return "OPEN", COLORS["sec_open"], "🔓"
    cap = capabilities.upper()
    if "WPA3" in cap or "SAE" in cap:
        return "WPA3", COLORS["sec_wpa3"], "🛡️"
    if "WPA2" in cap:
        return "WPA2", COLORS["sec_wpa2"], "🔒"
    if "WPA" in cap:
        return "WPA", COLORS["sec_wpa2"], "🔒"
    if "WEP" in cap:
        return "WEP", COLORS["sec_wep"], "⚠️"
    if "ESS" in cap:
        return "OPEN", COLORS["sec_open"], "🔓"
    return "UNKNOWN", COLORS["text_dim"], "❔"


# ======================================================
#  📡 قراءة الشبكات
# ======================================================

def scan_wifi_networks():
    if not ANDROID:
        return [
            {"ssid": "MyHomeWiFi", "bssid": "AA:BB:CC:11:22:33",
             "level": -42, "frequency": 2437, "capabilities": "[WPA2-PSK-CCMP]",
             "channel": 6, "band": "2.4 GHz",
             "security": "WPA2", "sec_color": COLORS["sec_wpa2"], "sec_icon": "🔒",
             "percent": signal_to_percent(-42), "quality": signal_quality(-42),
             "color": signal_color(-42), "bars": signal_bars(-42)},
            {"ssid": "TP-Link_5G", "bssid": "AA:BB:CC:44:55:66",
             "level": -55, "frequency": 5180, "capabilities": "[WPA3-SAE]",
             "channel": 36, "band": "5 GHz",
             "security": "WPA3", "sec_color": COLORS["sec_wpa3"], "sec_icon": "🛡️",
             "percent": signal_to_percent(-55), "quality": signal_quality(-55),
             "color": signal_color(-55), "bars": signal_bars(-55)},
            {"ssid": "Cafe_Free", "bssid": "AA:BB:CC:77:88:99",
             "level": -75, "frequency": 2462, "capabilities": "[ESS]",
             "channel": 11, "band": "2.4 GHz",
             "security": "OPEN", "sec_color": COLORS["sec_open"], "sec_icon": "🔓",
             "percent": signal_to_percent(-75), "quality": signal_quality(-75),
             "color": signal_color(-75), "bars": signal_bars(-75)},
            {"ssid": "Neighbor_WiFi", "bssid": "AA:BB:CC:AA:BB:CC",
             "level": -85, "frequency": 5745, "capabilities": "[WPA2-PSK]",
             "channel": 149, "band": "5 GHz",
             "security": "WPA2", "sec_color": COLORS["sec_wpa2"], "sec_icon": "🔒",
             "percent": signal_to_percent(-85), "quality": signal_quality(-85),
             "color": signal_color(-85), "bars": signal_bars(-85)},
        ]

    if not has_location_permission():
        return []

    try:
        activity = PythonActivity.mActivity
        wifi = cast(
            "android.net.wifi.WifiManager",
            activity.getApplicationContext()
                    .getSystemService(Context.WIFI_SERVICE)
        )
        try:
            wifi.startScan()
        except Exception:
            pass

        results = wifi.getScanResults()
        if not results:
            return []

        networks = []
        seen = set()
        for r in results:
            try:
                ssid = r.SSID
                bssid = r.BSSID
                level = r.level
                freq = r.frequency
                caps = r.capabilities
                if not ssid or ssid in seen:
                    continue
                seen.add(ssid)

                sec_name, sec_color, sec_icon = security_type(caps)
                band, _ = freq_to_band(freq)
                channel = freq_to_channel(freq)

                networks.append({
                    "ssid": ssid, "bssid": bssid, "level": level,
                    "frequency": freq, "capabilities": caps,
                    "channel": channel, "band": band,
                    "security": sec_name, "sec_color": sec_color,
                    "sec_icon": sec_icon,
                    "percent": signal_to_percent(level),
                    "quality": signal_quality(level),
                    "color": signal_color(level),
                    "bars": signal_bars(level),
                })
            except Exception:
                continue

        networks.sort(key=lambda n: n["level"], reverse=True)
        return networks
    except Exception as e:
        print(f"❌ Scan error: {e}")
        return []


def get_connection_info():
    if not ANDROID:
        return {"connected": True, "ssid": "MyHomeWiFi",
                "bssid": "AA:BB:CC:11:22:33", "ip": "192.168.1.42",
                "link_speed": 433, "rssi": -42, "frequency": 2437}
    try:
        activity = PythonActivity.mActivity
        wifi = cast(
            "android.net.wifi.WifiManager",
            activity.getApplicationContext()
                    .getSystemService(Context.WIFI_SERVICE)
        )
        info = wifi.getConnectionInfo()
        if not info or not info.getSSID():
            return {"connected": False}

        ssid = info.getSSID().strip('"')
        if ssid == "<unknown ssid>" or not ssid:
            return {"connected": False}

        ip_int = info.getIpAddress()
        ip = f"{(ip_int & 0xFF)}.{(ip_int >> 8) & 0xFF}." \
             f"{(ip_int >> 16) & 0xFF}.{(ip_int >> 24) & 0xFF}"

        return {
            "connected": True,
            "ssid": ssid,
            "bssid": info.getBSSID() or "—",
            "ip": ip,
            "link_speed": info.getLinkSpeed(),
            "rssi": info.getRssi(),
            "frequency": info.getFrequency(),
        }
    except Exception as e:
        print(f"Connection info error: {e}")
        return {"connected": False}


# ======================================================
#  📶 إرسال الاقتراحات
# ======================================================

def suggest_wifi(ssid, password):
    if not ANDROID:
        return True
    try:
        if VERSION.SDK_INT < 29:
            return False
        suggestion = (WifiNetworkSuggestion.Builder()
                      .setSsid(ssid)
                      .setWpa2Passphrase(password)
                      .build())
        activity = PythonActivity.mActivity
        wifi = cast(
            "android.net.wifi.WifiManager",
            activity.getApplicationContext()
                    .getSystemService(Context.WIFI_SERVICE)
        )
        return wifi.addNetworkSuggestions([suggestion]) == 0
    except Exception:
        return False


def clear_suggestions():
    if not ANDROID:
        return
    try:
        activity = PythonActivity.mActivity
        wifi = cast(
            "android.net.wifi.WifiManager",
            activity.getApplicationContext()
                    .getSystemService(Context.WIFI_SERVICE)
        )
        wifi.removeNetworkSuggestions([])
    except Exception:
        pass


def open_wifi_settings():
    if not ANDROID:
        return
    try:
        intent = Intent(Settings.ACTION_WIFI_SETTINGS)
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        PythonActivity.mActivity.startActivity(intent)
    except Exception:
        pass


# ======================================================
#  📁 إدارة ملفات الباسوردات
# ======================================================

DEFAULT_PASSWORDS = [
    "12345678", "password", "admin123", "qwerty123",
    "iloveyou", "hErO20HeWa50", "letmein",
    "welcome123", "abc12345", "P@ssw0rd!",
]


def get_files_dir():
    if ANDROID:
        try:
            from android.storage import app_storage_path
            path = os.path.join(app_storage_path(), "passwords")
        except Exception:
            path = "passwords"
    else:
        path = "passwords"
    os.makedirs(path, exist_ok=True)
    return path


def list_password_files():
    files_dir = get_files_dir()
    files = [{"name": "default", "path": None,
              "count": len(DEFAULT_PASSWORDS), "builtin": True}]
    try:
        for fname in sorted(os.listdir(files_dir)):
            if fname.endswith(".txt"):
                fpath = os.path.join(files_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        count = len([
                            l for l in f
                            if l.strip() and not l.startswith("#")
                        ])
                    files.append({"name": fname, "path": fpath,
                                  "count": count, "builtin": False})
                except Exception:
                    continue
    except Exception:
        pass
    return files


def read_file_passwords(fpath):
    if fpath is None:
        return None
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            return [l.strip() for l in f
                    if l.strip() and not l.startswith("#")]
    except Exception:
        return None


def delete_password_file(fpath):
    if fpath is None:
        return False
    try:
        os.remove(fpath)
        return True
    except Exception:
        return False


def save_password_file(name, content):
    files_dir = get_files_dir()
    if not name.endswith(".txt"):
        name += ".txt"
    fpath = os.path.join(files_dir, name)
    try:
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)
        return fpath
    except Exception:
        return None


def import_passwords_from_path(src_path):
    try:
        import shutil
        files_dir = get_files_dir()
        name = os.path.basename(src_path)
        if not name.endswith(".txt"):
            name += ".txt"
        dst = os.path.join(files_dir, name)
        shutil.copy(src_path, dst)
        return dst
    except Exception:
        return None


# ======================================================
#  🧱 مكونات واجهة
# ======================================================

class Card(BoxLayout):
    def __init__(self, bg_color=None, radius=16, **kwargs):
        super().__init__(**kwargs)
        self.bg_color = get_color_from_hex(bg_color or COLORS["surface"])
        self.radius = dp(radius)
        with self.canvas.before:
            self._color = Color(*self.bg_color)
            self._rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[self.radius]
            )
        self.bind(pos=self._update, size=self._update)

    def _update(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size


class PrimaryButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_color = (0, 0, 0, 0)
        self.color = get_color_from_hex("#0F1419")
        self.bold = True
        self.font_size = sp(16)
        self.bg = get_color_from_hex(COLORS["primary"])
        with self.canvas.before:
            self._color = Color(*self.bg)
            self._rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(14)]
            )
        self.bind(pos=self._update, size=self._update)

    def _update(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def set_color(self, hex_color):
        self.bg = get_color_from_hex(hex_color)
        self._color.rgba = self.bg


class SecondaryButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_color = (0, 0, 0, 0)
        self.color = get_color_from_hex(COLORS["primary"])
        self.bold = True
        self.font_size = sp(13)
        with self.canvas.before:
            self._border = Color(*get_color_from_hex(COLORS["border"]))
            self._rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(14)]
            )
        self.bind(pos=self._update, size=self._update)

    def _update(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size


class SignalBar(BoxLayout):
    def __init__(self, percent, color, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(6)
        self.percent = percent
        self.bar_color = get_color_from_hex(color)
        with self.canvas:
            Color(*get_color_from_hex(COLORS["surface3"]))
            self._bg = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(3)]
            )
            self._color = Color(*self.bar_color)
            self._bar = RoundedRectangle(
                pos=self.pos, size=(0, self.height), radius=[dp(3)]
            )
        self.bind(pos=self._update, size=self._update)

    def _update(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._bar.pos = self.pos
        self._bar.size = (self.width * self.percent / 100, self.height)


class NetworkRow(BoxLayout):
    def __init__(self, network, on_select, **kwargs):
        super().__init__(**kwargs)
        self.network = network
        self.on_select = on_select
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(110)
        self.padding = [dp(14), dp(10)]
        self.spacing = dp(6)

        with self.canvas.before:
            self._color = Color(*get_color_from_hex(COLORS["surface2"]))
            self._rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(12)]
            )
        self.bind(pos=self._update, size=self._update)

        # السطر 1
        line1 = BoxLayout(size_hint_y=None, height=dp(26), spacing=dp(8))
        line1.add_widget(Label(
            text=network["bars"], font_size=sp(14),
            color=get_color_from_hex(network["color"]),
            size_hint=(None, 1), width=dp(50), halign="left",
        ))
        line1.add_widget(Label(
            text=network["ssid"], font_size=sp(15), bold=True,
            color=get_color_from_hex(COLORS["text"]),
            halign="left", valign="middle",
        ))
        line1.add_widget(Label(
            text=network["sec_icon"], font_size=sp(14),
            size_hint=(None, 1), width=dp(28),
        ))
        self.add_widget(line1)

        # السطر 2
        line2 = BoxLayout(size_hint_y=None, height=dp(12), spacing=dp(8))
        line2.add_widget(SignalBar(network["percent"], network["color"]))
        line2.add_widget(Label(
            text=f"{network['percent']}%", font_size=sp(11), bold=True,
            color=get_color_from_hex(network["color"]),
            size_hint=(None, 1), width=dp(42), halign="right",
        ))
        self.add_widget(line2)

        # السطر 3
        details = (
            f"[color={COLORS['text_dim']}]"
            f"📶 {network['level']} dBm  •  {network['quality']}  "
            f"•  {network['band']}  •  Ch {network['channel']}  •  [/color]"
            f"[color={network['sec_color']}][b]{network['security']}[/b][/color]"
        )
        self.add_widget(Label(
            text=details, font_size=sp(10), markup=True,
            halign="left", valign="middle",
            size_hint_y=None, height=dp(16),
        ))

        # السطر 4
        self.add_widget(Label(
            text=f"[color={COLORS['text_dim']}]🔗 {network['bssid']}[/color]",
            font_size=sp(10), markup=True,
            halign="left", valign="middle",
            size_hint_y=None, height=dp(16),
        ))

    def _update(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.on_select(self.network)
            return True
        return super().on_touch_down(touch)


class FileRow(BoxLayout):
    """صف لملف باسوردات."""
    def __init__(self, file_info, selected, on_select, **kwargs):
        super().__init__(**kwargs)
        self.file_info = file_info
        self.on_select = on_select
        self.size_hint_y = None
        self.height = dp(46)
        self.padding = [dp(10), dp(6)]
        self.spacing = dp(8)

        bg = COLORS["surface3"] if selected else COLORS["surface2"]
        with self.canvas.before:
            self._color = Color(*get_color_from_hex(bg))
            self._rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(10)]
            )
        self.bind(pos=self._update, size=self._update)

        icon = "⭐" if file_info["builtin"] else "📄"
        self.add_widget(Label(
            text=icon, font_size=sp(15),
            size_hint=(None, 1), width=dp(26),
        ))

        name_color = COLORS["primary"] if selected else COLORS["text"]
        self.add_widget(Label(
            text=file_info["name"], font_size=sp(13), bold=selected,
            color=get_color_from_hex(name_color),
            halign="left", valign="middle",
        ))

        self.add_widget(Label(
            text=f"{file_info['count']} pwds", font_size=sp(11),
            color=get_color_from_hex(COLORS["text_dim"]),
            size_hint=(None, 1), width=dp(64), halign="right",
        ))

        if selected:
            self.add_widget(Label(
                text="✓", font_size=sp(15),
                color=get_color_from_hex(COLORS["success"]),
                size_hint=(None, 1), width=dp(20),
            ))

    def _update(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.on_select(self.file_info)
            return True
        return super().on_touch_down(touch)


# ======================================================
#  🖥️ التطبيق
# ======================================================

class WiFiTesterApp(App):
    def build(self):
        self.title = "WiFi Tester Pro"
        Window.clearcolor = get_color_from_hex(COLORS["bg"])

        if ANDROID:
            Clock.schedule_once(lambda dt: request_android_permissions(), 1.5)

        self.passwords = list(DEFAULT_PASSWORDS)
        self.selected_file = "default"
        self.running = False
        self.index = 0
        self.networks = []
        self.auto_scan_event = None

        root = BoxLayout(orientation="vertical")
        root.add_widget(self._build_header())

        scroll = ScrollView(do_scroll_x=False)
        content = BoxLayout(
            orientation="vertical",
            padding=[dp(16), dp(8), dp(16), dp(16)],
            spacing=dp(14),
            size_hint_y=None,
        )
        content.bind(minimum_height=content.setter("height"))

        content.add_widget(self._build_connection_card())
        content.add_widget(self._build_stats_card())
        content.add_widget(self._build_networks_card())
        content.add_widget(self._build_input_card())
        content.add_widget(self._build_files_card())     # ← جديد
        content.add_widget(self._build_control_card())
        content.add_widget(self._build_progress_card())
        content.add_widget(self._build_log_card())

        scroll.add_widget(content)
        root.add_widget(scroll)

        Clock.schedule_once(lambda dt: self.scan_networks(None), 2.5)
        Clock.schedule_once(lambda dt: self.update_connection_info(None), 3.0)

        return root

    # ---------- الهيدر ----------
    def _build_header(self):
        header = Card(
            bg_color=COLORS["surface"], radius=0,
            size_hint_y=None, height=dp(70),
            padding=[dp(20), dp(14)],
        )
        inner = BoxLayout(orientation="horizontal", spacing=dp(12))

        icon_box = BoxLayout(size_hint=(None, None), size=(dp(44), dp(44)))
        with icon_box.canvas.before:
            Color(*get_color_from_hex(COLORS["primary"]))
            icon_box._circle = RoundedRectangle(
                pos=icon_box.pos, size=icon_box.size, radius=[dp(22)]
            )
        icon_box.bind(
            pos=lambda *a: setattr(icon_box._circle, "pos", icon_box.pos),
            size=lambda *a: setattr(icon_box._circle, "size", icon_box.size),
        )
        icon_box.add_widget(Label(text="📶", font_size=sp(22), color=(0, 0, 0, 1)))
        inner.add_widget(icon_box)

        titles = BoxLayout(orientation="vertical", spacing=dp(2))
        titles.add_widget(Label(
            text="WiFi Tester Pro", font_size=sp(20), bold=True,
            color=get_color_from_hex(COLORS["text"]),
            halign="left", valign="bottom",
            size_hint_y=None, height=dp(28),
        ))
        titles.add_widget(Label(
            text="Professional Network Analyzer", font_size=sp(11),
            color=get_color_from_hex(COLORS["text_dim"]),
            halign="left", valign="top",
            size_hint_y=None, height=dp(20),
        ))
        inner.add_widget(titles)
        header.add_widget(inner)
        return header

    # ---------- بطاقة الاتصال ----------
    def _build_connection_card(self):
        card = Card(
            bg_color=COLORS["surface"],
            size_hint_y=None, height=dp(150),
            padding=[dp(16), dp(14)], spacing=dp(6),
            orientation="vertical",
        )
        header_row = BoxLayout(size_hint_y=None, height=dp(20))
        header_row.add_widget(Label(
            text="CURRENT CONNECTION", font_size=sp(11), bold=True,
            color=get_color_from_hex(COLORS["primary"]),
            halign="left", valign="middle",
        ))
        card.add_widget(header_row)

        self.conn_label = Label(
            text="[color=#8A929C]Fetching...[/color]",
            markup=True, font_size=sp(12),
            halign="left", valign="top",
            size_hint_y=None,
            text_size=(Window.width - dp(64), None),
        )
        self.conn_label.bind(
            width=lambda *a: setattr(
                self.conn_label, "text_size",
                (self.conn_label.width, None)
            )
        )
        card.add_widget(self.conn_label)
        return card

    # ---------- الإحصائيات ----------
    def _build_stats_card(self):
        card = Card(
            bg_color=COLORS["surface"],
            size_hint_y=None, height=dp(90),
            padding=[dp(16), dp(14)], spacing=dp(8),
            orientation="vertical",
        )
        card.add_widget(Label(
            text="STATISTICS", font_size=sp(11), bold=True,
            color=get_color_from_hex(COLORS["primary"]),
            halign="left", valign="middle",
            size_hint_y=None, height=dp(18),
        ))
        stats_row = BoxLayout(spacing=dp(8), size_hint_y=None, height=dp(50))

        self.stat_total = self._make_stat_box("0", "TOTAL", COLORS["accent"])
        stats_row.add_widget(self.stat_total)
        self.stat_secured = self._make_stat_box("0", "SECURED", COLORS["sec_wpa2"])
        stats_row.add_widget(self.stat_secured)
        self.stat_open = self._make_stat_box("0", "OPEN", COLORS["danger"])
        stats_row.add_widget(self.stat_open)
        self.stat_best = self._make_stat_box("—", "BEST", COLORS["success"])
        stats_row.add_widget(self.stat_best)

        card.add_widget(stats_row)
        return card

    def _make_stat_box(self, value, label, color):
        box = Card(
            bg_color=COLORS["surface2"], radius=10,
            orientation="vertical",
            padding=[dp(6), dp(6)], spacing=dp(2),
        )
        val_lbl = Label(
            text=f"[color={color}][b]{value}[/b][/color]",
            markup=True, font_size=sp(16),
            size_hint_y=None, height=dp(22),
        )
        box.add_widget(val_lbl)
        box.add_widget(Label(
            text=f"[color={COLORS['text_dim']}][size=9]{label}[/size][/color]",
            markup=True, font_size=sp(9),
            size_hint_y=None, height=dp(14),
        ))
        box.value_label = val_lbl
        return box

    # ---------- بطاقة الشبكات ----------
    def _build_networks_card(self):
        card = Card(
            bg_color=COLORS["surface"],
            size_hint_y=None, height=dp(520),
            padding=[dp(16), dp(14)], spacing=dp(10),
            orientation="vertical",
        )
        header = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(6))
        header.add_widget(Label(
            text="AVAILABLE NETWORKS", font_size=sp(11), bold=True,
            color=get_color_from_hex(COLORS["primary"]),
            halign="left", valign="middle",
        ))
        self.auto_btn = Button(
            text="🔄 Auto: OFF", size_hint=(None, 1), width=dp(110),
            background_normal="", background_color=(0, 0, 0, 0),
            color=get_color_from_hex(COLORS["text_dim"]),
            bold=True, font_size=sp(12),
        )
        self.auto_btn.bind(on_press=self.toggle_auto_scan)
        header.add_widget(self.auto_btn)

        scan_btn = Button(
            text="📡 Scan", size_hint=(None, 1), width=dp(80),
            background_normal="", background_color=(0, 0, 0, 0),
            color=get_color_from_hex(COLORS["accent"]),
            bold=True, font_size=sp(12),
        )
        scan_btn.bind(on_press=self.scan_networks)
        header.add_widget(scan_btn)
        card.add_widget(header)

        self.networks_scroll = ScrollView(do_scroll_x=False)
        self.networks_box = BoxLayout(
            orientation="vertical", spacing=dp(8),
            size_hint_y=None,
        )
        self.networks_box.bind(minimum_height=self.networks_box.setter("height"))
        self.networks_scroll.add_widget(self.networks_box)
        card.add_widget(self.networks_scroll)

        self.networks_placeholder = Label(
            text="[color=#8A929C]Tap 📡 Scan to discover networks[/color]",
            markup=True, font_size=sp(13),
        )
        self.networks_box.add_widget(self.networks_placeholder)
        return card

    # ---------- بطاقة الإدخال ----------
    def _build_input_card(self):
        card = Card(
            bg_color=COLORS["surface"],
            size_hint_y=None, height=dp(120),
            padding=[dp(16), dp(14)], spacing=dp(8),
            orientation="vertical",
        )
        card.add_widget(Label(
            text="SELECTED NETWORK", font_size=sp(11), bold=True,
            color=get_color_from_hex(COLORS["primary"]),
            halign="left", valign="middle",
            size_hint_y=None, height=dp(18),
        ))
        self.ssid_input = TextInput(
            hint_text="Tap a network above, or type SSID",
            multiline=False,
            size_hint_y=None, height=dp(52),
            font_size=sp(15),
            background_color=get_color_from_hex(COLORS["surface2"]),
            foreground_color=get_color_from_hex(COLORS["text"]),
            hint_text_color=get_color_from_hex(COLORS["text_dim"]),
            cursor_color=get_color_from_hex(COLORS["primary"]),
            padding=[dp(14), dp(14)],
        )
        card.add_widget(self.ssid_input)
        return card

    # ---------- بطاقة ملفات الباسوردات ----------
    def _build_files_card(self):
        card = Card(
            bg_color=COLORS["surface"],
            size_hint_y=None, height=dp(280),
            padding=[dp(16), dp(14)], spacing=dp(10),
            orientation="vertical",
        )
        card.add_widget(Label(
            text="PASSWORD FILES", font_size=sp(11), bold=True,
            color=get_color_from_hex(COLORS["primary"]),
            halign="left", valign="middle",
            size_hint_y=None, height=dp(18),
        ))

        files_scroll = ScrollView(do_scroll_x=False)
        self.files_box = BoxLayout(
            orientation="vertical", spacing=dp(6),
            size_hint_y=None,
        )
        self.files_box.bind(minimum_height=self.files_box.setter("height"))
        files_scroll.add_widget(self.files_box)
        card.add_widget(files_scroll)

        buttons_row = BoxLayout(
            spacing=dp(8), size_hint_y=None, height=dp(42)
        )
        add_btn = SecondaryButton(text="➕ New")
        add_btn.bind(on_press=self.show_add_file_dialog)
        buttons_row.add_widget(add_btn)

        import_btn = SecondaryButton(text="📂 Import")
        import_btn.bind(on_press=self.import_file)
        buttons_row.add_widget(import_btn)

        delete_btn = SecondaryButton(text="🗑  Delete")
        delete_btn.bind(on_press=self.delete_current_file)
        buttons_row.add_widget(delete_btn)

        card.add_widget(buttons_row)

        self.refresh_files()
        return card

    # ---------- بطاقة التحكم ----------
    def _build_control_card(self):
        card = Card(
            bg_color=COLORS["surface"],
            size_hint_y=None, height=dp(150),
            padding=[dp(16), dp(14)], spacing=dp(10),
            orientation="vertical",
        )
        card.add_widget(Label(
            text="CONTROL", font_size=sp(11), bold=True,
            color=get_color_from_hex(COLORS["primary"]),
            halign="left", valign="middle",
            size_hint_y=None, height=dp(18),
        ))
        self.start_btn = PrimaryButton(
            text="▶  START TESTING", size_hint_y=None, height=dp(52)
        )
        self.start_btn.bind(on_press=self.toggle)
        card.add_widget(self.start_btn)

        row = BoxLayout(spacing=dp(8), size_hint_y=None, height=dp(42))
        settings_btn = SecondaryButton(text="📲 Settings")
        settings_btn.bind(on_press=lambda x: open_wifi_settings())
        row.add_widget(settings_btn)

        export_btn = SecondaryButton(text="💾 Export")
        export_btn.bind(on_press=self.export_log)
        row.add_widget(export_btn)

        clear_btn = SecondaryButton(text="🗑  Clear")
        clear_btn.bind(on_press=self.clear_log)
        row.add_widget(clear_btn)

        card.add_widget(row)
        return card

    # ---------- التقدم ----------
    def _build_progress_card(self):
        card = Card(
            bg_color=COLORS["surface"],
            size_hint_y=None, height=dp(90),
            padding=[dp(16), dp(14)], spacing=dp(8),
            orientation="vertical",
        )
        self.progress_label = Label(
            text="Ready", font_size=sp(14),
            color=get_color_from_hex(COLORS["text"]),
            halign="left", valign="middle",
            size_hint_y=None, height=dp(20),
        )
        card.add_widget(self.progress_label)

        self.progress = ProgressBar(
            max=100, value=0, size_hint_y=None, height=dp(10)
        )
        card.add_widget(self.progress)

        self.percent_label = Label(
            text="0%", font_size=sp(12),
            color=get_color_from_hex(COLORS["text_dim"]),
            halign="right", valign="middle",
            size_hint_y=None, height=dp(18),
        )
        card.add_widget(self.percent_label)
        return card

    # ---------- السجل ----------
    def _build_log_card(self):
        card = Card(
            bg_color=COLORS["surface"],
            size_hint_y=None, height=dp(340),
            padding=[dp(16), dp(14)], spacing=dp(8),
            orientation="vertical",
        )
        card.add_widget(Label(
            text="LIVE LOG", font_size=sp(11), bold=True,
            color=get_color_from_hex(COLORS["primary"]),
            halign="left", valign="middle",
            size_hint_y=None, height=dp(18),
        ))
        log_bg = Card(
            bg_color="#0A0D11", radius=12,
            padding=[dp(10), dp(8)],
        )
        log_scroll = ScrollView(do_scroll_x=False)
        self.log_label = Label(
            text="", font_size=sp(12),
            color=get_color_from_hex(COLORS["text"]),
            halign="left", valign="top",
            size_hint_y=None, markup=True,
        )
        self.log_label.bind(
            width=lambda *a: setattr(
                self.log_label, "text_size",
                (self.log_label.width, None)
            )
        )
        self.log_label.bind(texture_size=self.log_label.setter("size"))
        log_scroll.add_widget(self.log_label)
        log_bg.add_widget(log_scroll)
        card.add_widget(log_bg)

        self.append_log("🚀 WiFi Tester Pro started", "primary")
        self.append_log(f"📋 {len(self.passwords)} passwords loaded", "text")
        self.append_log("", "text")
        return card

    # ======================================================
    #  المنطق
    # ======================================================

    def append_log(self, message, style="text"):
        colors = {
            "primary": COLORS["primary"], "danger": COLORS["danger"],
            "warning": COLORS["warning"], "text": COLORS["text"],
            "dim": COLORS["text_dim"], "accent": COLORS["accent"],
            "success": COLORS["success"],
        }
        color = colors.get(style, COLORS["text"])
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_label.text += (
            f"[color={COLORS['text_dim']}]{ts}[/color]  "
            f"[color={color}]{message}[/color]\n"
        )

    # ---------- الشبكات ----------
    def scan_networks(self, instance):
        self.append_log("📡 Scanning networks...", "accent")
        threading.Thread(target=self._do_scan, daemon=True).start()

    def _do_scan(self):
        networks = scan_wifi_networks()
        Clock.schedule_once(lambda dt: self._update_networks(networks), 0)

    @mainthread
    def _update_networks(self, networks):
        self.networks = networks
        self.networks_box.clear_widgets()

        total = len(networks)
        secured = sum(1 for n in networks if n["security"] != "OPEN")
        open_n = total - secured
        best = max((n["level"] for n in networks), default=None)

        self.stat_total.value_label.text = (
            f"[color={COLORS['accent']}][b]{total}[/b][/color]"
        )
        self.stat_secured.value_label.text = (
            f"[color={COLORS['sec_wpa2']}][b]{secured}[/b][/color]"
        )
        self.stat_open.value_label.text = (
            f"[color={COLORS['danger']}][b]{open_n}[/b][/color]"
        )
        if best:
            self.stat_best.value_label.text = (
                f"[color={COLORS['success']}][b]{best}[/b][/color]"
            )

        if not networks:
            self.networks_box.add_widget(Label(
                text="[color=#8A929C]No networks found.\n\n"
                     "Make sure:\n"
                     "• Location permission granted\n"
                     "• GPS is enabled\n"
                     "• Wi-Fi is ON[/color]",
                markup=True, font_size=sp(12),
                halign="center",
                size_hint_y=None, height=dp(150),
            ))
            self.append_log("⚠  No networks found", "warning")
            return

        for net in networks:
            self.networks_box.add_widget(
                NetworkRow(net, on_select=self._select_network)
            )
        self.append_log(
            f"✅ Found {total} networks ({secured} 🔒 / {open_n} 🔓)",
            "success"
        )

    def _select_network(self, network):
        self.ssid_input.text = network["ssid"]
        self.append_log(
            f"📡 Selected: [b]{network['ssid']}[/b] "
            f"({network['security']}, {network['percent']}%)",
            "accent"
        )

    # ---------- معلومات الاتصال ----------
    def update_connection_info(self, instance):
        threading.Thread(target=self._do_fetch_conn, daemon=True).start()

    def _do_fetch_conn(self):
        info = get_connection_info()
        Clock.schedule_once(lambda dt: self._render_conn(info), 0)

    @mainthread
    def _render_conn(self, info):
        if not info.get("connected"):
            self.conn_label.text = (
                f"[color={COLORS['danger']}]❌ Not connected[/color]\n"
                f"[color={COLORS['text_dim']}]No active Wi-Fi connection[/color]"
            )
            return
        ssid = info["ssid"]
        ip = info["ip"]
        bssid = info["bssid"]
        speed = info["link_speed"]
        rssi = info["rssi"]
        freq = info["frequency"]
        band, _ = freq_to_band(freq)
        pct = signal_to_percent(rssi)

        self.conn_label.text = (
            f"[color={COLORS['success']}][b]✓ Connected[/b][/color]\n"
            f"[color={COLORS['text']}]📶 [b]{ssid}[/b][/color]\n"
            f"[color={COLORS['text_dim']}]"
            f"🌐 IP: {ip}\n"
            f"📡 Signal: {rssi} dBm ({pct}%)\n"
            f"⚡ Speed: {speed} Mbps  •  {band}\n"
            f"🔗 MAC: {bssid}[/color]"
        )

    # ---------- Auto-Scan ----------
    def toggle_auto_scan(self, instance):
        if self.auto_scan_event:
            self.auto_scan_event.cancel()
            self.auto_scan_event = None
            self.auto_btn.text = "🔄 Auto: OFF"
            self.auto_btn.color = get_color_from_hex(COLORS["text_dim"])
            self.append_log("⏸  Auto-scan disabled", "dim")
        else:
            self.auto_scan_event = Clock.schedule_interval(
                self.scan_networks, 30
            )
            self.auto_btn.text = "🔄 Auto: ON"
            self.auto_btn.color = get_color_from_hex(COLORS["success"])
            self.append_log("▶  Auto-scan enabled (30s)", "success")

    # ---------- ملفات الباسوردات ----------
    def refresh_files(self):
        self.files_box.clear_widgets()
        files = list_password_files()
        for f in files:
            selected = (f["name"] == self.selected_file)
            self.files_box.add_widget(
                FileRow(f, selected, on_select=self.select_file)
            )

    def select_file(self, file_info):
        self.selected_file = file_info["name"]
        if file_info["builtin"]:
            self.passwords = list(DEFAULT_PASSWORDS)
        else:
            pwds = read_file_passwords(file_info["path"])
            self.passwords = pwds if pwds else []

        self.append_log(
            f"📁 Selected: [b]{file_info['name']}[/b] "
            f"({len(self.passwords)} passwords)",
            "accent"
        )
        self.refresh_files()

    def show_add_file_dialog(self, instance):
        content = BoxLayout(
            orientation="vertical", spacing=dp(10),
            padding=dp(16),
        )
        content.add_widget(Label(
            text="Create new password file",
            font_size=sp(14), bold=True,
            color=get_color_from_hex(COLORS["text"]),
            size_hint_y=None, height=dp(30),
        ))
        name_input = TextInput(
            hint_text="File name (e.g. my_wifi.txt)",
            multiline=False,
            size_hint_y=None, height=dp(45),
            background_color=get_color_from_hex(COLORS["surface2"]),
            foreground_color=get_color_from_hex(COLORS["text"]),
            cursor_color=get_color_from_hex(COLORS["primary"]),
            padding=[dp(12), dp(12)],
        )
        content.add_widget(name_input)

        content.add_widget(Label(
            text="Passwords (one per line)",
            font_size=sp(12),
            color=get_color_from_hex(COLORS["text_dim"]),
            size_hint_y=None, height=dp(22),
        ))

        pwds_input = TextInput(
            hint_text="password1\npassword2\npassword3",
            multiline=True,
            background_color=get_color_from_hex(COLORS["surface2"]),
            foreground_color=get_color_from_hex(COLORS["text"]),
            cursor_color=get_color_from_hex(COLORS["primary"]),
            padding=[dp(12), dp(12)],
        )
        content.add_widget(pwds_input)

        buttons = BoxLayout(
            spacing=dp(8), size_hint_y=None, height=dp(45)
        )
        popup = Popup(
            title="", content=content,
            size_hint=(0.9, 0.7),
            background_color=get_color_from_hex(COLORS["surface"]),
            separator_color=get_color_from_hex(COLORS["primary"]),
        )

        def on_save(*args):
            name = name_input.text.strip()
            txt = pwds_input.text.strip()
            if not name or not txt:
                self.append_log("⚠  Name and passwords required", "danger")
                return
            path = save_password_file(name, txt)
            if path:
                self.append_log(f"✅ Created: {name}", "success")
                popup.dismiss()
                self.refresh_files()
            else:
                self.append_log("❌ Failed to create file", "danger")

        save_btn = PrimaryButton(text="Save")
        save_btn.bind(on_press=on_save)
        buttons.add_widget(save_btn)

        cancel_btn = SecondaryButton(text="Cancel")
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        buttons.add_widget(cancel_btn)

        content.add_widget(buttons)
        popup.open()

    def import_file(self, instance):
        try:
            from plyer import filechooser
            filechooser.open_file(
                on_selection=self._on_file_selected,
                filters=[("Text files", "*.txt")],
            )
        except Exception as e:
            self.append_log("⚠  File chooser not available", "warning")
            self.append_log(f"   {e}", "dim")

    def _on_file_selected(self, selection):
        if not selection:
            return
        dst = import_passwords_from_path(selection[0])
        if dst:
            self.append_log(
                f"✅ Imported: {os.path.basename(dst)}", "success"
            )
            self.refresh_files()
        else:
            self.append_log("❌ Import failed", "danger")

    def delete_current_file(self, instance):
        if not self.selected_file or self.selected_file == "default":
            self.append_log("⚠  Cannot delete default file", "warning")
            return
        files = list_password_files()
        target = next(
            (f for f in files if f["name"] == self.selected_file), None
        )
        if not target or target["builtin"]:
            return
        if delete_password_file(target["path"]):
            self.append_log(f"🗑  Deleted: {target['name']}", "warning")
            self.selected_file = "default"
            self.passwords = list(DEFAULT_PASSWORDS)
            self.refresh_files()
        else:
            self.append_log("❌ Delete failed", "danger")

    # ---------- الاختبار ----------
    def toggle(self, instance):
        if self.running:
            self.running = False
            self.start_btn.text = "▶  START TESTING"
            self.start_btn.set_color(COLORS["primary"])
            self.append_log("⏸  Stopped", "warning")
            return

        ssid = self.ssid_input.text.strip()
        if not ssid:
            self.append_log("⚠  Select or type a network first", "danger")
            return

        self.running = True
        self.index = 0
        self.start_btn.text = "⏸  STOP"
        self.start_btn.set_color(COLORS["danger"])
        self.progress.value = 0
        self.progress_label.text = f"Testing {ssid}..."
        self.percent_label.text = "0%"

        self.append_log(f"📶 Target: [b]{ssid}[/b]", "primary")
        self.append_log("📡 Sending suggestions...", "accent")

        clear_suggestions()
        Clock.schedule_interval(lambda dt: self.send_next(ssid), 0.6)

    def send_next(self, ssid):
        if not self.running:
            return False
        if self.index >= len(self.passwords):
            self.append_log("")
            self.append_log("✅ All suggestions sent", "success")
            self.append_log("👉 Check Wi-Fi settings", "accent")
            self.progress_label.text = "Completed ✓"
            self.progress.value = 100
            self.percent_label.text = "100%"
            self.running = False
            self.start_btn.text = "▶  START TESTING"
            self.start_btn.set_color(COLORS["primary"])
            return False

        pwd = self.passwords[self.index]
        self.index += 1
        ok = suggest_wifi(ssid, pwd)

        style = "success" if ok else "warning"
        icon = "✓" if ok else "⚠"
        self.append_log(
            f"[{self.index:02d}/{len(self.passwords)}] {icon}  {pwd}",
            style
        )

        percent = int((self.index / len(self.passwords)) * 100)
        self.progress.value = percent
        self.percent_label.text = f"{percent}%"
        self.progress_label.text = (
            f"Testing... {self.index}/{len(self.passwords)}"
        )
        return True

    # ---------- السجل ----------
    def clear_log(self, instance):
        self.log_label.text = ""
        self.append_log("🗑  Log cleared", "dim")
        self.append_log("", "text")

    def export_log(self, instance):
        try:
            if ANDROID:
                try:
                    from android.storage import primary_external_storage_path
                    path = os.path.join(
                        primary_external_storage_path(),
                        "Download",
                        f"wifi_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    )
                except Exception:
                    path = "wifi_log.txt"
            else:
                path = "wifi_log.txt"

            clean = re.sub(r"\[.*?\]", "", self.log_label.text)
            with open(path, "w", encoding="utf-8") as f:
                f.write(clean)
            self.append_log(
                f"💾 Saved: {os.path.basename(path)}", "success"
            )
        except Exception as e:
            self.append_log(f"❌ Export failed: {e}", "danger")


if __name__ == "__main__":
    WiFiTesterApp().run()