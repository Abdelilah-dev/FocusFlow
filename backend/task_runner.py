import threading
import time as time_module

from backend.name import Name
from backend.timer import Time, TaskState
from backend.priority import Priority
from backend.blocker import Blocker
from backend.notifications import Notification


class TaskRunner:
    def __init__(self, name_instance: Name, time_instance: Time,
                 priority_instance: Priority, sites: list, sound_manager=None):
        self.name_instance = name_instance
        self.time_instance = time_instance
        self.priority_instance = priority_instance
        self.sites = sites
        self.sound_manager = sound_manager

        self.blocker = Blocker()
        self.notifier = Notification(name_instance, time_instance, priority_instance, sound_manager)

        self._stopped = False
        self._threads = []
        self._finished = False
        self._break_notify_mark = self.time_instance.break_time_spent // 300

    def start(self):
        for site in self.sites:
            self.blocker.sites_instance.add_site(site)

        notif_thread = threading.Thread(target=self.notifier.manage_notif, daemon=True)
        notif_thread.start()
        self._threads.append(notif_thread)

        watcher_thread = threading.Thread(target=self._watch_task, daemon=True)
        watcher_thread.start()
        self._threads.append(watcher_thread)

    def _watch_task(self):
        while not self._stopped and self.time_instance.state == TaskState.WAITING:
            self.time_instance.update_status()
            if self.time_instance.state != TaskState.WAITING:
                break
            time_module.sleep(1)

        if self._stopped:
            return

        blocked_ok = self.blocker.block_sites()
        if not blocked_ok:
            self.notifier.send_alert("Couldn't block sites — run FocusFlow as admin.")

        while not self._stopped and self.time_instance.state in (TaskState.IN_PROGRESS, TaskState.BREAK):
            if self.time_instance.state == TaskState.IN_PROGRESS:
                self.time_instance.tick_focus()
                self._break_notify_mark = 0
            elif self.time_instance.state == TaskState.BREAK:
                self.time_instance.tick_break()
                mark = self.time_instance.break_time_spent // 300
                if mark > self._break_notify_mark:
                    self._break_notify_mark = mark
                    self.notifier.send_alert(f"You've wasted {mark * 5} minutes on break.")
            time_module.sleep(1)

        self.blocker.unblock_sites()

        if not self._stopped and self.time_instance.state == TaskState.PENDING_VALIDATION:
            print(f"[TaskRunner] Task finished, sending notification...")
            self.notifier.send_alert(f"{self.name_instance.name} finished. Take a break!")
            print(f"[TaskRunner] Notification sent.")

        self._finished = True

    def stop(self):
        self._stopped = True
        self.notifier.stop()
        self.time_instance.cancel_or_refuse_task()
        self.blocker.unblock_sites()

    def is_finished(self) -> bool:
        return self._finished
