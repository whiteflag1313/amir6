#!/usr/bin/env python3
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
from kivy.uix.filechooser import FileChooserListView
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

DEFAULT_SAVE = "/storage/emulated/0/Download/clean_ipv6.txt"

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
            tls.sendall(b"GET /cdn-cgi/trace HTTP/1.1\r\nHost: cloudflare.com\r\nConnection: close\r\n\r\n")
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
        self.orientation  = "horizontal"
        self.size_hint_y  = None
        self.height       = dp(48)
        self.padding      = [dp(6), dp(2)]
        self.spacing      = dp(4)
        self.ip           = ip

        # رنگ پینگ
        if ms < 450:
            clr = get_color_from_hex("#00ff88")
        elif ms < 650:
            clr = get_color_from_hex("#ffcc00")
        else:
            clr = get_color_from_hex("#ff4444")

        # ─── rank ───
        self.add_widget(Label(
            text=f"[b]{rank}[/b]",
            markup=True,
            size_hint_x=None,
            width=dp(30),
            color=get_color_from_hex("#555555"),
            font_size="12sp",
            halign="center",
            valign="middle"
        ))

        # ─── IP ───
        self.add_widget(Label(
            text=ip,
            size_hint_x=1,
            color=get_color_from_hex("#00ccff"),
            font_size="11sp",
            halign="left",
            valign="middle",
            shorten=True,
            shorten_from="right",
            text_size=(None, None)
        ))

        # ─── ping ───
        self.add_widget(Label(
            text=f"[b]{ms:.0f}ms[/b]",
            markup=True,
            size_hint_x=None,
            width=dp(62),
            color=clr,
            font_size="13sp",
            halign="center",
            valign="middle"
        ))

        # ─── copy btn ───
        btn = Button(
            text="📋",
            size_hint_x=None,
            width=dp(38),
            background_color=get_color_from_hex("#1a2233"),
            font_size="15sp"
        )
        btn.bind(on_press=lambda x: self.copy())
        self.add_widget(btn)

        # خط جدا کننده
        self.canvas.after  # خط پایین هر ردیف از padding میاد

    def copy(self):
        Clipboard.copy(self.ip)


