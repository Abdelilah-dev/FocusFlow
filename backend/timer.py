from datetime import datetime, timedelta
from enum import Enum, auto


class TaskState(Enum):
    WAITING = auto()
    IN_PROGRESS = auto()
    BREAK = auto()
    PENDING_VALIDATION = auto()
    COMPLETED = auto()
    REFUSED = auto()


class Time:
    def __init__(
        self,
        start_hour: int,
        start_minute: int,
        start_second: int = 0,
        duration_hours: int = 0,
        duration_minutes: int = 0,
        duration_seconds: int = 0,
    ):
        now = datetime.now()
        sh = max(0, min(23, start_hour))
        sm = max(0, min(59, start_minute))
        ss = max(0, min(59, start_second))

        self._start_datetime = now.replace(hour=sh, minute=sm, second=ss, microsecond=0)

        if self._start_datetime < now.replace(second=0, microsecond=0):
            self._start_datetime += timedelta(days=1)

        dh = max(0, duration_hours)
        dm = max(0, min(59, duration_minutes))
        ds = max(0, min(59, duration_seconds))

        self._duration_total_seconds = (dh * 3600) + (dm * 60) + ds
        if self._duration_total_seconds == 0:
            self._duration_total_seconds = 60

        # Accumulated time tracking across multiple sessions
        self._focus_time_spent = 0      # Total seconds accumulated in focus
        self._break_time_spent = 0      # Total seconds accumulated in break
        self._mode_start_time = None    # When current mode started

        self._state = TaskState.WAITING


    @property
    def start_datetime(self) -> datetime:
        return self._start_datetime

    @property
    def start_hour(self) -> int:
        return self._start_datetime.hour

    @start_hour.setter
    def start_hour(self, hour: int):
        h = max(0, min(23, hour))
        now = datetime.now()
        self._start_datetime = self._start_datetime.replace(hour=h)
        if self._start_datetime < now.replace(second=0, microsecond=0):
            self._start_datetime += timedelta(days=1)

    @property
    def start_minute(self) -> int:
        return self._start_datetime.minute

    @start_minute.setter
    def start_minute(self, minute: int):
        m = max(0, min(59, minute))
        now = datetime.now()
        self._start_datetime = self._start_datetime.replace(minute=m)
        if self._start_datetime < now.replace(second=0, microsecond=0):
            self._start_datetime += timedelta(days=1)

    @property
    def start_second(self) -> int:
        return self._start_datetime.second

    @start_second.setter
    def start_second(self, second: int):
        s = max(0, min(59, second))
        now = datetime.now()
        self._start_datetime = self._start_datetime.replace(second=s)
        if self._start_datetime < now.replace(microsecond=0):
            self._start_datetime += timedelta(days=1)

    @property
    def duration_total_seconds(self) -> int:
        return self._duration_total_seconds

    @property
    def duration_hours(self) -> int:
        return self._duration_total_seconds // 3600

    @duration_hours.setter
    def duration_hours(self, hours: int):
        dh = max(0, hours)
        current_minutes = self.duration_minutes
        current_seconds = self.duration_seconds
        self._duration_total_seconds = (dh * 3600) + (current_minutes * 60) + current_seconds
        if self._duration_total_seconds == 0:
            self._duration_total_seconds = 60

    @property
    def duration_minutes(self) -> int:
        return (self._duration_total_seconds % 3600) // 60

    @duration_minutes.setter
    def duration_minutes(self, minutes: int):
        dm = max(0, min(59, minutes))
        current_hours = self.duration_hours
        current_seconds = self.duration_seconds
        self._duration_total_seconds = (current_hours * 3600) + (dm * 60) + current_seconds
        if self._duration_total_seconds == 0:
            self._duration_total_seconds = 60

    @property
    def duration_seconds(self) -> int:
        return self._duration_total_seconds % 60

    @duration_seconds.setter
    def duration_seconds(self, seconds: int):
        ds = max(0, min(59, seconds))
        current_hours = self.duration_hours
        current_minutes = self.duration_minutes
        self._duration_total_seconds = (current_hours * 3600) + (current_minutes * 60) + ds
        if self._duration_total_seconds == 0:
            self._duration_total_seconds = 60

    @property
    def state(self) -> TaskState:
        return self._state

    @state.setter
    def state(self, value: TaskState):
        if not isinstance(value, TaskState):
            raise TypeError(f"state must be TaskState, got {type(value)}")
        self._state = value

    # ── Time tracking (accumulated + current session) ──
    @property
    def focus_time_spent(self) -> int:
        """Total seconds spent in focus (accumulated + current session)."""
        total = self._focus_time_spent
        if self._state == TaskState.IN_PROGRESS and self._mode_start_time:
            total += int((datetime.now() - self._mode_start_time).total_seconds())
        return total

    @property
    def break_time_spent(self) -> int:
        """Total seconds spent in break (accumulated + current session)."""
        total = self._break_time_spent
        if self._state == TaskState.BREAK and self._mode_start_time:
            total += int((datetime.now() - self._mode_start_time).total_seconds())
        return total

    # Backward-compatible aliases
    @property
    def elapsed_seconds(self) -> int:
        return self.focus_time_spent

    @property
    def break_elapsed_seconds(self) -> int:
        return self.break_time_spent

    # ── Display values ──
    @property
    def remaining_seconds(self) -> int:
        """Countdown: how many seconds left in focus."""
        return max(0, self._duration_total_seconds - self.focus_time_spent)

    @property
    def formatted_remaining(self) -> str:
        rem = self.remaining_seconds
        h = rem // 3600
        m = (rem % 3600) // 60
        s = rem % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    @property
    def formatted_break_time(self) -> str:
        """Countup: how many seconds spent in break."""
        b_sec = self.break_time_spent
        h = b_sec // 3600
        m = (b_sec % 3600) // 60
        s = b_sec % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    # ── State transitions ──
    def update_status(self) -> str:
        if self._state == TaskState.WAITING and datetime.now() >= self._start_datetime:
            self._state = TaskState.IN_PROGRESS
            self._mode_start_time = datetime.now()
            return "STARTED"
        return self._state.name

    def start_now(self) -> str:
        """Force start the task immediately from WAITING state."""
        if self._state == TaskState.WAITING:
            self._state = TaskState.IN_PROGRESS
            self._mode_start_time = datetime.now()
            return "STARTED"
        return self._state.name

    def tick_focus(self):
        """Check if focus countdown reached zero. Stop at PENDING_VALIDATION."""
        if self._state == TaskState.IN_PROGRESS:
            if self.remaining_seconds <= 0:
                # Finalize current focus session
                if self._mode_start_time:
                    session = int((datetime.now() - self._mode_start_time).total_seconds())
                    self._focus_time_spent += session
                    self._mode_start_time = None
                self._state = TaskState.PENDING_VALIDATION
                # Stay in PENDING_VALIDATION until user clicks done/refuse

    def tick_break(self):
        """Break is count-up; nothing to check here (computed on demand)."""
        pass

    def go_to_break(self):
        """Switch from IN_PROGRESS to BREAK. Finalize focus time."""
        if self._state == TaskState.IN_PROGRESS:
            if self._mode_start_time:
                session = int((datetime.now() - self._mode_start_time).total_seconds())
                self._focus_time_spent += session
            self._state = TaskState.BREAK
            self._mode_start_time = datetime.now()

    def resume_focus(self):
        """Switch from BREAK back to IN_PROGRESS. Finalize break time."""
        if self._state == TaskState.BREAK:
            if self._mode_start_time:
                session = int((datetime.now() - self._mode_start_time).total_seconds())
                self._break_time_spent += session
            self._state = TaskState.IN_PROGRESS
            self._mode_start_time = datetime.now()

    def toggle_break(self) -> str:
        """Toggle between IN_PROGRESS and BREAK states."""
        if self._state == TaskState.IN_PROGRESS:
            self.go_to_break()
            return "BREAK"
        elif self._state == TaskState.BREAK:
            self.resume_focus()
            return "RESUMED"
        return self._state.name

    def cancel_or_refuse_task(self):
        if self._state in (TaskState.IN_PROGRESS, TaskState.PENDING_VALIDATION, TaskState.BREAK):
            # Finalize whichever mode we are in
            if self._state == TaskState.IN_PROGRESS and self._mode_start_time:
                session = int((datetime.now() - self._mode_start_time).total_seconds())
                self._focus_time_spent += session
            elif self._state == TaskState.BREAK and self._mode_start_time:
                session = int((datetime.now() - self._mode_start_time).total_seconds())
                self._break_time_spent += session
            self._mode_start_time = None
            self._state = TaskState.REFUSED

    def mark_completed(self):
        """Mark task as completed from PENDING_VALIDATION."""
        if self._state == TaskState.PENDING_VALIDATION:
            self._state = TaskState.COMPLETED

    def __repr__(self) -> str:
        return (
            f"Time(start={self._start_datetime.strftime('%H:%M:%S')}, "
            f"duration={self.formatted_remaining}, state={self._state.name}, "
            f"focus_spent={self.focus_time_spent}s, break_spent={self.break_time_spent}s)"
        )