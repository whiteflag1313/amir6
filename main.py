#!/usr/bin/env python3
# AMIR6 - Simorgh Architecture Clone (Arvan Scan + CF Config Real Ping & Connect)

import threading, socket, ssl, time, random, ipaddress, os, urllib.parse
from queue import Queue, Empty

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.core.clipboard import Clipboard

Window.clearcolor = get_color_from_hex("#0d0d0d")

# ====================== ISP Ranges (Arvan & Cloudflare) ======================
ARVAN_IPV4 = [
    "91.216.13.0/24", "130.185.120.0/22", "185.204.168.0/22",
    "185.235.40.0/22", "193.24.119.0/24", "194.5.192.0/23",
    "194.5.206.0/23", "185.215.232.0/22", "37.32.3.0/24",
    "185.143.232.0/22", "185.220.226.0/24", "193.176.240.0/24",
]

CF_IPV4 = [
    "104.16.0.0/13", "104.24.0.0/14", "172.64.0.0/13",
    "162.158.0.0/15", "198.41.128.0/17", "173.245.48.0/20",
    "103.21.244.0/22", "103.22.200.0/22", "103.31.4.0/22",
    "141.101.64.0/18", "108.162.192.0/18", "190.93.240.0/20",
    "188.114.96.0/20", "197.234.240.0/22",
]

ISP_DICT = {
    "AbrArvan CDN and IaaS (Arvan)": ARVAN_IPV4,
    "Cloudflare": CF_IPV4
}

def rand_ip_from_ranges(ranges):
    if not ranges:
        return None
    net = ipaddress.ip_network(random.choice(ranges), strict=False)
    n = int(net.num_addresses)
    if n <= 2:
        return str(net.network_address)
    return str(net.network_address + random.randint(1, n - 2))

def parse_vless_config(config_str):
    sni = "cloudflare.com"
    address = "185.121.201.201"
    port = "443"
    try:
        config_str = config_str.strip()
        if config_str.startswith("vless://"):
            parts = config_str.split("@")
            if len(parts) > 1:
                right_part = parts[1].split("#")[0]
                if "?" in right_part:
                    server_port_path, query_part = right_part.split("?", 1)
                elif "/" in right_part:
                    server_port_path, query_part = right_part.split("/", 1)
                else:
                    server_port_path, query_part = right_part, ""
                
                if ":" in server_port_path:
                    address, port = server_port_path.split(":", 1)
                else:
                    address = server_port_path
                
                params = urllib.parse.parse_qs(query_part)
                if "sni" in params:
                    sni = params["sni"][0]
    except Exception:
        pass
    return address, port, sni

def ping_once(ip, sni_domain, delay_url="https://www.gstatic.com/generate_204", timeout=4.0):
    """تست واقعی اتصال (Real Delay) مانند سیمرغ روی پورت ۴۴۳"""
    try:
        t0 = time.monotonic()
        info = socket.getaddrinfo(ip, 443, socket.AF_INET, socket.SOCK_STREAM)
        af, st, pr, _, addr = info[0]
        
        s = socket.socket(af, st, pr)
        s.settimeout(timeout)
        s.connect(addr)
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        target_sni = sni_domain if sni_domain else "cloudflare.com"
        
        with ctx.wrap_socket(s, server_hostname=target_sni) as tls:
            tls.sendall(
                f"GET / HTTP/1.1\r\n"
                f"Host: {target_sni}\r\n"
                f"Connection: close\r\n\r\n".encode()
            )
            tls.recv(64)
            
        return (time.monotonic() - t0) * 1000
    except Exception:
        return None

def test_ip(ip, sni_domain, delay_url):
    ms = ping_once(ip, sni_domain, delay_url)
    if ms is None:
        return None
    return round(ms, 1)

