#!/usr/bin/env python3
# AMIR6 - CF IPv6 Scanner (Improved UI)

import threading, socket, ssl, time, random, ipaddress, os
from queue import Queue, Empty

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.core.clipboard import Clipboard

Window.clearcolor = get_color_from_hex("#0d0d0d")

CF_SUBNETS = [
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

def get_save_path():
    paths = [
        "/storage/emulated/0/Download/clean_ipv6.txt",
        "/sdcard/Download/clean_ipv6.txt",
        os.path.expanduser("\~/clean_ipv6.txt"),
    ]
    for p in paths:
        try:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "a").close()
            return p
        except:
            pass
    return paths[-1]

def rand_ip():
    net = ipaddress.IPv6Network(random.choice(CF_SUBNETS), strict=False)
    n = int(net.num_addresses)
    return str(net.network_address + random.randint(1, n - 2))

def ping_once(ip, timeout=4.0):
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        t0 = time.monotonic()
        info = socket.getaddrinfo(ip, 443, socket.AF_INET6, socket.SOCK_STREAM)
        af, st, pr, _, addr = info[0]
        s = socket.socket(af, st, pr)
        s.settimeout(timeout)
        s.connect(addr)
        with ctx.wrap_socket(s, server_hostname="cloudflare.com") as tls:
            tls.sendall(
                b"GET /cdn-cgi/trace HTTP/1.1\r\n"
                b"Host: cloudflare.com\r\n"
                b"Connection: close\r\n\r\n"
            )
            d = tls.recv(256)
            if len(d) < 10:
                return None
        return (time.monotonic() - t0) * 1000
    except:
        return None

def test_ip(ip, pcount=2):
    pings = []
    for _ in range(pcount):
        ms = ping_once(ip)
        if ms is None:
            return None
        pings.append(ms)
        time.sleep(0.02)
    return round(sum(pings) / len(pings), 1)


