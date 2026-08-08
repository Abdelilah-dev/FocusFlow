[![FocusFlow Banner](https://github.com/Abdelilah-dev/FocusFlow/raw/main/FocusFlowBanner.png)](https://github.com/Abdelilah-dev/FocusFlow/blob/main/FocusFlowBanner.png)

# 🎯 FocusFlow

**An all-in-one, high-performance desktop workspace built to help you maintain deep focus, manage workflow, and block distractions on Windows and Linux.**

[![License: MIT](https://img.shields.io/badge/License-MIT-gold.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10%2B-ffc107.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-blue.svg)](#-installation)
[![UI Theme](https://img.shields.io/badge/UI-Dark%20%26%20Gold%20Aesthetic-111111.svg)](#-interface-preview)
[![AUR](https://img.shields.io/badge/AUR-focusflow--git-1793d1.svg)](#option-2-arch-linux-aur)

[📥 Download Installer](https://github.com/Abdelilah-dev/FocusFlow/releases/latest) • [🐛 Report Bug](https://github.com/Abdelilah-dev/FocusFlow/issues) • [⭐ Request Feature](https://github.com/Abdelilah-dev/FocusFlow/issues)

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Interface Preview](#-interface-preview)
- [Installation](#-installation)
- [Running from Source](#-running-from-source-windows--linux)
- [Running Without Repeated `sudo` Prompts](#-running-without-repeated-sudo-prompts-linux)
- [What FocusFlow Modifies](#️-what-focusflow-modifies-transparency)
- [Known Limitations](#-known-limitations)
- [Uninstalling](#️-uninstalling)
- [License](#-license)

---

## 🌟 Overview

**FocusFlow** is a sleek, cross-platform productivity application designed for developers, students, and power users. Built with a modern **Dark & Gold aesthetic**, it combines a **Pomodoro timer**, **ambient audio background**, a **Kanban task board**, and a **hard-blocking website tool** that works seamlessly on both **Windows** and **Linux**.

---

## ✨ Key Features

### ⏱️ Custom Focus & Break Timer

- **Flexible Intervals**: Easily configure and toggle between Focus and Break durations tailored to your workflow.
- **Audio & Visual Alerts**: Receive notification cues and audio alerts when completing focus sessions.
- **System Tray Support**: Runs smoothly in the background via the system tray without cluttering your desktop.

### 🚫 Advanced Site & Distraction Blocker

- **System-Level Blocking**: Redirects blocked domains directly to `0.0.0.0` inside system hosts files (`/etc/hosts` on Linux and `C:\Windows\System32\drivers\etc\hosts` on Windows).
- **Bypasses Encrypted DNS**: Disables Secure DNS / DNS-over-HTTPS in Chrome, Firefox, and Opera, and firewalls off common DoH resolvers so blocked sites can't sneak past the hosts file.
- **Active Session Termination**: Instantly closes active tabs navigating to blacklisted domains.
- **Instant Blacklist**: Enter a domain name and click **Add** to enforce instant restriction.

### 🎵 Ambient Soundscapes

- **4 High-Quality Audio Tracks**: Rain 🌧️, Wind 💨, Ocean 🌊, and Forest 🌲.
- **Smooth Audio Engine**: Features seamless **Fade-In & Fade-Out** audio transitions to prevent sharp sound interruptions.
- **Single-Track Focus**: Play one ambient environment at a time for maximum concentration.

### 📋 Interactive Kanban Task Board

- **4 Workflow Columns**: `TO DO`, `IN PROGRESS`, `DONE`, and `REFUSED`.
- **Progress Counter**: Dynamic task tracking showing completed items vs total tasks.
- **One-Click Clear**: Quickly reset your board for fresh daily sessions.

---

## 📸 Interface Preview

[![FocusFlow Dashboard](https://github.com/Abdelilah-dev/FocusFlow/raw/main/FocusFlow.png)](https://github.com/Abdelilah-dev/FocusFlow/blob/main/FocusFlow.png)

---

## 📥 Installation

### Option 1: Standalone Installer (Windows)

1. Navigate to the **[Releases](https://github.com/Abdelilah-dev/FocusFlow/releases/latest)** section.
2. Download `FocusFlow_Setup.exe`.
3. Run the installer and launch **FocusFlow** directly from your Desktop!

### Option 2: Arch Linux (AUR)

FocusFlow is packaged for Arch Linux (and AUR helpers like `yay` or `paru`) as `focusflow-git`.

```bash
yay -S focusflow-git
```

This installs FocusFlow to `/opt/focusflow`, adds a `focusflow` command, and registers it in your application launcher with its own icon — no manual Python setup required.

> By default, blocking a site still asks for your password each time it needs elevated access (writing to `/etc/hosts`, updating firewall rules, flushing DNS). See **[Running Without Repeated `sudo` Prompts](#-running-without-repeated-sudo-prompts-linux)** below to make this seamless.

---

## 🚀 Running from Source (Windows & Linux)

### Prerequisites

- **Python 3.10+**
- On Linux, ensure Qt multimedia plugins are installed (e.g., `qt6-multimedia-plugins` or `gstreamer`).

### Setup & Launch

1. **Clone the repository:**

   ```bash
   git clone https://github.com/Abdelilah-dev/FocusFlow.git
   cd FocusFlow
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application:**

   - **On Linux** *(see below to avoid running as root)*:

     ```bash
     python3 main.py
     ```

   - **On Windows** *(run CMD/PowerShell as Administrator)*:

     ```
     python main.py
     ```

---

## 🔓 Running Without Repeated `sudo` Prompts (Linux)

FocusFlow's site blocker needs elevated access for three things: editing `/etc/hosts`, managing `iptables`/`ip6tables` rules (to block DNS-over-HTTPS resolvers), and restarting the system DNS resolver. Instead of running the whole app as root, you can grant your user just enough permission for those specific actions — the app then runs entirely as your normal user.

1. **Allow your user to edit `/etc/hosts` directly:**

   ```bash
   sudo setfacl -m u:$USER:rw /etc/hosts
   ```

2. **Allow passwordless access to only the commands the blocker needs.** Create a dedicated sudoers file:

   ```bash
   sudo visudo -f /etc/sudoers.d/focusflow
   ```

   Add this single line (replace `yourusername` with your actual username, e.g. from `whoami`):

   ```
   yourusername ALL=(root) NOPASSWD: /usr/bin/iptables, /usr/bin/ip6tables, /usr/bin/iptables-save, /usr/bin/ip6tables-save, /usr/bin/systemctl restart systemd-resolved, /usr/bin/systemctl restart nscd, /usr/bin/resolvectl flush-caches
   ```

   Save and verify it's valid:

   ```bash
   sudo visudo -c
   ```

3. **Allow your user to write the saved `iptables` rules file:**

   ```bash
   sudo mkdir -p /etc/iptables
   sudo setfacl -m u:$USER:rwx /etc/iptables
   ```

That's it — launch `focusflow` normally (no `sudo`), and the site blocker will work without any password prompts.

> ⚠️ This grants your user passwordless root access to `iptables`, `ip6tables`, and specific `systemctl`/`resolvectl` commands only — not full root. Review the sudoers line before applying it if you're on a shared or security-sensitive machine.

---

## 🛡️ What FocusFlow Modifies (Transparency)

Because the site blocker works at the system level, it's worth knowing exactly what it touches before you run it:

| Component | What happens |
|---|---|
| `/etc/hosts` (or Windows equivalent) | Blocked domains (and common subdomains) are appended, tagged with `# FocusFlow` so they can be cleanly removed. A one-time backup is saved as `hosts.focusflow_backup`. |
| Browser preferences | Secure DNS / DNS-over-HTTPS is switched off in Chrome, Edge, Brave, Opera, and Firefox profiles it finds on your system. |
| Firewall (Linux) | `iptables`/`ip6tables` rules are added to drop outbound traffic on port 853 (DNS-over-TLS) and to a list of known public DoH resolver IPs. |
| DNS cache | `systemd-resolved`/`nscd` are restarted and caches flushed each time blocking starts. |

All of this is reversed automatically when a focus session ends or is stopped (`unblock_sites()`), except the browser DNS-over-HTTPS toggle and firewall rules, which stay off/in place until you re-enable them yourself.

---

## ⚠️ Known Limitations

- **Chromium-based browsers cache DNS internally.** Even after `/etc/hosts` is updated, Chrome/Brave/Edge may keep resolving a blocked site from their own internal DNS cache for a minute or two. On Linux, the Arch package works around this for **Brave** specifically by restarting it (`--restore-last-session`) when blocking starts. For other Chromium browsers, manually clear it at `<browser>://net-internals/#dns` if you need it instant.
- **Firewall-based DoH blocking is Linux/Windows only** and requires either the `sudo`/NOPASSWD setup above or running as root.
- **`iptables` rules persist after the app closes** until you flush them yourself (see [Uninstalling](#️-uninstalling)) — this is intentional so a session can't be un-blocked by just quitting the app, but it's good to know.

---

## 🗑️ Uninstalling

**Remove the package (Arch/AUR):**

```bash
sudo pacman -Rns focusflow-git
```

**Restore your original `/etc/hosts`** (if a backup exists):

```bash
sudo cp /etc/hosts.focusflow_backup /etc/hosts
```

**Remove the passwordless sudo rule (if you set it up):**

```bash
sudo rm /etc/sudoers.d/focusflow
```

**Clear the firewall rules added for DoH blocking:**

```bash
sudo iptables -F OUTPUT
sudo ip6tables -F OUTPUT
sudo rm -f /etc/iptables/rules.v4 /etc/iptables/rules.v6
```

> ⚠️ `iptables -F OUTPUT` clears **all** OUTPUT rules, not just FocusFlow's — only run this if you don't have other custom OUTPUT rules you want to keep.

---

## 📜 License

Distributed under the **MIT License**. See [`LICENSE`](https://github.com/Abdelilah-dev/FocusFlow/blob/main/LICENSE) for more details.

---

Crafted with ❤️ by **Abdelilah** for uninterrupted deep work.
*If FocusFlow helps your productivity, consider giving it a ⭐ on GitHub!*