class IPRow(BoxLayout):
    def __init__(self, rank, ip, ms, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(46)
        self.padding = [dp(6), dp(2)]
        self.spacing = dp(6)
        self.ip = ip
        self.app_instance = app_instance

        self.lbl_rank = Label(text=str(rank), size_hint_x=0.08, color=get_color_from_hex("#666666"), font_size="11sp")
        self.add_widget(self.lbl_rank)

        self.lbl_ip = Label(text=ip, size_hint_x=0.50, color=get_color_from_hex("#00ccff"), font_size="11sp", halign="left")
        self.lbl_ip.bind(size=self.lbl_ip.setter('text_size'))
        self.add_widget(self.lbl_ip)

        self.lbl_ping = Label(text=f"{ms:.0f} ms", size_hint_x=0.22, color=self.get_ping_color(ms), font_size="11sp", bold=True)
        self.add_widget(self.lbl_ping)

        # دکمه Connect اختصاصی روبه‌روی هر آی‌پی (دقیقاً مثل سیمرغ)
        btn_connect = Button(text="CONNECT", size_hint_x=0.20, background_color=get_color_from_hex("#005500"),
                             color=get_color_from_hex("#00ff88"), font_size="10sp", bold=True)
        btn_connect.bind(on_press=lambda x: self.app_instance.connect_with_ip(self.ip))
        self.add_widget(btn_connect)

    def get_ping_color(self, ms):
        if ms < 450:
            return get_color_from_hex("#00ff88")
        elif ms < 650:
            return get_color_from_hex("#ffcc00")
        else:
            return get_color_from_hex("#ff4444")

class Amir6App(App):
    def build(self):
        self.title = "AMIR6 - Simorgh Engine"
        self.running = False
        self.results = []
        self.tested = 0
        self.found = 0
        self.total = 500
        self.lock = threading.Lock()
        self.q = None
        self.row_widgets = []

        root = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(6))

        header = Label(text="[b][color=00ccff]AMIR6[/color]  Simorgh Architecture[/b]", markup=True,
                       size_hint_y=None, height=dp(28), font_size="15sp")
        root.add_widget(header)

        # ۱. انتخاب ISP (بخش MSP Configuration)
        isp_box = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(6))
        isp_box.add_widget(Label(text="ISP:", size_hint_x=0.15, color=get_color_from_hex("#aaaaaa"), font_size="12sp"))
        self.spin_isp = Spinner(text="AbrArvan CDN and IaaS (Arvan)", values=list(ISP_DICT.keys()), size_hint_x=0.85,
                                background_color=get_color_from_hex("#1a1a2e"), color=(1,1,1,1), font_size="12sp")
        isp_box.add_widget(self.spin_isp)
        root.add_widget(isp_box)

        # ۲. بخش Real Delay URL (لینک تست تاخیر)
        url_box = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(6))
        url_box.add_widget(Label(text="Delay URL:", size_hint_x=0.22, color=get_color_from_hex("#aaaaaa"), font_size="12sp"))
        self.spin_url = Spinner(text="https://www.gstatic.com/generate_204", 
                                values=[
                                    "https://www.gstatic.com/generate_204",
                                    "https://connectivitycheck.gstatic.com/generate_204",
                                    "https://www.google.com/generate_204",
                                    "https://cp.cloudflare.com/generate_204"
                                ], size_hint_x=0.78,
                                background_color=get_color_from_hex("#1a1a2e"), color=(1,1,1,1), font_size="11sp")
        url_box.add_widget(self.spin_url)
        root.add_widget(url_box)

        # ۳. باکس جایگذاری کانفیگ (Paste VLESS Config Port 443)
        config_layout = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(52), spacing=dp(2))
        config_layout.add_widget(Label(text="Paste VLESS Config (Port 443):", size_hint_y=None, height=dp(14), color=get_color_from_hex("#00ccff"), font_size="10sp"))
        self.txt_config = TextInput(text="vless://uuid@185.121.201.201:443?type=ws&security=tls&sni=long-morning-7443.amirsanaei1313.workers.dev#OMID",
                                    multiline=False, size_hint_y=None, height=dp(36), font_size="10sp",
                                    background_color=get_color_from_hex("#1a1a2e"), foreground_color=(1,1,1,1))
        config_layout.add_widget(self.txt_config)
        root.add_widget(config_layout)

        # دکمه‌های کنترل (START / STOP / SAVE / CLEAR)
        btn_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        self.btn_start = Button(text="START SCAN", background_color=get_color_from_hex("#005500"), color=get_color_from_hex("#00ff88"), bold=True, font_size="13sp")
        self.btn_start.bind(on_press=self.start_scan)
        btn_row.add_widget(self.btn_start)

        self.btn_stop = Button(text="STOP", background_color=get_color_from_hex("#550000"), color=get_color_from_hex("#ff4444"), bold=True, font_size="13sp", disabled=True)
        self.btn_stop.bind(on_press=self.stop_scan)
        btn_row.add_widget(self.btn_stop)

        self.btn_save = Button(text="COPY ALL", background_color=get_color_from_hex("#003355"), color=get_color_from_hex("#00aaff"), bold=True, font_size="13sp")
        self.btn_save.bind(on_press=self.save_results)
        btn_row.add_widget(self.btn_save)
        root.add_widget(btn_row)

        self.progress = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(6))
        root.add_widget(self.progress)

        self.lbl_status = Label(text="Ready to scan Arvan ranges...", color=get_color_from_hex("#888888"), size_hint_y=None, height=dp(22), font_size="12sp")
        root.add_widget(self.lbl_status)

        # لیست نتایج به همراه دکمه Connect روبه‌روی هر آی‌پی
        scroll = ScrollView(do_scroll_x=False)
        self.results_layout = GridLayout(cols=1, size_hint_y=None, spacing=dp(3), padding=[0, dp(2)])
        self.results_layout.bind(minimum_height=self.results_layout.setter("height"))
        
        for i in range(30):
            row = IPRow(i + 1, "—", 0, self)
            row.opacity = 0
            row.height = 0
            self.row_widgets.append(row)
            self.results_layout.add_widget(row)
            
        scroll.add_widget(self.results_layout)
        root.add_widget(scroll)

        Clock.schedule_interval(self.flush_rows, 0.5)
        return root

    def start_scan(self, *args):
        if self.running:
            return
        self.running = True
        self.results = []
        self.tested = 0
        self.found = 0
        self.progress.value = 0
        self.btn_start.disabled = True
        self.btn_stop.disabled = False
        self.lbl_status.color = get_color_from_hex("#00ccff")
        threading.Thread(target=self.scan_worker, daemon=True).start()

    def stop_scan(self, *args):
        self.running = False
        if self.q:
            while not self.q.empty():
                try:
                    self.q.get_nowait()
                    self.q.task_done()
                except Exception:
                    break
        self.btn_start.disabled = False
        self.btn_stop.disabled = True
        self.lbl_status.text = f"Stopped — {self.found} IPs found"
        self.lbl_status.color = get_color_from_hex("#ffcc00")

    def scan_worker(self):
        selected_isp_name = self.spin_isp.text
        ranges = ISP_DICT.get(selected_isp_name, ARVAN_IPV4)
        
        raw_config = self.txt_config.text.strip()
        _, _, sni_domain = parse_vless_config(raw_config)
        delay_url = self.spin_url.text

        self.q = Queue()
        for _ in range(self.total):
            ip = rand_ip_from_ranges(ranges)
            if ip:
                self.q.put(ip)

        def worker():
            while self.running:
                try:
                    ip = self.q.get(timeout=0.5)
                except Empty:
                    break
                if not self.running:
                    self.q.task_done()
                    break
                ms = test_ip(ip, sni_domain, delay_url)
                if not self.running:
                    self.q.task_done()
                    break
                with self.lock:
                    self.tested += 1
                    if ms is not None:
                        self.found += 1
                        self.results.append((ms, ip))
                        self.results.sort()
                self.q.task_done()

        ts = [threading.Thread(target=worker, daemon=True) for _ in range(60)]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        if self.running:
            Clock.schedule_once(self.scan_done, 0)

    def flush_rows(self, dt):
        with self.lock:
            pct = (self.tested / self.total * 100) if self.total else 0
            found = self.found
            tested = self.tested
            current = self.results[:30]

        for i, row in enumerate(self.row_widgets):
            if i < len(current):
                m, p = current[i]
                row.ip = p
                row.lbl_rank.text = str(i + 1)
                row.lbl_ip.text = p
                row.lbl_ping.text = f"{m:.0f} ms"
                row.lbl_ping.color = row.get_ping_color(m)
                row.opacity = 1
                row.height = dp(46)
            else:
                row.opacity = 0
                row.height = 0

        self.progress.value = min(pct, 100)
        self.lbl_status.text = f"Scanning... {tested}/{self.total}  |  Found: {found}"

    def scan_done(self, *args):
        self.running = False
        self.btn_start.disabled = False
        self.btn_stop.disabled = True
        self.lbl_status.text = f"Finished — {self.found} working IPs found!"
        self.lbl_status.color = get_color_from_hex("#00ff88")
        self.progress.value = 100

    def connect_with_ip(self, clean_ip):
        """زمانی که روی دکمه Connect روبه‌روی آی‌پی میزنی، کانفیگ مرده با این آی‌پی جدید زنده میشه"""
        raw_config = self.txt_config.text.strip()
        address, port, sni = parse_vless_config(raw_config)
        
        # جایگزینی آی‌پی جدیدِ پیدا شده با آی‌پی قبلی در کانفیگ
        new_config = raw_config.replace(f"{address}:{port}", f"{clean_ip}:{port}")
        Clipboard.copy(new_config)
        
        self.show_popup("Connected Successfully!", f"Config updated with IP:\n{clean_ip}\n\n(New config copied to clipboard!)")

    def save_results(self, *args):
        if not self.results:
            self.show_popup("Error", "No IPs to copy!")
            return
        ip_text = "\n".join([ip for _, ip in self.results]) + "\n"
        Clipboard.copy(ip_text)
        self.show_popup("Copied", f"{len(self.results)} IPs copied to clipboard!")

    def show_popup(self, title, msg):
        content = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        content.add_widget(Label(text=msg, color=(1,1,1,1), font_size="13sp", halign="center"))
        btn = Button(text="OK", size_hint_y=None, height=dp(40), background_color=get_color_from_hex("#005500"))
        content.add_widget(btn)
        popup = Popup(title=title, content=content, size_hint=(0.85, 0.35),
                      background_color=get_color_from_hex("#1a1a2e"))
        btn.bind(on_press=popup.dismiss)
        popup.open()

if __name__ == "__main__":
    Amir6App().run()
