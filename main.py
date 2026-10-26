#!/usr/bin/env python3
# AMIR6 - CF & Arvan Hybrid IPv Scanner (Fixed Architecture)

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

# ====================== ISP Ranges ======================
CF_IPV6 = [
    "2606:4700:3030::/48","2606:4700:3031::/48",
    "2606:4700:3032::/48","2606:4700:3033::/48",
    "2606:4700:3034::/48","2606:4700:3035::/48",
    "2606:4700:3036::/48","2606:4700:3037::/48",
    "2606:4700:3038::/48","2606:4700:f1::/48",
    "2606:4700:f2::/48","2606:4700:10::/48",
    "2606:4700:20::/48","2606:4700:80::/48",
    "2606:4700:90::/48","2606:4700:110::/48",
    "2606:4700:130::/48","2606:4700:150::/48",
    "2606:4700:300::/48","2606:4700:4700::/48",
]

CF_IPV4 = [
    "104.16.0.0/13", "104.24.0.0/14", "172.64.0.0/13",
    "162.158.0.0/15", "198.41.128.0/17", "173.245.48.0/20",
    "103.21.244.0/22", "103.22.200.0/22", "103.31.4.0/22",
    "141.101.64.0/18", "108.162.192.0/18", "190.93.240.0/20",
    "188.114.96.0/20", "197.234.240.0/22",
]

ARVAN_IPV4 = [
    "91.216.13.0/24", "130.185.120.0/22", "185.204.168.0/22",
    "185.235.40.0/22", "193.24.119.0/24", "194.5.192.0/23",
    "194.5.206.0/23", "185.215.232.0/22", "37.32.3.0/24",
    "185.143.232.0/22", "185.220.226.0/24", "193.176.240.0/24",
]

ISP_LIST = [
    "Cloudflare",
    "ArvanCloud Global TR",
    "AbrArvan CDN and IaaS",
    "ARVANCLOUD GLOBAL TECHNOLOGIES L.L.C",
    "Mobin Arvand Infrastructure Company LTD",
    "Noyan Abr Arvan Co. (Private Joint Stock)",
    "ArvanCloud CDN (IR)",
    "ArvanCloud Global (AE)",
    "AbrArvan IaaS",
]

def get_ranges(isp_name, protocol):
    ranges = []
    if isp_name == "Cloudflare":
        if protocol in ("IPv6", "Both"):
            ranges.extend(CF_IPV6)
        if protocol in ("IPv4", "Both"):
            ranges.extend(CF_IPV4)
    else:
        if protocol in ("IPv4", "Both"):
            ranges.extend(ARVAN_IPV4)
    return ranges

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
    try:
        config_str = config_str.strip()
        if config_str.startswith("vless://"):
            parts = config_str.split("@")
            if len(parts) > 1:
                host_part = parts[1].split("#")[0]
                if "?" in host_part:
                    _, query_part = host_part.split("?", 1)
                elif "/" in host_part:
                    _, query_part = host_part.split("/", 1)
                else:
                    query_part = ""
                
                params = urllib.parse.parse_qs(query_part)
                if "sni" in params:
                    sni = params["sni"][0]
    except Exception:
        pass
    return sni

def ping_once(ip, sni_domain, timeout=5.0):
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        t0 = time.monotonic()
        family = socket.AF_INET6 if ":" in ip else socket.AF_INET
        info = socket.getaddrinfo(ip, 443, family, socket.SOCK_STREAM)
        af, st, pr, _, addr = info[0]
        s = socket.socket(af, st, pr)
        s.settimeout(timeout)
        s.connect(addr)
        
        target_sni = sni_domain if sni_domain else "cloudflare.com"
        
        # برقراری هندشیک TLS روی پورت ۴۴۳ با SNI کلادفلر (حتی روی آی‌پی آروان)
        with ctx.wrap_socket(s, server_hostname=target_sni) as tls:
            tls.sendall(
                f"GET /cdn-cgi/trace HTTP/1.1\r\n"
                f"Host: {target_sni}\r\n"
                f"Connection: close\r\n\r\n".encode()
            )
            d = tls.recv(256)
            if len(d) < 3:
                return None
        return (time.monotonic() - t0) * 1000
    except Exception:
        return None