class Amir6App(App):
    def build(self):
        self.title    = "AMIR6"
        self.running  = False
        self.results  = []
        self.tested   = 0
        self.found    = 0
        self.total    = 0
        self.lock     = threading.Lock()
        self.save_path = DEFAULT_SAVE

        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(6))

        # ─── Header ───
        root.add_widget(Label(
            text="[b][color=00ccff]AMIR6[/color]  CF IPv6 Scanner[/b]",
            markup=True, size_hint_y=None, height=dp(34), font_size="15sp"
        ))

        # ─── Settings ───
        s = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(6))
        s.add_widget(Label(text="Count:", size_hint_x=0.20, color=get_color_from_hex("#aaa"), font_size="13sp"))
        self.spin_count = Spinner(text="1000", values=["300","500","1000","2000","3000"],
            size_hint_x=0.25, background_color=get_color_from_hex("#1a2233"), color=(1,1,1,1), font_size="13sp")
        s.add_widget(self.spin_count)
        s.add_widget(Label(text="Threads:", size_hint_x=0.22, color=get_color_from_hex("#aaa"), font_size="13sp"))
        self.spin_threads = Spinner(text="100", values=["50","100","150","200"],
            size_hint_x=0.25, background_color=get_color_from_hex("#1a2233"), color=(1,1,1,1), font_size="13sp")
        s.add_widget(self.spin_threads)
        root.add_widget(s)

        # ─── Save path ───
        sp = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(6))
        self.lbl_path = Label(
            text=self.save_path, color=get_color_from_hex("#666"),
            font_size="10sp", halign="left", valign="middle",
            size_hint_x=0.78, shorten=True, shorten_from="left"
        )
        sp.add_widget(self.lbl_path)
        btn_pick = Button(text="📁 مسیر", size_hint_x=0.22,
            background_color=get_color_from_hex("#222233"), font_size="11sp")
        btn_pick.bind(on_press=self.pick_path)
        sp.add_widget(btn_pick)
        root.add_widget(sp)

        # ─── Buttons ───
        br = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(6))
        self.btn_start = Button(text="▶ START", background_color=get_color_from_hex("#005500"),
            color=get_color_from_hex("#00ff88"), bold=True, font_size="14sp")
        self.btn_start.bind(on_press=self.start_scan)
        br.add_widget(self.btn_start)
        self.btn_stop = Button(text="■ STOP", background_color=get_color_from_hex("#550000"),
            color=get_color_from_hex("#ff4444"), bold=True, font_size="14sp", disabled=True)
        self.btn_stop.bind(on_press=self.stop_scan)
        br.add_widget(self.btn_stop)
        self.btn_save = Button(text="💾 SAVE", background_color=get_color_from_hex("#003355"),
            color=get_color_from_hex("#00aaff"), bold=True, font_size="14sp")
        self.btn_save.bind(on_press=self.save_results)
        br.add_widget(self.btn_save)
        self.btn_clear = Button(text="🗑 CLEAR", background_color=get_color_from_hex("#222"),
            color=get_color_from_hex("#aaa"), bold=True, font_size="14sp")
        self.btn_clear.bind(on_press=self.clear_results)
        br.add_widget(self.btn_clear)
        root.add_widget(br)

        # ─── Progress ───
        self.progress = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(8))
        root.add_widget(self.progress)
        self.lbl_status = Label(text="Ready — press START",
            color=get_color_from_hex("#666"), size_hint_y=None, height=dp(24), font_size="12sp")
        root.add_widget(self.lbl_status)

        # ─── Legend ───
        root.add_widget(Label(
            text="[color=00ff88]●<450ms[/color]  [color=ffcc00]●<650ms[/color]  [color=ff4444]●>650ms[/color]   📋 کپی IP",
            markup=True, size_hint_y=None, height=dp(20), font_size="11sp"
        ))

        # ─── Divider ───
        root.add_widget(Label(
            text="─" * 80, size_hint_y=None, height=dp(2),
            color=get_color_from_hex("#222233"), font_size="8sp"
        ))

        # ─── Results ───
        scroll = ScrollView(do_scroll_x=False)
        self.results_layout = GridLayout(
            cols=1, size_hint_y=None, spacing=dp(2), padding=[0, dp(2)]
        )
        self.results_layout.bind(minimum_height=self.results_layout.setter("height"))
        scroll.add_widget(self.results_layout)
        root.add_widget(scroll)

        # ─── Best ───
        self.lbl_best = Label(
            text="Best: —", markup=True,
            color=get_color_from_hex("#00ff88"),
            size_hint_y=None, height=dp(26), font_size="12sp"
        )
        root.add_widget(self.lbl_best)

        Clock.schedule_interval(self.flush_ui, 0.4)
        return root

    # ─── File picker ───
    def pick_path(self, *args):
        content = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(8))
        fc = FileChooserListView(
            path="/storage/emulated/0/",
            filters=["*.txt"],
            dirselect=True
        )
        content.add_widget(fc)

        btns = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
        btn_ok = Button(text="انتخاب", background_color=get_color_from_hex("#005500"))
        btn_cancel = Button(text="لغو", background_color=get_color_from_hex("#550000"))
        btns.add_widget(btn_ok)
        btns.add_widget(btn_cancel)
        content.add_widget(btns)

        popup = Popup(title="انتخاب مسیر ذخیره", content=content,
            size_hint=(0.95, 0.85), background_color=get_color_from_hex("#0d0d1a"))

        def on_ok(*a):
            if fc.selection:
                sel = fc.selection[0]
                if os.path.isdir(sel):
                    self.save_path = os.path.join(sel, "clean_ipv6.txt")
                else:
                    self.save_path = sel
            else:
                self.save_path = os.path.join(fc.path, "clean_ipv6.txt")
            self.lbl_path.text = self.save_path
            popup.dismiss()

        btn_ok.bind(on_press=on_ok)
        btn_cancel.bind(on_press=popup.dismiss)
        popup.open()

    # ─── Scan ───
    def start_scan(self, *args):
        if self.running: return
        self.running = True
        self.results = []
        self.tested = self.found = 0
        self.total = int(self.spin_count.text)
        self.results_layout.clear_widgets()
        self.progress.value = 0
        self.btn_start.disabled = True
        self.btn_stop.disabled = False
        self.lbl_status.color = get_color_from_hex("#00ccff")
        threading.Thread(target=self._scan_worker, daemon=True).start()

    def stop_scan(self, *args):
        self.running = False
        self.btn_start.disabled = False
        self.btn_stop.disabled = True

    def _scan_worker(self):
        q = Queue()
        for _ in range(self.total): q.put(rand_ip())
        n = int(self.spin_threads.text)

        def worker():
            while self.running:
                try: ip = q.get(timeout=1)
                except Empty: break
                ms = test_ip(ip)
                with self.lock:
                    self.tested += 1
                    if ms is not None:
                        self.found += 1
                        self.results.append((ms, ip))
                        self.results.sort()
                q.task_done()

        ts = [threading.Thread(target=worker, daemon=True) for _ in range(n)]
        for t in ts: t.start()
        for t in ts: t.join()
        if self.running:
            Clock.schedule_once(lambda dt: self._scan_done(), 0)

    def _scan_done(self):
        self.running = False
        self.btn_start.disabled = False
        self.btn_stop.disabled = True
        self.lbl_status.text = f"✓ Finished — {self.found} clean IPs"
        self.lbl_status.color = get_color_from_hex("#00ff88")
        self.progress.value = 100

    # ─── UI flush ───
    def flush_ui(self, dt):
        with self.lock:
            pct   = (self.tested / self.total * 100) if self.total else 0
            found = self.found
            tested = self.tested
            data  = self.results[:60]

        self.results_layout.clear_widgets()
        for i, (ms, ip) in enumerate(data, 1):
            self.results_layout.add_widget(IPRow(i, ip, ms))

        self.progress.value = min(pct, 100)
        if self.running:
            self.lbl_status.text = f"Scanning {tested}/{self.total}  |  Found: {found}"
        if data:
            bms, bip = data[0]
            self.lbl_best.text = f"Best: [color=00ccff]{bip}[/color]  [color=00ff88]{bms:.0f}ms[/color]"

    # ─── Save ───
    def save_results(self, *args):
        if not self.results:
            self.show_popup("خطا", "نتیجه‌ای نیست!"); return
        try:
            os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
        except: pass
        existing = set()
        if os.path.exists(self.save_path):
            existing = {l.strip() for l in open(self.save_path) if l.strip()}
        all_ips = existing | {ip for _, ip in self.results}
        with open(self.save_path, "w") as f:
            for ip in sorted(all_ips):
                f.write(ip + "\n")
        self.show_popup("ذخیره شد ✓", f"{len(all_ips)} IP\n\n{self.save_path}")

    def clear_results(self, *args):
        self.results = []
        self.results_layout.clear_widgets()
        self.lbl_best.text = "Best: —"
        self.lbl_status.text = "Cleared"
        self.progress.value = 0

    def show_popup(self, title, msg):
        c = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        c.add_widget(Label(text=msg, color=(1,1,1,1), font_size="13sp", halign="center"))
        btn = Button(text="OK", size_hint_y=None, height=dp(42),
            background_color=get_color_from_hex("#005500"))
        c.add_widget(btn)
        p = Popup(title=title, content=c, size_hint=(0.88, 0.4),
            background_color=get_color_from_hex("#0d0d1a"))
        btn.bind(on_press=p.dismiss)
        p.open()


if __name__ == "__main__":
    Amir6App().run()
