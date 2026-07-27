import os
from pathlib import Path
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl, QTimer, QObject, Signal, Slot, QSettings


class SmartState(QObject):
    settings_changed = Signal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = QSettings("FocusFlow", "Sound")
        self._cache = {}

    def get(self, key, default=None):
        if key in self._cache:
            return self._cache[key]
        val = self._settings.value(key, default)
        if val is not None and default is not None:
            try:
                val = type(default)(val)
            except (ValueError, TypeError):
                val = default
        self._cache[key] = val
        return val

    def set(self, key, value):
        self._cache[key] = value
        self._settings.setValue(key, value)
        self.settings_changed.emit(key, value)

    def sync(self):
        self._settings.sync()


class EffectsEngine(QObject):
    effect_played = Signal(str)
    effect_error = Signal(str)
    _MAX_CONCURRENT = 8

    def __init__(self, parent=None):
        super().__init__(parent)
        self._players = set()
        self._volume = 0.8
        self._enabled = True
        self._preload_cache = {}

    def set_enabled(self, enabled):
        self._enabled = enabled

    def set_volume(self, value):
        self._volume = max(0.0, min(1.0, value))

    def preload(self, name, file_path):
        if not os.path.exists(file_path):
            return
        self._preload_cache[name] = file_path

    @Slot(str)
    def play(self, name, fallback_path=None):
        if not self._enabled:
            return
        path = self._preload_cache.get(name, fallback_path)
        if not path or not os.path.exists(path):
            self.effect_error.emit(f"Effect missing: {name}")
            return
        if len(self._players) >= self._MAX_CONCURRENT:
            oldest = next(iter(self._players))
            self._cleanup_player(oldest)
        player = QMediaPlayer(self)
        audio_out = QAudioOutput(self)
        player.setAudioOutput(audio_out)
        audio_out.setVolume(self._volume)
        player.setSource(QUrl.fromLocalFile(path))
        player.mediaStatusChanged.connect(self._on_media_status)
        player.errorOccurred.connect(self._on_player_error)
        player._ff_tag = name
        self._players.add(player)
        player.play()

    def _on_media_status(self, status):
        player = self.sender()
        if status in (QMediaPlayer.MediaStatus.EndOfMedia, QMediaPlayer.MediaStatus.InvalidMedia):
            self._cleanup_player(player)

    def _on_player_error(self, error, error_string):
        player = self.sender()
        self._cleanup_player(player)

    def _cleanup_player(self, player):
        if player in self._players:
            self._players.discard(player)
            tag = getattr(player, "_ff_tag", "")
            if tag:
                self.effect_played.emit(tag)
            player.deleteLater()