def test_ip(ip, sni_domain, pcount=2):
    pings = []
    for _ in range(pcount):
        ms = ping_once(ip, sni_domain)
        if ms is None:
            return None
        pings.append(ms)
        time.sleep(0.02)
    return round(sum(pings) / len(pings), 1)

class IPRow(BoxLayout):
    def __init__(self, rank, ip, ms, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(52)
        self.padding = [dp(6), dp(2)]
        self.spacing = dp(2)
        self.ip = ip
        self.rank = rank

        top_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(26), spacing=dp(6))
        self.lbl_rank = Label(text=str(rank), size_hint_x=0.08, color=get_color_from_hex("#666666"),
                               font_size="12sp", halign="center", valign="middle")
        top_layout.add_widget(self.lbl_rank)

        self.lbl_ip = Label(text=ip, size_hint_x=0.76, color=get_color_from_hex("#00ccff"),
                            font_size="12sp", halign="left", valign="middle", shorten=True, shorten_from="right")
        self.lbl_ip.bind(on_touch_down=self.copy_ip_touch)
        top_layout.add_widget(self.lbl_ip)

        btn_copy = Button(text="COPY", size_hint_x=0.16, background_color=get_color_from_hex("#1a1a2e"),
                          color=get_color_from_hex("#00ccff"), font_size="10sp", bold=True)
        btn_copy.bind(on_press=self.copy_ip)
        top_layout.add_widget(btn_copy)
        self.add_widget(top_layout)

        bottom_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(20))
        bottom_layout.add_widget(Label(text="", size_hint_x=0.08))
        self.lbl_ping = Label(text=f"Ping: {ms:.0f} ms", size_hint_x=0.92, color=self.get_ping_color(ms),
                              font_size="12sp", bold=True, halign="left", valign="middle")
        self.lbl_ping.bind(size=self.lbl_ping.setter('text_size'))
        bottom_layout.add_widget(self.lbl_ping)
        self.add_widget(bottom_layout)

    def get_ping_color(self, ms):
        if ms < 450:
            return get_color_from_hex("#00ff88")
        elif ms < 650:
            return get_color_from_hex("#ffcc00")
        else:
            return get_color_from_hex("#ff4444")

    def update_data(self, rank, ip, ms):
        self.rank = rank
        self.ip = ip
        self.lbl_rank.text = str(rank)
        self.lbl_ip.text = ip
        self.lbl_ping.text = f"Ping: {ms:.0f} ms"
        self.lbl_ping.color = self.get_ping_color(ms)

    def copy_ip(self, *args):
        Clipboard.copy(self.ip)
        return True

    def copy_ip_touch(self, instance, touch):
        if self.lbl_ip.collide_point(*touch.pos):
            Clipboard.copy(self.ip)
            return True
        return False

