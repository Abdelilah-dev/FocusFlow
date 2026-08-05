import platform
import os
import json
import shutil
import subprocess
from backend.sites import Sites


class Blocker:

    DOH_IPS = [
        "1.1.1.1", "1.0.0.1", "104.16.248.249", "104.16.249.249",
        "8.8.8.8", "8.8.4.4",
        "9.9.9.9", "149.112.112.112",
        "185.228.168.168", "185.228.169.168",
        "94.140.14.14", "94.140.15.15",
        "208.67.222.222", "208.67.220.220",
    ]

    def __init__(self):
        self._os = platform.system()

        if self._os == "Windows":
            self.hosts_path = os.path.join(
                os.environ.get('SystemRoot', 'C:\\Windows'),
                'System32', 'drivers', 'etc', 'hosts'
            )
        else:
            self.hosts_path = "/etc/hosts"

        self.sites_instance = Sites()
        self._backup_created = False
        self._doh_disabled = False

    def _create_backup(self):
        if not self._backup_created and os.path.exists(self.hosts_path):
            backup_path = self.hosts_path + '.focusflow_backup'
            try:
                shutil.copy2(self.hosts_path, backup_path)
                self._backup_created = True
            except Exception:
                pass

    def _is_our_block_line(self, line):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            return False
        if '# FocusFlow' in stripped:
            return True
        return False

    def _run_cmd(self, cmd, check=False):
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
            return result.returncode == 0
        except Exception:
            return False

    def _disable_chrome_doh(self):
        if self._os == "Windows":
            local_appdata = os.environ.get('LOCALAPPDATA', '')
            browsers = {
                "Chrome": [os.path.join(local_appdata, "Google", "Chrome", "User Data")],
                "Edge": [os.path.join(local_appdata, "Microsoft", "Edge", "User Data")],
                "Brave": [os.path.join(local_appdata, "BraveSoftware", "Brave-Browser", "User Data")],
            }
        else:
            browsers = {
                "Chrome": [
                    "~/.config/google-chrome",
                    "~/.config/google-chrome-beta",
                    "~/.config/google-chrome-unstable",
                    "~/.config/chromium",
                ],
                "Edge": [
                    "~/.config/microsoft-edge",
                    "~/.config/microsoft-edge-beta",
                    "~/.config/microsoft-edge-dev",
                ],
                "Brave": [
                    "~/.config/BraveSoftware",
                ],
            }
        for browser_name, paths in browsers.items():
            for path in paths:
                expanded = os.path.expanduser(path)
                if not os.path.exists(expanded):
                    continue
                prefs_path = os.path.join(expanded, "Default", "Preferences")
                if os.path.exists(prefs_path):
                    try:
                        with open(prefs_path, "r", encoding="utf-8") as f:
                            prefs = json.load(f)
                        if "dns_over_https" not in prefs:
                            prefs["dns_over_https"] = {}
                        prefs["dns_over_https"]["mode"] = "off"
                        with open(prefs_path, "w", encoding="utf-8") as f:
                            json.dump(prefs, f)
                    except Exception:
                        pass

    def _disable_firefox_doh(self):
        if self._os == "Windows":
            appdata = os.environ.get('APPDATA', '')
            firefox_dirs = [os.path.join(appdata, "Mozilla", "Firefox", "Profiles")]
        else:
            firefox_dirs = [
                "~/.mozilla/firefox",
                "~/.var/app/org.mozilla.firefox/.mozilla/firefox",
                "~/snap/firefox/common/.mozilla/firefox",
            ]
        for ff_dir in firefox_dirs:
            expanded = os.path.expanduser(ff_dir)
            if not os.path.exists(expanded):
                continue
            for profile in os.listdir(expanded):
                profile_path = os.path.join(expanded, profile)
                if not os.path.isdir(profile_path):
                    continue
                prefs_js = os.path.join(profile_path, "prefs.js")
                user_js = os.path.join(profile_path, "user.js")
                try:
                    with open(user_js, "a", encoding="utf-8") as f:
                        f.write("\n// FocusFlow: Disable DNS-over-HTTPS\n")
                        f.write('user_pref("network.trr.mode", 5);\n')
                        f.write('user_pref("network.dns.disablePrefetch", true);\n')
                        f.write('user_pref("network.dns.disablePrefetchFromHTTPS", true);\n')
                    if os.path.exists(prefs_js):
                        with open(prefs_js, "r", encoding="utf-8") as f:
                            content = f.read()
                        content = content.replace(
                            'user_pref("network.trr.mode"',
                            '// FocusFlow disabled: user_pref("network.trr.mode"'
                        )
                        if 'user_pref("network.trr.mode", 5)' not in content:
                            content += '\nuser_pref("network.trr.mode", 5);\n'
                        with open(prefs_js, "w", encoding="utf-8") as f:
                            f.write(content)
                except Exception:
                    pass

    def _disable_opera_doh(self):
        if self._os == "Windows":
            appdata = os.environ.get('APPDATA', '')
            opera_dirs = [
                os.path.join(appdata, "Opera Software", "Opera Stable"),
                os.path.join(appdata, "Opera Software", "Opera Beta"),
                os.path.join(appdata, "Opera Software", "Opera Developer"),
            ]
        else:
            opera_dirs = [
                "~/.config/opera",
                "~/.config/opera-beta",
                "~/.config/opera-developer",
            ]
        for op_dir in opera_dirs:
            expanded = os.path.expanduser(op_dir)
            if not os.path.exists(expanded):
                continue
            prefs_path = os.path.join(expanded, "Preferences")
            if os.path.exists(prefs_path):
                try:
                    with open(prefs_path, "r", encoding="utf-8") as f:
                        prefs = json.load(f)
                    if "dns_over_https" not in prefs:
                        prefs["dns_over_https"] = {}
                    prefs["dns_over_https"]["mode"] = "off"
                    with open(prefs_path, "w", encoding="utf-8") as f:
                        json.dump(prefs, f)
                except Exception:
                    pass

    def _block_doh_firewall(self):
        if self._os == "Windows":
            self._block_doh_firewall_windows()
        elif self._os == "Linux":
            self._block_doh_firewall_linux()

        def _block_doh_firewall_linux(self):
        rules = [
            "sudo iptables -C OUTPUT -p tcp --dport 853 -j DROP 2>/dev/null || sudo iptables -A OUTPUT -p tcp --dport 853 -j DROP",
            "sudo iptables -C OUTPUT -p udp --dport 853 -j DROP 2>/dev/null || sudo iptables -A OUTPUT -p udp --dport 853 -j DROP",
            "sudo ip6tables -C OUTPUT -p tcp --dport 853 -j DROP 2>/dev/null || sudo ip6tables -A OUTPUT -p tcp --dport 853 -j DROP",
            "sudo ip6tables -C OUTPUT -p udp --dport 853 -j DROP 2>/dev/null || sudo ip6tables -A OUTPUT -p udp --dport 853 -j DROP",
        ]
        for ip in self.DOH_IPS:
            if ":" in ip:
                rules.append(f"sudo ip6tables -C OUTPUT -d {ip} -j DROP 2>/dev/null || sudo ip6tables -A OUTPUT -d {ip} -j DROP")
            else:
                rules.append(f"sudo iptables -C OUTPUT -d {ip} -j DROP 2>/dev/null || sudo iptables -A OUTPUT -d {ip} -j DROP")
        for rule in rules:
            self._run_cmd(rule)
        try:
            os.makedirs("/etc/iptables", exist_ok=True)
            self._run_cmd("sudo bash -c 'iptables-save > /etc/iptables/rules.v4'")
            self._run_cmd("sudo bash -c 'ip6tables-save > /etc/iptables/rules.v6'")
        except Exception:
            pass

    def _block_doh_firewall_windows(self):
        self._run_cmd('netsh advfirewall firewall delete rule name="FocusFlow_DoH_TCP"')
        self._run_cmd('netsh advfirewall firewall add rule name="FocusFlow_DoH_TCP" dir=out action=block protocol=TCP remoteport=853')
        self._run_cmd('netsh advfirewall firewall delete rule name="FocusFlow_DoH_UDP"')
        self._run_cmd('netsh advfirewall firewall add rule name="FocusFlow_DoH_UDP" dir=out action=block protocol=UDP remoteport=853')
        for ip in self.DOH_IPS:
            rule_name = "FocusFlow_DoH_" + ip.replace(".", "_").replace(":", "_")
            self._run_cmd(f'netsh advfirewall firewall delete rule name="{rule_name}"')
            self._run_cmd(f'netsh advfirewall firewall add rule name="{rule_name}" dir=out action=block remoteip={ip}')

        def _flush_dns(self):
        system = platform.system()
        try:
            if system == "Linux":
                subprocess.run(["sudo", "systemctl", "restart", "systemd-resolved"], check=False, capture_output=True)
                subprocess.run(["sudo", "systemctl", "restart", "nscd"], check=False, capture_output=True)
                subprocess.run(["sudo", "resolvectl", "flush-caches"], check=False, capture_output=True)
            elif system == "Darwin":
                subprocess.run(["dscacheutil", "-flushcache"], check=False, capture_output=True)
                subprocess.run(["killall", "-HUP", "mDNSResponder"], check=False, capture_output=True)
            elif system == "Windows":
                subprocess.run(["ipconfig", "/flushdns"], check=False, capture_output=True)
        except Exception:
            pass

    def _disable_all_doh(self):
        if self._doh_disabled:
            return
        self._disable_chrome_doh()
        self._disable_firefox_doh()
        self._disable_opera_doh()
        self._block_doh_firewall()
        self._doh_disabled = True

    def block_sites(self):
        try:
            self._disable_all_doh()
            self._create_backup()
            self.unblock_sites()

            with open(self.hosts_path, 'a', encoding='utf-8') as s:
                for site in self.sites_instance.sites:
                    s.write(f"0.0.0.0 {site} # FocusFlow\n")
                    s.write(f"127.0.0.1 {site} # FocusFlow\n")
                    s.write(f":: {site} # FocusFlow\n")
                    if not site.startswith("www."):
                        s.write(f"0.0.0.0 www.{site} # FocusFlow\n")
                        s.write(f"127.0.0.1 www.{site} # FocusFlow\n")
                        s.write(f":: www.{site} # FocusFlow\n")
                    for sub in ["m.", "mobile.", "app.", "api."]:
                        s.write(f"0.0.0.0 {sub}{site} # FocusFlow\n")
                        s.write(f"127.0.0.1 {sub}{site} # FocusFlow\n")

            self._flush_dns()
            return True

        except PermissionError:
            return False
        except OSError as e:
            print(f"[Blocker] Error blocking: {e}")
            return False

    def unblock_sites(self):
        if not os.path.exists(self.hosts_path):
            return

        try:
            with open(self.hosts_path, 'r', encoding='utf-8') as s:
                lines = s.readlines()

            with open(self.hosts_path, 'w', encoding='utf-8') as s:
                for line in lines:
                    if not self._is_our_block_line(line):
                        s.write(line)

        except PermissionError:
            print("[Blocker] Permission denied: cannot unblock sites.")
        except OSError as e:
            print(f"[Blocker] Error unblocking: {e}")
