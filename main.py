#!/usr/bin/env python3
# AMIR6 - Simorgh MSP Architecture & Hybrid Scanner

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

# ====================== رنج‌های آی‌پی MSP (آروان و کلادفلر) ======================
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
    """استخراج هوشمند آدرس، پورت و SNI از کانفیگ پورت 443"""
    sni = "cloudflare.com"
    address = "194.5.192.92"
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

def test_real_delay(ip, sni_domain, delay_url, timeout=4.0):
    """تست واقعی تاخیر از طریق هندشیک امن پورت 443 و بستر MSP"""
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
            # ارسال درخواست تست سلامت مشابه مکانیزم سورس
            tls.sendall(
                f"GET / HTTP/1.1\r\n"
                f"Host: {target_sni}\r\n"
                f"Connection: close\r\n\r\n".encode()
            )
            tls.recv(32)
            
        return round((time.monotonic() - t0) * 1000, 1)
    except Exception:
        return None

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

        self.lbl_ip = Label(text=ip, size_hint_x=0.48, color=get_color_from_hex("#00ccff"), font_size="11sp", halign="left")
        self.lbl_ip.bind(size=self.lbl_ip.setter('text_size'))
        self.add_widget(self.lbl_ip)

        self.lbl_ping = Label(text=f"{ms:.0f} ms", size_hint_x=0.22, color=get_color_from_hex("#00ff88"), font_size="11sp", bold=True)
        self.add_widget(self.lbl_ping)

        # دکمه اتصال اختصاصی برای هر آی‌پی (MSP Connect)
        btn_connect = Button(text="CONNECT", size_hint_x=0.22, background_color=get_color_from_hex("#005500"),
                             color=get_color_from_hex("#00ff88"), font_size="10sp", bold=True)
        btn_connect.bind(on_press=lambda x: self.app_instance.connect_with_ip(self.ip))
        self.add_widget(btn_connect)

class Amir6App(App):
    def build(self):
        self.title = "AMIR6 - Simorgh MSP Engine"
        self.running = False
        self.results = []
        self.tested = 0
        self.found = 0
        self.total = 300
        self.lock = threading.Lock()
        self.q = None
        self.row_widgets = []

        root = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(6))

        header = Label(text="[b][color=00ccff]AMIR6[/color] MSP Core Engine[/b]", markup=True,
                       size_hint_y=None, height=dp(28), font_size="15sp")
        root.add_widget(header)

        # ۱. بخش MSP Configuration (انتخاب ISP)
        isp_box = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(6))
        isp_box.add_widget(Label(text="ISP:", size_hint_x=0.15, color=get_color_from_hex("#aaaaaa"), font_size="12sp"))
        self.spin_isp = Spinner(text="AbrArvan CDN and IaaS (Arvan)", values=list(ISP_DICT.keys()), size_hint_x=0.85,
                                background_color=get_color_from_hex("#1a1a2e"), color=(1,1,1,1), font_size="12sp")
        isp_box.add_widget(self.spin_isp)
        root.add_widget(isp_box)

        # ۲. بخش Real Delay URL
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

        # ۳. بخش CF Config (جایگذاری کانفیگ پورت 443)
        config_layout = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(52), spacing=dp(2))
        config_layout.add_widget(Label(text="Paste CF Config (Port 443):", size_hint_y=None, height=dp(14), color=get_color_from_hex("#00ccff"), font_size="10sp"))
        self.txt_config = TextInput(text="vless://uuid@194.5.192.92:443?type=ws&security=tls&sni=long-morning-7443.amirsanaei1313.workers.dev#OMID",
                                    multiline=False, size_hint_y=None, height=dp(36), font_size="10sp",
                                    background_color=get_color_from_hex("#1a1a2e"), foreground_color=(1,1,1,1))
        config_layout.add_widget(self.txt_config)
        root.add_widget(config_layout)

        # دکمه‌های کنترل
        btn_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        self.btn_start = Button(text="START MSP SCAN", background_color=get_color_from_hex("#005500"), color=get_color_from_hex("#00ff88"), bold=True, font_size="13sp")
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

        self.lbl_status = Label(text="MSP Engine Ready...", color=get_color_from_hex("#888888"), size_hint_y=None, height=dp(22), font_size="12sp")
        root.add_widget(self.lbl_status)

        # لیست نتایج
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
        self.lbl_status.text = f"Stopped — {self.found} working IPs found"
        self.lbl_status.color = get_color_from_hex("#ffcc00")

    def scan_worker(self):
        selected_isp = self.spin_isp.text
        ranges = ISP_DICT.get(selected_isp, ARVAN_IPV4)
        
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
                ms = test_real_delay(ip, sni_domain, delay_url)
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

        # کاهش تعداد تردها برای پایداری بیشتر سوکت‌ها در اندروید
        ts = [threading.Thread(target=worker, daemon=True) for _ in range(30)]
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
                row.opacity = 1
                row.height = dp(46)
            else:
                row.opacity = 0
                row.height = 0

        self.progress.value = min(pct, 100)
        self.lbl_status.text = f"MSP Scanning... {tested}/{self.total}  |  Found: {found}"

    def scan_done(self, *args):
        self.running = False
        self.btn_start.disabled = False
        self.btn_stop.disabled = True
        self.lbl_status.text = f"Scan Complete — {self.found} working IPs ready!"
        self.lbl_status.color = get_color_from_hex("#00ff88")
        self.progress.value = 100

    def connect_with_ip(self, clean_ip):
        """اعمال آی‌پی تمیز اسکن‌شده بر روی کانفیگ به سبک موتور MSP"""
        raw_config = self.txt_config.text.strip()
        address, port, _ = parse_vless_config(raw_config)
        
        # جایگزینی آی‌پی جدید در کانفیگ اصلی جهت استفاده در v2rayNG
        new_config = raw_config.replace(f"{address}:{port}", f"{clean_ip}:{port}")
        Clipboard.copy(new_config)
        
        self.show_popup("MSP Connected!", f"Clean IP mapped successfully:\n{clean_ip}\n\n(Config copied to clipboard!)")

    def save_results(self, *args):
        if not self.results:
            self.show_popup("Error", "No IPs found to copy!")
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