class Amir6App(App):
    def build(self):
        self.title = "AMIR6 - CF IPv Scanner"
        self.running = False
        self.results = []
        self.tested = 0
        self.found = 0
        self.total = 1000
        self.lock = threading.Lock()
        self.q = None
        self.row_widgets = []
        self.save_data = None
        self.selected_isp = "AbrArvan CDN and IaaS"

        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))

        header = Label(text="[b][color=00ccff]AMIR6[/color]  Hybrid Scanner[/b]", markup=True,
                       size_hint_y=None, height=dp(30), font_size="16sp")
        root.add_widget(header)

        # Config Paste Box
        config_layout = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(56), spacing=dp(2))
        config_layout.add_widget(Label(text="Paste VLESS Config (Cloudflare/Worker):", size_hint_y=None, height=dp(16), color=get_color_from_hex("#00ccff"), font_size="10sp"))
        self.txt_config = TextInput(text="vless://uuid@185.121.201:443?type=ws&security=tls&sni=long-morning-7443.amirsanaei1313.workers.dev#OMID",
                                    multiline=False, size_hint_y=None, height=dp(36), font_size="10sp",
                                    background_color=get_color_from_hex("#1a1a2e"), foreground_color=(1,1,1,1))
        config_layout.add_widget(self.txt_config)
        root.add_widget(config_layout)

        # Count + Threads
        settings1 = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(6))
        settings1.add_widget(Label(text="Count:", size_hint_x=0.22, color=get_color_from_hex("#aaaaaa"), font_size="13sp"))
        self.spin_count = Spinner(text="1000", values=["500","1000","2000","3000","Custom"], size_hint_x=0.28,
                                  background_color=get_color_from_hex("#1a1a2e"), color=(1,1,1,1), font_size="14sp")
        self.spin_count.bind(text=self.on_count_select)
        settings1.add_widget(self.spin_count)

        settings1.add_widget(Label(text="Threads:", size_hint_x=0.22, color=get_color_from_hex("#aaaaaa"), font_size="13sp"))
        self.spin_threads = Spinner(text="100", values=["50","100","150","200"], size_hint_x=0.28,
                                    background_color=get_color_from_hex("#1a1a2e"), color=(1,1,1,1), font_size="14sp")
        settings1.add_widget(self.spin_threads)
        root.add_widget(settings1)

        # Type + ISP
        settings2 = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(6))
        settings2.add_widget(Label(text="Type:", size_hint_x=0.22, color=get_color_from_hex("#aaaaaa"), font_size="13sp"))
        self.spin_proto = Spinner(text="IPv4", values=["IPv4", "IPv6", "Both"], size_hint_x=0.28,
                                  background_color=get_color_from_hex("#1a1a2e"), color=(1,1,1,1), font_size="14sp")
        settings2.add_widget(self.spin_proto)

        settings2.add_widget(Label(text="ISP:", size_hint_x=0.15, color=get_color_from_hex("#aaaaaa"), font_size="13sp"))
        self.btn_isp = Button(text="AbrArvan CDN and IaaS", size_hint_x=0.35,
                              background_color=get_color_from_hex("#1a1a2e"), color=(1,1,1,1),
                              font_size="11sp", shorten=True)
        self.btn_isp.bind(on_press=self.open_isp_popup)
        settings2.add_widget(self.btn_isp)
        root.add_widget(settings2)

        # Buttons
        btn_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        self.btn_start = Button(text="START", background_color=get_color_from_hex("#005500"),
                                color=get_color_from_hex("#00ff88"), bold=True, font_size="14sp")
        self.btn_start.bind(on_press=self.start_scan)
        btn_row.add_widget(self.btn_start)

        self.btn_stop = Button(text="STOP", background_color=get_color_from_hex("#550000"),
                               color=get_color_from_hex("#ff4444"), bold=True, font_size="14sp", disabled=True)
        self.btn_stop.bind(on_press=self.stop_scan)
        btn_row.add_widget(self.btn_stop)

        self.btn_save = Button(text="SAVE", background_color=get_color_from_hex("#003355"),
                               color=get_color_from_hex("#00aaff"), bold=True, font_size="14sp")
        self.btn_save.bind(on_press=self.save_results)
        btn_row.add_widget(self.btn_save)

        self.btn_clear = Button(text="CLEAR", background_color=get_color_from_hex("#222222"),
                                color=get_color_from_hex("#aaaaaa"), bold=True, font_size="14sp")
        self.btn_clear.bind(on_press=self.clear_results)
        btn_row.add_widget(self.btn_clear)
        root.add_widget(btn_row)

        self.progress = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(8))
        root.add_widget(self.progress)

        self.lbl_status = Label(text="Ready", color=get_color_from_hex("#888888"),
                                size_hint_y=None, height=dp(24), font_size="13sp")
        root.add_widget(self.lbl_status)

        root.add_widget(Label(
            text="[color=00ff88]<450ms[/color]    [color=ffcc00]<650ms[/color]    [color=ff4444]>650ms[/color]    (tap IP or COPY)",
            markup=True, size_hint_y=None, height=dp(20), font_size="11sp"
        ))

        scroll = ScrollView(do_scroll_x=False)
        self.results_layout = GridLayout(cols=1, size_hint_y=None, spacing=dp(4), padding=[0, dp(4)])
        self.results_layout.bind(minimum_height=self.results_layout.setter("height"))
        for i in range(50):
            row = IPRow(i + 1, "—", 0)
            row.opacity = 0
            row.height = 0
            self.row_widgets.append(row)
            self.results_layout.add_widget(row)
        scroll.add_widget(self.results_layout)
        root.add_widget(scroll)

        self.lbl_best = Label(text="Best: —", color=get_color_from_hex("#00ff88"),
                              size_hint_y=None, height=dp(26), font_size="12sp", markup=True)
        root.add_widget(self.lbl_best)

        Clock.schedule_interval(self.flush_rows, 0.5)
        return root

    def open_isp_popup(self, *args):
        content = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(6))
        content.add_widget(Label(text="Select ISP", size_hint_y=None, height=dp(30),
                                 color=get_color_from_hex("#00ccff"), font_size="15sp", bold=True))

        scroll = ScrollView(do_scroll_x=False)
        layout = GridLayout(cols=1, size_hint_y=None, spacing=dp(4))
        layout.bind(minimum_height=layout.setter("height"))

        for isp in ISP_LIST:
            btn = Button(text=isp, size_hint_y=None, height=dp(42),
                         background_color=get_color_from_hex("#1a1a2e"),
                         color=(1,1,1,1), font_size="13sp")
            btn.bind(on_press=lambda x, name=isp: self.select_isp(name))
            layout.add_widget(btn)

        scroll.add_widget(layout)
        content.add_widget(scroll)

        btn_close = Button(text="Close", size_hint_y=None, height=dp(40),
                           background_color=get_color_from_hex("#333333"))
        content.add_widget(btn_close)

        self.isp_popup = Popup(title="", content=content, size_hint=(0.9, 0.75),
                               background_color=get_color_from_hex("#0d0d0d"))
        btn_close.bind(on_press=self.isp_popup.dismiss)
        self.isp_popup.open()

    def select_isp(self, name):
        self.selected_isp = name
        self.btn_isp.text = name
        if hasattr(self, "isp_popup"):
            self.isp_popup.dismiss()

    def on_count_select(self, spinner, text):
        if text == "Custom":
            self.show_custom_popup()

    def show_custom_popup(self):
        content = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        content.add_widget(Label(text="Enter custom count:", color=(1,1,1,1), font_size="14sp"))
        self.txt_custom = TextInput(text="5000", multiline=False, input_filter="int",
                                    font_size="16sp", size_hint_y=None, height=dp(40))
        content.add_widget(self.txt_custom)
        btn_ok = Button(text="SET", size_hint_y=None, height=dp(42),
                        background_color=get_color_from_hex("#005500"),
                        color=get_color_from_hex("#00ff88"), bold=True)
        content.add_widget(btn_ok)
        popup = Popup(title="Custom Count", content=content, size_hint=(0.8, 0.35),
                      background_color=get_color_from_hex("#1a1a2e"))
        def set_val(instance):
            val = self.txt_custom.text.strip()
            if val.isdigit() and int(val) > 0:
                self.spin_count.text = val
            popup.dismiss()
        btn_ok.bind(on_press=set_val)
        popup.open()

    def start_scan(self, *args):
        if self.running:
            return
        try:
            self.total = int(self.spin_count.text)
        except Exception:
            self.total = 1000
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
        self.lbl_status.text = f"Stopped — {self.found} IPs"
        self.lbl_status.color = get_color_from_hex("#ffcc00")

    def scan_worker(self):
        isp = self.selected_isp
        proto = self.spin_proto.text
        
        # استخراج هوشمند SNI از کانفیگ کلادفلر
        raw_config = self.txt_config.text.strip()
        sni_domain = parse_vless_config(raw_config)
        
        ranges = get_ranges(isp, proto)

        if not ranges:
            Clock.schedule_once(lambda dt: self.show_popup("Error", f"No ranges available for {isp} + {proto}"), 0)
            self.running = False
            Clock.schedule_once(lambda dt: setattr(self.btn_start, 'disabled', False), 0)
            Clock.schedule_once(lambda dt: setattr(self.btn_stop, 'disabled', True), 0)
            return

        self.q = Queue()
        for _ in range(self.total):
            ip = rand_ip_from_ranges(ranges)
            if ip:
                self.q.put(ip)

        threads = int(self.spin_threads.text)

        def worker():
            while self.running:
                try:
                    ip = self.q.get(timeout=0.5)
                except Empty:
                    break
                if not self.running:
                    self.q.task_done()
                    break
                ms = test_ip(ip, sni_domain)
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

        ts = [threading.Thread(target=worker, daemon=True) for _ in range(threads)]
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
            current = self.results[:50]

        for i, row in enumerate(self.row_widgets):
            if i < len(current):
                m, p = current[i]
                row.update_data(i + 1, p, m)
                row.opacity = 1
                row.height = dp(52)
            else:
                row.opacity = 0
                row.height = 0

        self.progress.value = min(pct, 100)
        self.lbl_status.text = f"Scanning... {tested}/{self.total}  |  Found: {found}"
        if self.results:
            best_ms, best_ip = self.results[0]
            self.lbl_best.text = f"Best: [color=00ccff]{best_ip}[/color]  [color=00ff88]{best_ms:.0f}ms[/color]"

    def scan_done(self, *args):
        self.running = False
        self.btn_start.disabled = False
        self.btn_stop.disabled = True
        self.lbl_status.text = f"Finished — {self.found} clean IPs"
        self.lbl_status.color = get_color_from_hex("#00ff88")
        self.progress.value = 100

    def save_results(self, *args):
        if not self.results:
            self.show_popup("Error", "No IPs to save!")
            return
        ip_text = "\n".join([ip for _, ip in self.results]) + "\n"
        Clipboard.copy(ip_text)
        self.save_data = ip_text
        try:
            from jnius import autoclass, cast
            from android import activity
            Intent = autoclass('android.content.Intent')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            intent = Intent(Intent.ACTION_CREATE_DOCUMENT)
            intent.addCategory(Intent.CATEGORY_OPENABLE)
            intent.setType("text/plain")
            intent.putExtra(Intent.EXTRA_TITLE, "clean_ip.txt")
            currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
            currentActivity.startActivityForResult(intent, 42)
            activity.bind(on_activity_result=self.on_activity_result)
        except Exception as e:
            self.show_popup("Error", f"Could not open save dialog:\n{str(e)}\n\nIPs are in clipboard.")

    def on_activity_result(self, request_code, result_code, intent):
        if request_code != 42:
            return
        try:
            from jnius import autoclass, cast
            Activity = autoclass('android.app.Activity')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            if result_code == Activity.RESULT_OK and intent is not None:
                uri = intent.getData()
                if uri is not None:
                    activity = PythonActivity.mActivity
                    resolver = activity.getContentResolver()
                    stream = resolver.openOutputStream(uri)
                    if stream is not None and self.save_data:
                        stream.write(self.save_data.encode("utf-8"))
                        stream.flush()
                        stream.close()
                        self.show_popup("Saved Successfully", f"{len(self.results)} IPs saved!\n\n(Also copied to clipboard)")
                        return
        except Exception as e:
            print("Save result error:", e)
        self.show_popup("Error", "Save cancelled or failed.\nIPs are still in clipboard.")

    def clear_results(self, *args):
        self.results = []
        for row in self.row_widgets:
            row.opacity = 0
            row.height = 0
        self.lbl_best.text = "Best: —"
        self.lbl_status.text = "Cleared"
        self.progress.value = 0

    def show_popup(self, title, msg):
        content = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        content.add_widget(Label(text=msg, color=(1,1,1,1), font_size="13sp", halign="center"))
        btn = Button(text="OK", size_hint_y=None, height=dp(42), background_color=get_color_from_hex("#005500"))
        content.add_widget(btn)
        popup = Popup(title=title, content=content, size_hint=(0.88, 0.38),
                      background_color=get_color_from_hex("#1a1a2e"))
        btn.bind(on_press=popup.dismiss)
        popup.open()

if __name__ == "__main__":
    Amir6App().run()