class AmbienceEngine(QObject):
    ambience_changed = Signal(str)
    active_changed = Signal(str, bool)
    fade_started = Signal(str, int)
    fade_finished = Signal(str)
    volume_changed = Signal(float)
    error_occurred = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ambiences = {}
        self._active = None
        self._master_volume = 1.0
        self._fade_step = 0.08
        self._fade_timer = QTimer(self)
        self._fade_timer.timeout.connect(self._fade_tick)
        self._fade_interval = 40
        self._crossfade_ms = 3000

    def register(self, name, file_path):
        if not os.path.exists(file_path):
            for ext in [".ogg", ".wav", ".mp3"]:
                alt = Path(file_path).with_suffix(ext)
                if alt.exists():
                    file_path = str(alt)
                    break
        if not os.path.exists(file_path):
            self.error_occurred.emit(name, f"File not found: {file_path}")
            return

        a = self._create_track(file_path)
        b = self._create_track(file_path)

        self._ambiences[name] = {
            "a": a, "b": b,
            "current": "a",
            "vol_a": 0.0, "vol_b": 0.0,
            "target": 0.0,
            "file": file_path,
            "ready": True,
        }

    def _create_track(self, file_path):
        player = QMediaPlayer(self)
        audio = QAudioOutput(self)
        player.setAudioOutput(audio)
        audio.setVolume(0.0)
        player.setSource(QUrl.fromLocalFile(file_path))
        player.errorOccurred.connect(self._on_track_error)
        return {"player": player, "audio": audio}

    def _on_track_error(self, error, error_string):
        pass

    def is_ready(self, name):
        return self._ambiences.get(name, {}).get("ready", False)

    def is_active(self, name):
        return self._active == name

    def active_name(self):
        return self._active

    def set_master_volume(self, value):
        self._master_volume = max(0.0, min(1.0, value))
        for name in self._ambiences:
            self._apply_volume(name)
        self.volume_changed.emit(self._master_volume)

    def get_master_volume(self):
        return self._master_volume

    def set_fade_speed(self, step, interval_ms=40):
        self._fade_step = max(0.01, min(1.0, step))
        self._fade_interval = max(10, interval_ms)
        if self._fade_timer.isActive():
            self._fade_timer.stop()
            self._fade_timer.start(self._fade_interval)

    def set_crossfade_ms(self, ms):
        self._crossfade_ms = max(1000, min(8000, ms))

    @Slot(str)
    def play(self, name):
        if name not in self._ambiences:
            self.error_occurred.emit(name, "Not registered")
            return
        if self._active == name:
            return

        if self._active:
            amb = self._ambiences[self._active]
            amb["target"] = 0.0
            self.active_changed.emit(self._active, False)

        self._active = name
        amb = self._ambiences[name]
        amb["target"] = 1.0

        track = amb["current"]
        player = amb[track]["player"]
        if player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
            player.play()
            self._start_loop_monitor(name)

        self.active_changed.emit(name, True)
        self.ambience_changed.emit(name)
        if not self._fade_timer.isActive():
            self._fade_timer.start(self._fade_interval)

    @Slot()
    def stop(self):
        if not self._active:
            return
        amb = self._ambiences[self._active]
        amb["target"] = 0.0
        self.active_changed.emit(self._active, False)
        old = self._active
        self._active = None
        self.ambience_changed.emit("")
        if not self._fade_timer.isActive():
            self._fade_timer.start(self._fade_interval)

    def _start_loop_monitor(self, name):
        amb = self._ambiences[name]
        track = amb["current"]
        player = amb[track]["player"]
        duration = player.duration()
        if duration <= 0:
            QTimer.singleShot(500, lambda: self._start_loop_monitor(name))
            return

        monitor = QTimer(self)
        monitor.timeout.connect(lambda: self._check_loop(name))
        monitor.start(100)
        amb["monitor"] = monitor

    def _check_loop(self, name):
        if name != self._active:
            return
        amb = self._ambiences[name]
        track = amb["current"]
        player = amb[track]["player"]

        if player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
            return

        duration = player.duration()
        position = player.position()
        if duration <= 0 or position <= 0:
            return

        remaining = duration - position
        if remaining <= self._crossfade_ms and not amb.get("crossfading", False):
            amb["crossfading"] = True
            self._do_crossfade(name)

    def _do_crossfade(self, name):
        amb = self._ambiences[name]
        current = amb["current"]
        next_track = "b" if current == "a" else "a"

        current_player = amb[current]["player"]
        next_player = amb[next_track]["player"]
        next_audio = amb[next_track]["audio"]

        next_player.setPosition(0)
        next_audio.setVolume(0.0)
        next_player.play()

        steps = max(1, int(self._crossfade_ms / self._fade_interval))
        base_vol = amb["target"] * self._master_volume

        def step(i):
            if i > steps or name != self._active:
                if name != self._active:
                    next_player.stop()
                amb["crossfading"] = False
                return

            progress = i / steps
            out_vol = base_vol * (1.0 - progress)
            in_vol = base_vol * progress

            amb[current]["audio"].setVolume(min(out_vol, 1.0))
            amb[next_track]["audio"].setVolume(min(in_vol, 1.0))

            if i == steps:
                current_player.stop()
                amb["current"] = next_track
                amb["vol_a"] = in_vol if next_track == "a" else 0.0
                amb["vol_b"] = in_vol if next_track == "b" else 0.0
                amb["crossfading"] = False
            else:
                QTimer.singleShot(self._fade_interval, lambda: step(i + 1))

        step(0)

    def _fade_tick(self):
        moving = False
        for name in self._ambiences:
            amb = self._ambiences[name]
            if amb.get("crossfading", False):
                continue

            for track in ["a", "b"]:
                current = amb[f"vol_{track}"]
                target = amb["target"] if (amb["current"] == track and amb["target"] > 0) else 0.0

                if abs(current - target) < self._fade_step:
                    amb[f"vol_{track}"] = target
                else:
                    if current < target:
                        amb[f"vol_{track}"] = min(current + self._fade_step, target)
                    else:
                        amb[f"vol_{track}"] = max(current - self._fade_step, target)
                    moving = True

                self._apply_track_volume(name, track)

            if amb["target"] <= 0 and amb["vol_a"] <= 0 and amb["vol_b"] <= 0:
                for t in ["a", "b"]:
                    if amb[t]["player"].playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                        amb[t]["player"].stop()
                if "monitor" in amb:
                    amb["monitor"].stop()
                    amb["monitor"].deleteLater()
                    del amb["monitor"]

        if not moving:
            self._fade_timer.stop()

    def _apply_track_volume(self, name, track):
        amb = self._ambiences[name]
        vol = amb[f"vol_{track}"] * self._master_volume
        amb[track]["audio"].setVolume(min(vol, 1.0))

    def _apply_volume(self, name):
        self._apply_track_volume(name, "a")
        self._apply_track_volume(name, "b")

    def _on_error(self, name, error, error_string):
        if name in self._ambiences:
            self._ambiences[name]["ready"] = False
        self.error_occurred.emit(name, f"[{error}] {error_string}")
        if self._active == name:
            self._active = None
            self.active_changed.emit(name, False)


