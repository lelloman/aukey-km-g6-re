#!/usr/bin/env python3
"""Unprivileged keyboard programs using the installed, restricted lighting helper."""
import argparse
import fcntl
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

HELPER = Path("/usr/local/sbin/km-g6-lighting")
# Physical slots confirmed in lighting-map.json, not USB keycodes.
CPU_KEYS = ((0, 2), (0, 3), (0, 4), (0, 5))  # F1–F4
DISK_KEYS = ((0, 6), (0, 7), (0, 8), (0, 9))  # F5–F8
RAM_KEYS = ((0, 10), (0, 11), (0, 12), (0, 13))  # F9–F12
ALL_KEYS = CPU_KEYS + DISK_KEYS + RAM_KEYS
RAM_LEVELS = (60, 75, 85, 95)
RAM_FLASH_ABOVE = 98
THRESHOLDS = (20, 40, 60, 80)
DISK_LEVELS = (50, 40, 30, 20)
FLASH_SECONDS = 0.5


def cpu_counters(text):
    fields = text.splitlines()[0].split()
    if fields[0] != "cpu" or len(fields) < 5:
        raise ValueError("Missing aggregate CPU counters in /proc/stat")
    counters = [int(value) for value in fields[1:9]]
    # user/nice already include guest/guest_nice: do not count those twice.
    idle = counters[3] + (counters[4] if len(counters) > 4 else 0)
    return sum(counters), idle


def read_cpu():
    return cpu_counters(Path("/proc/stat").read_text())


def cpu_percent(previous, current):
    total = current[0] - previous[0]
    idle = current[1] - previous[1]
    if total <= 0:
        return 0.0
    return min(100.0, max(0.0, 100.0 * (total - idle) / total))


def free_gb(path):
    stats = os.statvfs(path)
    # Space available to the ordinary user; exclude root-reserved blocks.
    return max(0.0, stats.f_bavail * stats.f_frsize / 1_000_000_000)


def ram_percent(text):
    values = {}
    for line in text.splitlines():
        fields = line.split()
        if fields and fields[0] in ("MemTotal:", "MemAvailable:"):
            if len(fields) != 3 or fields[2] != "kB":
                raise ValueError("Invalid memory counters in /proc/meminfo")
            values[fields[0]] = int(fields[1])
    total = values.get("MemTotal:", 0)
    available = values.get("MemAvailable:", -1)
    if total <= 0 or available < 0 or available > total:
        raise ValueError("Missing or invalid MemTotal/MemAvailable in /proc/meminfo")
    return 100.0 * (total - available) / total


def read_ram():
    return ram_percent(Path("/proc/meminfo").read_text())


def base_frame(cpu, disk_free, brightness, disk_levels=DISK_LEVELS,
               flash_below=10, flash_on=True, *, ram=0):
    frame = {key: brightness if cpu > threshold else 0
             for key, threshold in zip(CPU_KEYS, THRESHOLDS)}
    for key, threshold in zip(DISK_KEYS, disk_levels):
        lit = flash_on if disk_free < flash_below else disk_free <= threshold
        frame[key] = brightness if lit else 0
    for key, threshold in zip(RAM_KEYS, RAM_LEVELS):
        lit = flash_on if ram > RAM_FLASH_ABOVE else ram > threshold
        frame[key] = brightness if lit else 0
    return frame


class Lighting:
    def __init__(self):
        self.previous = {}

    def command(self, *args):
        result = subprocess.run(["sudo", "-n", "--", str(HELPER), *map(str, args)],
                                capture_output=True, text=True, timeout=5)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or "Lighting helper failed")
        return result.stdout

    def start(self):
        self.command("info")
        self.command("clear")
        self.previous = {key: 0 for key in ALL_KEYS}

    def render(self, frame):
        # Do not clear between samples: unchanged LEDs stay steady.
        for (row, col), value in frame.items():
            if self.previous.get((row, col)) != value:
                self.command("set", row, col, value)
                self.previous[row, col] = value

    def stop(self):
        self.command("clear")

    def refresh(self):
        # Detect unplugging even while no indicator values change. A replugged
        # keyboard may have returned to its onboard effect; reclaim the frame.
        status = self.command("info")
        if "active=0" in status.split():
            self.command("clear")
            self.previous = {key: 0 for key in ALL_KEYS}


