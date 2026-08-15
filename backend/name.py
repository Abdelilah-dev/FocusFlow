import sys
import threading
import json
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from paths import app_data_path


class Name:
    MAX_LENGTH = 30
    _lock = threading.Lock()

    def __init__(self, name: str = ""):
        self._name = ""
        self.name = name

    @staticmethod
    def _get_next_task_number():
        used_numbers = set()
        
        try:
            tasks_path = app_data_path("tasks.json")
            if os.path.exists(tasks_path):
                with open(tasks_path, "r", encoding="utf-8") as f:
                    tasks = json.load(f)
                for task in tasks:
                    task_name = task.get("name", "")
                    match = re.match(r"^Task\s+(\d+)$", task_name)
                    if match:
                        used_numbers.add(int(match.group(1)))
        except Exception:
            pass
        
        n = 1
        while n in used_numbers:
            n += 1
        return n

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        clean_name = str(value).strip()
        
        if not clean_name:
            with Name._lock:
                next_num = Name._get_next_task_number()
                clean_name = f"Task {next_num}"
        else:
            if len(clean_name) > self.MAX_LENGTH:
                clean_name = clean_name[:self.MAX_LENGTH - 3].rstrip() + "..."
            
            if clean_name:
                clean_name = clean_name[0].upper() + clean_name[1:]
            
        self._name = clean_name

    def __str__(self):
        return self._name

    def __repr__(self):
        return f"Name(name='{self._name}')"

    def __eq__(self, other):
        if isinstance(other, Name):
            return self._name == other._name
        return False

    def __hash__(self):
        return hash(self._name)