class SoundManager(QObject):
    ambience_changed = Signal(str)
    ambience_active = Signal(str, bool)
    ambience_volume = Signal(float)
    effect_played = Signal(str)
    effect_error = Signal(str)
    error_occurred = Signal(str, str)
    global_mute_changed = Signal(bool)
    global_volume_changed = Signal(float)
    state_loaded = Signal()
    play_notification = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = SmartState(self)
        self._ambience = AmbienceEngine(self)
        self._effects = EffectsEngine(self)
        self._muted = False
        self._saved_volume = 0.5
        self._ducking = False
        self._duck_target = 0.2
        self._duck_timer = QTimer(self)
        self._duck_timer.timeout.connect(self._duck_tick)
        self._duck_step = 0.05
        self._duck_original = 0.5
        self._duck_paused_effects = False

        self._ambience.ambience_changed.connect(self.ambience_changed)
        self._ambience.active_changed.connect(self.ambience_active)
        self._ambience.volume_changed.connect(self.ambience_volume)
        self._ambience.error_occurred.connect(self.error_occurred)
        self._effects.effect_played.connect(self.effect_played)
        self._effects.effect_error.connect(self.effect_error)
        self.play_notification.connect(self._on_play_notification)

        self._sfx_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "sfx")

        self._load_state()

    def _load_state(self):
        last = self._state.get("last_ambience", "")
        vol = self._state.get("master_volume", 0.5)
        fx = self._state.get("effects_enabled", True)
        self._ambience.set_master_volume(vol)
        self._effects.set_volume(vol)
        self._effects.set_enabled(fx)
        self._saved_volume = vol
        self.state_loaded.emit()

    def register_ambience(self, name, file_path):
        self._ambience.register(name, file_path)

    def preload_effect(self, name, file_path):
        self._effects.preload(name, file_path)

    def play_ambience(self, name):
        self._ambience.play(name)
        if name:
            self._state.set("last_ambience", name)

    def stop_ambience(self):
        self._ambience.stop()
        self._state.set("last_ambience", "")

    @Slot(str)
    def _on_play_notification(self, name):
        if name not in self._effects._preload_cache:
            for ext in [".ogg", ".wav", ".mp3"]:
                fallback = os.path.join(self._sfx_dir, name + ext)
                if os.path.exists(fallback):
                    self.play_effect(name, fallback)
                    return
        self.play_effect(name)

    def play_effect(self, name, fallback_path=None):
        self._effects.play(name, fallback_path)

    def set_master_volume(self, value):
        vol = max(0.0, min(1.0, value))
        if self._muted and vol > 0:
            self._muted = False
            self.global_mute_changed.emit(False)
        self._duck_original = vol
        self._ambience.set_master_volume(vol)
        self._effects.set_volume(vol)
        self._saved_volume = vol
        self._state.set("master_volume", vol)
        self.global_volume_changed.emit(vol)

    def get_master_volume(self):
        if self._muted:
            return 0.0
        return self._ambience.get_master_volume()

    def toggle_mute(self):
        if self._muted:
            self._muted = False
            self._ambience.set_master_volume(self._saved_volume)
            self._effects.set_volume(self._saved_volume)
            self.global_mute_changed.emit(False)
            self.global_volume_changed.emit(self._saved_volume)
        else:
            self._saved_volume = self._ambience.get_master_volume()
            self._muted = True
            self._ambience.set_master_volume(0.0)
            self._effects.set_volume(0.0)
            self.global_mute_changed.emit(True)
            self.global_volume_changed.emit(0.0)

    def is_muted(self):
        return self._muted

    def set_effects_enabled(self, enabled):
        self._effects.set_enabled(enabled)
        self._state.set("effects_enabled", enabled)

    def effects_enabled(self):
        return self._effects._enabled

    def set_fade_speed(self, step, interval_ms=40):
        self._ambience.set_fade_speed(step, interval_ms)

    def set_crossfade_duration(self, ms):
        self._ambience.set_crossfade_ms(ms)

    def start_ducking(self, target=0.2, duration_ms=200, pause_effects=False):
        if not self._ambience._active:
            return
        self._ducking = True
        self._duck_target = target
        self._duck_original = self._ambience.get_master_volume()
        self._duck_step = abs(self._duck_original - target) / max(1, duration_ms / 40)
        self._duck_paused_effects = pause_effects
        if pause_effects:
            self._effects.set_enabled(False)
        self._duck_timer.start(40)

    def stop_ducking(self, duration_ms=400):
        if not self._ducking:
            return
        self._duck_target = self._duck_original
        self._duck_step = abs(self._ambience.get_master_volume() - self._duck_original) / max(1, duration_ms / 40)
        self._duck_timer.start(40)

    def _duck_tick(self):
        current = self._ambience.get_master_volume()
        target = self._duck_target
        if abs(current - target) < self._duck_step:
            self._ambience.set_master_volume(target)
            self._duck_timer.stop()
            if target == self._duck_original:
                self._ducking = False
                if self._duck_paused_effects:
                    self._effects.set_enabled(self._state.get("effects_enabled", True))
                    self._duck_paused_effects = False
        else:
            if current < target:
                new_vol = min(current + self._duck_step, target)
            else:
                new_vol = max(current - self._duck_step, target)
            self._ambience.set_master_volume(new_vol)

    def active_ambience(self):
        return self._ambience.active_name()

    def is_ambience_ready(self, name):
        return self._ambience.is_ready(name)

    def save(self):
        self._state.sync()