class IPRow(BoxLayout):
    def __init__(self, rank, ip, ms, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(42)
        self.padding = [dp(8), dp(4)]
        self.spacing = dp(6)
        self.ip = ip

        if ms < 450:
            color = get_color_from_hex("#00ff88")
        elif ms < 650:
            color = get_color_from_hex("#ffcc00")
        else:
            color = get_color_from_hex("#ff4444")

        # Rank
        self.add_widget(Label(
            text=f"{rank}",
            size_hint_x=0.08,
            color=get_color_from_hex("#666666"),
            font_size="12sp",
            halign="center",
            valign="middle"
        ))

        # IP (clickable to copy)
        ip_label = Label(
            text=ip,
            size_hint_x=0.62,
            color=get_color_from_hex("#00ccff"),
            font_size="12sp",
            halign="left",
            valign="middle",
            shorten=True,
            shorten_from="right"
        )
        ip_label.bind(on_touch_down=self.copy_ip)
        self.add_widget(ip_label)

        # Ping
        self.add_widget(Label(
            text=f"{ms:.0f} ms",
            size_hint_x=0.22,
            color=color,
            font_size="13sp",
            bold=True,
            halign="right",
            valign="middle"
        ))

        # Copy button
        btn_copy = Button(
            text="📋",
            size_hint_x=0.08,
            background_color=get_color_from_hex("#1a1a2e"),
            font_size="14sp"
        )
        btn_copy.bind(on_press=self.copy_ip)
        self.add_widget(btn_copy)

    def copy_ip(self, *args):
        Clipboard.copy(self.ip)
        return True


class Amir6App(App):
    def build(self):
        self.title = "AMIR6 - CF IPv6 Scanner"
        self.running = False
        self.results = []
        self.tested = 0
        self.found = 0
        self.total = 0
        self.lock = threading.Lock()

        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))

        # Header
        header = Label(
            text="[b][color=00ccff]AMIR6[/color]  CF IPv6 Scanner[/b]",
            markup=True,
            size_hint_y=None,
            height=dp(36),
            font_size="16sp"
        )
        root.add_widget(header)

        # Settings
        settings = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        settings.add_widget(Label(text="Count:", size_hint_x=0.22, color=get_color_from_hex("#aaaaaa"), font_size="13sp"))
        self.spin_count = Spinner(text="1000", values=["500","1000","2000","3000"], size_hint_x=0.28, background_color=get_color_from_hex("#1a1a2e"), color=(1,1,1,1), font_size="14sp")
        settings.add_widget(self.spin_count)
        settings.add_widget(Label(text="Threads:", size_hint_x=0.22, color=get_color_from_hex("#aaaaaa"), font_size="13sp"))
        self.spin_threads = Spinner(text="100", values=["50","100","150","200"], size_hint_x=0.28, background_color=get_color_from_hex("#1a1a2e"), color=(1,1,1,1), font_size="14sp")
        settings.add_widget(self.spin_threads)
        root.add_widget(settings)

        # Buttons
        btn_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(6))
        self.btn_start = Button(text="START", background_color=get_color_from_hex("#005500"), color=get_color_from_hex("#00ff88"), bold=True, font_size="14sp")
        self.btn_start.bind(on_press=self.start_scan)
        btn_row.add_widget(self.btn_start)
        self.btn_stop = Button(text="STOP", background_color=get_color_from_hex("#550000"), color=get_color_from_hex("#ff4444"), bold=True, font_size="14sp", disabled=True)
        self.btn_stop.bind(on_press=self.stop_scan)
        btn_row.add_widget(self.btn_stop)
        self.btn_save = Button(text="SAVE", background_color=get_color_from_hex("#003355"), color=get_color_from_hex("#00aaff"), bold=True, font_size="14sp")
        self.btn_save.bind(on_press=self.save_results)
        btn_row.add_widget(self.btn_save)
        self.btn_clear = Button(text="CLEAR", background_color=get_color_from_hex("#222222"), color=get_color_from_hex("#aaaaaa"), bold=True, font_size="14sp")
        self.btn_clear.bind(on_press=self.clear_results)
        btn_row.add_widget(self.btn_clear)
        root.add_widget(btn_row)

        # Progress + Status
        self.progress = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(10))
        root.add_widget(self.progress)
        self.lbl_status = Label(text="Ready", color=get_color_from_hex("#888888"), size_hint_y=None, height=dp(26), font_size="13sp")
        root.add_widget(self.lbl_status)

        # Legend
        root.add_widget(Label(
            text="[color=00ff88]<450ms[/color]    [color=ffcc00]<650ms[/color]    [color=ff4444]>650ms[/color]    (tap IP or 📋 to copy)",
            markup=True, size_hint_y=None, height=dp(22), font_size="11sp"
        ))

        # Results
        scroll = ScrollView(do_scroll_x=False)
        self.results_layout = GridLayout(cols=1, size_hint_y=None, spacing=dp(3), padding=[0, dp(4)])
        self.results_layout.bind(minimum_height=self.results_layout.setter("height"))
        scroll.add_widget(self.results_layout)
        root.add_widget(scroll)

        # Best
        self.lbl_best = Label(text="Best: —", color=get_color_from_hex("#00ff88"), size_hint_y=None, height=dp(28), font_size="12sp", markup=True)
        root.add_widget(self.lbl_best)

        Clock.schedule_interval(self.flush_rows, 0.5)
        return root

    def start_scan(self, *args):
        if self.running: return
        self.running = True
        self.results = []
        self.tested = 0
        self.found = 0
        self.total = int(self.spin_count.text)
        self.results_layout.clear_widgets()
        self.progress.value = 0
        self.btn_start.disabled = True
        self.btn_stop.disabled = False
        self.lbl_status.color = get_color_from_hex("#00ccff")
        threading.Thread(target=self.scan_worker, daemon=True).start()

    def stop_scan(self, *args):
        self.running = False
        self.btn_start.disabled = False
        self.btn_stop.disabled = True
        self.lbl_status.text = f"Stopped — {self.found} IPs"
        self.lbl_status.color = get_color_from_hex("#ffcc00")

    def scan_worker(self):
        q = Queue()
        for _ in range(self.total):
            q.put(rand_ip())
        threads = int(self.spin_threads.text)

        def worker():
            while self.running:
                try:
                    ip = q.get(timeout=1)
                except Empty:
                    break
                ms = test_ip(ip)
                with self.lock:
                    self.tested += 1
                    if ms is not None:
                        self.found += 1
                        self.results.append((ms, ip))
                        self.results.sort()
                q.task_done()

        ts = [threading.Thread(target=worker, daemon=True) for _ in range(threads)]
        for t in ts: t.start()
        for t in ts: t.join()
        if self.running:
            Clock.schedule_once(self.scan_done, 0)

    def flush_rows(self, dt):
        with self.lock:
            pct = (self.tested / self.total * 100) if self.total else 0
            found = self.found
            tested = self.tested
            current = self.results[:50]

        self.results_layout.clear_widgets()
        for i, (m, p) in enumerate(current, 1):
            self.results_layout.add_widget(IPRow(i, p, m))

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
        path = get_save_path()
        existing = set()
        if os.path.exists(path):
            existing = {l.strip() for l in open(path) if l.strip()}
        all_ips = existing | {ip for _, ip in self.results}
        with open(path, "w") as f:
            for ip in sorted(all_ips):
                f.write(ip + "\n")
        self.show_popup("Saved ✓", f"{len(all_ips)} IPs saved to:\n\n{path}\n\n(You can find it in Download folder)")

    def clear_results(self, *args):
        self.results = []
        self.results_layout.clear_widgets()
        self.lbl_best.text = "Best: —"
        self.lbl_status.text = "Cleared"
        self.progress.value = 0

    def show_popup(self, title, msg):
        content = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        content.add_widget(Label(text=msg, color=(1,1,1,1), font_size="13sp", halign="center"))
        btn = Button(text="OK", size_hint_y=None, height=dp(42), background_color=get_color_from_hex("#005500"))
        content.add_widget(btn)
        popup = Popup(title=title, content=content, size_hint=(0.88, 0.38), background_color=get_color_from_hex("#1a1a2e"))
        btn.bind(on_press=popup.dismiss)
        popup.open()


if __name__ == "__main__":
    Amir6App().run()
