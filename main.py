#!/usr/bin/env python3
# AMIR6 - Auto MSP Config Generator & IP Fetcher

import urllib.request
import urllib.parse
import json
import ssl
import random
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.core.clipboard import Clipboard
from kivy.metrics import dp

Window.clearcolor = get_color_from_hex("#0d0d0d")

class Amir6App(App):
    def build(self):
        self.title = "AMIR6 - Auto MSP Generator"

        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))

        # هدر برنامه
        header = Label(
            text="[b][color=00ccff]AMIR6[/color] Auto MSP & IP Manager[/b]",
            markup=True, size_hint_y=None, height=dp(32), font_size="16sp"
        )
        root.add_widget(header)

        # انتخاب منبع دریافت آی‌پی تمیز
        source_box = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        source_box.add_widget(Label(text="IP Source:", size_hint_x=0.25, color=get_color_from_hex("#aaaaaa"), font_size="12sp"))
        self.spin_source = Spinner(
            text="Arvan Clean IPs (Online List)",
            values=["Arvan Clean IPs (Online List)", "Cloudflare Clean IPs (Online List)"],
            size_hint_x=0.75,
            background_color=get_color_from_hex("#1a1a2e"), color=(1,1,1,1), font_size="12sp"
        )
        source_box.add_widget(self.spin_source)
        root.add_widget(source_box)

        # ورودی کانفیگ پایه (ورکر کلادفلر پورت 443)
        config_layout = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(70), spacing=dp(2))
        config_layout.add_widget(Label(text="Base Worker Config (VLESS / WS / TLS):", size_hint_y=None, height=dp(16), color=get_color_from_hex("#00ccff"), font_size="11sp"))
        self.txt_config = TextInput(
            text="vless://your-uuid-here@194.5.192.92:443?encryption=none&security=tls&sni=long-morning-7443.amirsanaei1313.workers.dev&type=ws&host=long-morning-7443.amirsanaei1313.workers.dev&path=%2F#AMIR6-AutoMSP",
            multiline=True, size_hint_y=None, height=dp(50), font_size="10sp",
            background_color=get_color_from_hex("#1a1a2e"), foreground_color=(1,1,1,1)
        )
        config_layout.add_widget(self.txt_config)
        root.add_widget(config_layout)

        # دکمه‌ی دریافت خودکار و ترکیب
        btn_box = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(8))
        self.btn_auto = Button(
            text="FIND IP & GENERATE CONFIG",
            background_color=get_color_from_hex("#005500"),
            color=get_color_from_hex("#00ff88"), bold=True, font_size="13sp"
        )
        self.btn_auto.bind(on_press=self.auto_fetch_and_generate)
        btn_box.add_widget(self.btn_auto)
        root.add_widget(btn_box)

        # وضعیت برنامه
        self.lbl_status = Label(
            text="Ready. Click the button to fetch clean IP and build config automatically.",
            color=get_color_from_hex("#888888"), size_hint_y=None, height=dp(25), font_size="11sp"
        )
        root.add_widget(self.lbl_status)

        # بخش نمایش خروجی نهایی
        output_layout = BoxLayout(orientation="vertical", spacing=dp(2))
        output_layout.add_widget(Label(text="Final Generated Config:", size_hint_y=None, height=dp(18), color=get_color_from_hex("#00ff88"), font_size="11sp", halign="left"))
        
        self.txt_output = TextInput(
            text="",
            readonly=True, multiline=True, font_size="10sp",
            background_color=get_color_from_hex("#111118"), foreground_color=get_color_from_hex("#00ccff")
        )
        output_layout.add_widget(self.txt_output)
        root.add_widget(output_layout)

        return root

    def auto_fetch_and_generate(self, *args):
        raw_config = self.txt_config.text.strip()
        if not raw_config:
            self.show_popup("Error", "Please enter your base worker config first!")
            return

        self.lbl_status.text = "Fetching fresh clean IP from online source..."
        self.lbl_status.color = get_color_from_hex("#ffcc00")

        try:
            url = "https://raw.githubusercontent.com/yebekhe/ArvanFilterBypasser/main/ips.txt"
            if "Cloudflare" in self.spin_source.text:
                url = "https://raw.githubusercontent.com/yebekhe/CFScanner/main/ips.txt"

            # دور زدن خطای گواهی SSL در محیط اندروید
            ctx_ssl = ssl._create_unverified_context()

            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=ctx_ssl, timeout=5) as response:
                content = response.read().decode('utf-8')
                ip_lines = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#")]

            if not ip_lines:
                raise Exception("No IPs found in online source.")

            clean_ip = random.choice(ip_lines)

            parts = raw_config.split("vless://")[1].split("#")
            main_part = parts[0]
            tag = f"#{parts[1]}" if len(parts) > 1 else "#AMIR6-AutoMSP"
            
            user_host_query = main_part.split("@")
            user_info = user_host_query[0]
            host_query = user_host_query[1].split("?")
            
            server_port = host_query[0]
            query_str = host_query[1] if len(host_query) > 1 else ""
            
            port = "443"
            if ":" in server_port:
                port = server_port.split(":")[1]

            new_server_port = f"{clean_ip}:{port}"
            final_config = f"vless://{user_info}@{new_server_port}?{query_str}{tag}"
            
            self.txt_output.text = final_config
            Clipboard.copy(final_config)
            
            self.lbl_status.text = f"Success! Used Clean IP: {clean_ip} (Copied)"
            self.lbl_status.color = get_color_from_hex("#00ff88")
            self.show_popup("Success", f"Clean IP found and mapped successfully!\n\nIP: {clean_ip}\n\nConfig copied to clipboard!")

        except Exception as e:
            self.lbl_status.text = "Failed to fetch online IP. Check internet connection."
            self.lbl_status.color = get_color_from_hex("#ff4444")
            self.show_popup("Error", f"Could not fetch clean IP:\n{str(e)}")

    def show_popup(self, title, msg):
        content = BoxLayout(orientation="vertical", padding=dp(15), spacing=dp(10))
        content.add_widget(Label(text=msg, color=(1,1,1,1), font_size="13sp", halign="center"))
        btn = Button(text="OK", size_hint_y=None, height=dp(40), background_color=get_color_from_hex("#005500"))
        content.add_widget(btn)
        popup = Popup(title=title, content=content, size_hint=(0.85, 0.35), background_color=get_color_from_hex("#1a1a2e"))
        btn.bind(on_press=popup.dismiss)
        popup.open()

if __name__ == "__main__":
    Amir6App().run()