def positive_interval(text):
    value = float(text)
    if not math.isfinite(value) or value < 0.25:
        raise argparse.ArgumentTypeError("interval must be finite and at least 0.25 seconds")
    return value


def brightness_value(text):
    value = int(text)
    if not 0 <= value <= 255:
        raise argparse.ArgumentTypeError("brightness must be 0–255")
    return value


def nonnegative_gb(text):
    value = float(text)
    if not math.isfinite(value) or value < 0:
        raise argparse.ArgumentTypeError("GB threshold must be finite and nonnegative")
    return value


def preview_disk_alarm(seconds=10, brightness=255):
    """Temporarily pause the user service and always attempt to restore it."""
    def service(*args):
        return subprocess.run(["systemctl", "--user", *args], capture_output=True,
                              text=True, timeout=15, check=True)

    restart = False
    lighting = None
    lock = None
    old_term = signal.getsignal(signal.SIGTERM)

    def interrupted(signum, frame):
        raise KeyboardInterrupt

    try:
        signal.signal(signal.SIGTERM, interrupted)
        state = service("show", "km-g6-base.service", "--property=ActiveState", "--value").stdout.strip()
        restart = state in ("active", "activating", "reloading")
        if restart:
            service("stop", "km-g6-base.service")
        cache = Path.home() / ".cache" / "km-g6-control"
        cache.mkdir(parents=True, exist_ok=True)
        lock = (cache / "program.lock").open("a")
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("Stop the manually running keyboard program before previewing") from None
        lighting = Lighting()
        lighting.start()
        print(f"Preview: F5–F8 flashing for {seconds:g} seconds. No disk space is consumed.", flush=True)
        start = time.monotonic()
        end = start + seconds
        while time.monotonic() < end:
            now = time.monotonic()
            phase = int((now - start) / FLASH_SECONDS)
            lighting.render(base_frame(0, 0, brightness, flash_on=phase % 2 == 0))
            wake = min(end, start + (phase + 1) * FLASH_SECONDS)
            time.sleep(max(0, wake - time.monotonic()))
        return 0
    except KeyboardInterrupt:
        return 0
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"Preview failed: {error}", file=sys.stderr)
        return 1
    finally:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        try:
            if lighting:
                lighting.stop()
        except (OSError, RuntimeError, subprocess.SubprocessError) as error:
            print(f"Could not clear preview: {error}", file=sys.stderr)
        finally:
            if lock:
                lock.close()
            if restart:
                try:
                    service("start", "km-g6-base.service")
                    print("Live monitoring restarted.", flush=True)
                except (OSError, subprocess.SubprocessError) as error:
                    print(f"Could not restart monitoring: {error}; run systemctl --user start km-g6-base", file=sys.stderr)
            signal.signal(signal.SIGTERM, old_term)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    programs = parser.add_subparsers(dest="program", required=True)
    preview = programs.add_parser("preview-disk-alarm", help="flash F5–F8 briefly, then restore the service")
    preview.add_argument("--seconds", type=positive_interval, default=10.0)
    preview.add_argument("--brightness", type=brightness_value, default=255)
    base = programs.add_parser("base", help="CPU F1–F4, disk warnings F5–F8, RAM F9–F12")
    base.add_argument("--disk-path", type=Path, default=Path("/"),
                      help="path on the filesystem to monitor (default: /)")
    base.add_argument("--disk-levels", type=nonnegative_gb, nargs=4, default=DISK_LEVELS,
                      metavar=("F5_GB", "F6_GB", "F7_GB", "F8_GB"),
                      help="descending free-space warning thresholds in GB (default: 50 40 30 20)")
    base.add_argument("--disk-flash-below", type=nonnegative_gb, default=10,
                      help="flash F5–F8 below this many free GB (default: 10)")
    base.add_argument("--interval", type=positive_interval, default=1.0)
    base.add_argument("--disk-interval", type=positive_interval, default=20.0,
                      help="seconds between disk checks (default: 20)")
    base.add_argument("--brightness", type=brightness_value, default=255)
    base.add_argument("--dry-run", action="store_true", help="print metrics without sudo or device access")
    base.add_argument("--once", action="store_true", help="sample once, then exit (clears LEDs on exit)")
    base.add_argument("--quiet", action="store_true", help="omit per-sample output (for services)")
    args = parser.parse_args(argv)
    if args.program == "preview-disk-alarm":
        if args.seconds > 30:
            parser.error("preview must be at most 30 seconds")
        return preview_disk_alarm(args.seconds, args.brightness)
    if any(a <= b for a, b in zip(args.disk_levels, args.disk_levels[1:])):
        parser.error("--disk-levels must be strictly descending")
    if args.disk_flash_below > args.disk_levels[-1]:
        parser.error("--disk-flash-below must not exceed the F8 threshold")
    lighting = None
    lock = None
    old_term = signal.getsignal(signal.SIGTERM)

    def interrupted(signum, frame):
        raise KeyboardInterrupt

    try:
        disk = free_gb(args.disk_path)  # Fail before changing any LEDs.
        ram = read_ram()
        disk_deadline = time.monotonic() + args.disk_interval
        if not args.dry_run:
            if not HELPER.is_file():
                raise RuntimeError("Install the lighting helper first: docs/LIGHTING-HELPER.md")
            cache = Path.home() / ".cache" / "km-g6-control"
            cache.mkdir(parents=True, exist_ok=True)
            lock = (cache / "program.lock").open("a")
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise RuntimeError("A keyboard program is already running for this user") from None
            lighting = Lighting()
        signal.signal(signal.SIGTERM, interrupted)
        if lighting:
            lighting.start()
        print(f"Base: CPU F1–F4 >20/40/60/80%; disk {args.disk_path} "
              f"F5–F8 ≤{list(args.disk_levels)} GB, flashing below {args.disk_flash_below:g} GB; "
              "RAM F9–F12 >60/75/85/95%, flashing above 98%.", flush=True)
        print("Ctrl-C stops and clears the backlight." if lighting else "Preview only: no device access.", flush=True)
        previous = read_cpu()
        deadline = time.monotonic() + args.interval
        time.sleep(args.interval)  # First CPU reading needs a real sampling window.
        cpu = 0.0
        first_sample = True
        while True:
            now = time.monotonic()
            sample_due = first_sample or now >= deadline
            if sample_due:
                first_sample = False
                current = read_cpu()
                cpu = cpu_percent(previous, current)
                previous = current
                ram = read_ram()
                deadline = now + args.interval
            disk_due = now >= disk_deadline
            if disk_due:
                disk = free_gb(args.disk_path)
                disk_deadline = now + args.disk_interval
                if lighting:
                    lighting.refresh()
            disk_flashing = disk < args.disk_flash_below
            ram_flashing = ram > RAM_FLASH_ABOVE
            flashing = disk_flashing or ram_flashing
            frame = base_frame(cpu, disk, args.brightness, args.disk_levels,
                               args.disk_flash_below, int(now / FLASH_SECONDS) % 2 == 0, ram=ram)
            if lighting:
                lighting.render(frame)
            lit = [f"F{i + 1}" for i, key in enumerate(ALL_KEYS) if frame[key]]
            if (sample_due or disk_due) and not args.quiet:
                print(f"CPU {cpu:5.1f}% | disk free {disk:6.2f} GB "
                      f"{'[FLASHING]' if disk_flashing else ''} | RAM {ram:5.1f}% "
                      f"{'[FLASHING]' if ram_flashing else ''} | lit: {', '.join(lit) or 'none'}", flush=True)
            if args.once and sample_due:
                break
            wake = min(deadline, disk_deadline)
            if flashing:
                wake = min(wake, (int(now / FLASH_SECONDS) + 1) * FLASH_SECONDS)
            time.sleep(max(0, wake - time.monotonic()))
        return 0
    except KeyboardInterrupt:
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"Keyboard program: {error}", file=sys.stderr)
        return 1
    finally:
        # Ignore a second termination signal while doing bounded cleanup.
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        if lighting:
            try:
                lighting.stop()
            except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
                print(f"Could not clear backlight: {error}", file=sys.stderr)
        if lock:
            lock.close()
        signal.signal(signal.SIGTERM, old_term)


if __name__ == "__main__":
    raise SystemExit(main())
