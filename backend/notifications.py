import time
import platform
import subprocess
import os
from datetime import datetime, timedelta
from paths import resource_path

from backend.name import Name
from backend.timer import Time, TaskState
from backend.priority import Priority


class Notification:
    ALERT_SCHEDULE = {
        "High": [30, 20, 10, 8, 6, 4, 2],
        "Medium": [10, 7, 5, 3],
        "Low": [10, 5],
    }

    def __init__(self, name_instance, time_instance, priority_instance, sound_manager=None):
        self.name_instance = name_instance
        self.time_instance = time_instance
        self.priority_instance = priority_instance
        self.sound_manager = sound_manager
        self._stop = False
        self._dbus_address = self._find_dbus_address()
        self._sudo_user = os.environ.get('SUDO_USER')
        self._sudo_uid = os.environ.get('SUDO_UID')

    def _find_dbus_address(self):
        env_dbus = os.environ.get('DBUS_SESSION_BUS_ADDRESS')
        if env_dbus:
            return env_dbus
        sudo_uid = os.environ.get('SUDO_UID')
        if sudo_uid:
            bus_path = f"/run/user/{sudo_uid}/bus"
            if os.path.exists(bus_path):
                return f"unix:path={bus_path}"
        try:
            result = subprocess.run(
                ["cat", "/proc/1/environ"],
                capture_output=True, text=True, check=False
            )
            for part in result.stdout.split("\x00"):
                if part.startswith("DBUS_SESSION_BUS_ADDRESS="):
                    return part.split("=", 1)[1]
        except Exception:
            pass
        return None

    def stop(self):
        self._stop = True

    def send_alert(self, message):
        title = f"FocusFlow — {self.name_instance.name}"
        print(f"[NOTIFICATION] {title}: {message}")

        if self.sound_manager:
            try:
                priority = str(self.priority_instance)
                sound_key = f"notif_{priority.lower()}"
                self.sound_manager.play_notification.emit(sound_key)
            except Exception as e:
                print(f"[Notification] Sound error: {e}")

        try:
            if platform.system() == "Linux":
                env = os.environ.copy()
                if self._dbus_address:
                    env["DBUS_SESSION_BUS_ADDRESS"] = self._dbus_address

                cmd = ["notify-send", "-a", "FocusFlow", "-t", "10000", title, message]

                if self._sudo_user and self._sudo_uid:
                    cmd = ["sudo", "-u", self._sudo_user, "-E"] + cmd
                    env["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path=/run/user/{self._sudo_uid}/bus"

                result = subprocess.run(
                    cmd,
                    check=False, capture_output=True, text=True, env=env
                )
                if result.returncode != 0:
                    print(f"[Notification] notify-send error: {result.stderr}")
                else:
                    print(f"[Notification] notify-send sent successfully")
            else:
                from plyer import notification
                notification.notify(
                    title=title,
                    message=message,
                    app_name="FocusFlow",
		    app_icon=resource_path("assets", "icons", "app.ico"),
                    timeout=10
                )
                print(f"[Notification] plyer sent successfully")
        except Exception as e:
            print(f"[Notification] Error: {e}")

    def _get_alert_minutes(self):
        priority_str = str(self.priority_instance)
        return self.ALERT_SCHEDULE.get(priority_str, [])

    def manage_notif(self):
        if self.time_instance.state != TaskState.WAITING:
            return

        start_dt = self.time_instance.start_datetime
        alert_minutes = self._get_alert_minutes()
        now = datetime.now()

        upcoming_alerts = []
        for minutes_left in alert_minutes:
            alert_time = start_dt - timedelta(minutes=minutes_left)
            if alert_time > now:
                upcoming_alerts.append((alert_time, minutes_left))

        upcoming_alerts.sort(key=lambda x: x[0])

        for alert_time, minutes_left in upcoming_alerts:
            if self._stop:
                break

            now = datetime.now()
            if alert_time > now:
                sleep_seconds = (alert_time - now).total_seconds()
                while sleep_seconds > 0 and not self._stop:
                    chunk = min(sleep_seconds, 1.0)
                    time.sleep(chunk)
                    sleep_seconds -= chunk

            if self._stop:
                break

            if self.time_instance.state == TaskState.WAITING:
                self.send_alert(f"{minutes_left} minutes left to start.")

        if not self._stop and self.time_instance.state == TaskState.IN_PROGRESS:
            self.send_alert("Task started! Stay focused.")