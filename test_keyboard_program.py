import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import keyboard_program as program


class BaseProgramTests(unittest.TestCase):
    def test_cpu_thresholds_are_strict_and_cumulative(self):
        for percent, count in ((0, 0), (20, 0), (20.01, 1), (40, 1),
                               (40.01, 2), (60, 2), (60.01, 3),
                               (80, 3), (80.01, 4), (100, 4)):
            with self.subTest(percent=percent):
                frame = program.base_frame(percent, 100, 255)
                self.assertEqual([frame[key] for key in program.CPU_KEYS],
                                 [255] * count + [0] * (4 - count))
                self.assertTrue(all(frame[key] == 0 for key in program.DISK_KEYS))

    def test_disk_thresholds_inclusive_and_cumulative(self):
        for free, count in ((51, 0), (50, 1), (40.01, 1), (40, 2),
                            (30.01, 2), (30, 3), (20.01, 3), (20, 4), (10, 4)):
            frame = program.base_frame(0, free, 128, flash_on=False)
            self.assertEqual([frame[key] for key in program.DISK_KEYS],
                             [128] * count + [0] * (4 - count))
            self.assertTrue(all(frame[key] == 0 for key in program.CPU_KEYS))

    def test_critical_disk_flashes_without_changing_cpu(self):
        for free in (9.99, 0):
            for flash_on in (True, False):
                frame = program.base_frame(65, free, 255, flash_on=flash_on)
                self.assertEqual([frame[key] for key in program.DISK_KEYS],
                                 [255 if flash_on else 0] * 4)
                self.assertEqual([frame[key] for key in program.CPU_KEYS], [255, 255, 255, 0])

    def test_custom_disk_thresholds(self):
        frame = program.base_frame(0, 60, 255, (100, 80, 60, 40), 20)
        self.assertEqual([frame[key] for key in program.DISK_KEYS], [255, 255, 255, 0])

    def test_cpu_guest_not_double_counted_and_iowait_is_idle(self):
        counters = program.cpu_counters("cpu 100 20 30 400 50 6 7 8 90 10\ncpu0 1 2 3 4")
        self.assertEqual(counters, (621, 450))
        self.assertEqual(program.cpu_percent((100, 60), (200, 120)), 40)
        self.assertEqual(program.cpu_percent((100, 60), (100, 60)), 0)
        self.assertEqual(program.cpu_percent((100, 60), (90, 50)), 0)

    def test_disk_excludes_root_reserved_blocks(self):
        with patch.object(program.os, "statvfs", return_value=SimpleNamespace(f_bavail=15_000_000, f_frsize=1000)):
            self.assertEqual(program.free_gb("/example"), 15)

    def test_only_changed_keys_are_sent(self):
        lighting = program.Lighting()
        lighting.command = Mock()
        lighting.start()
        self.assertEqual(lighting.command.call_args_list[0].args, ("info",))
        self.assertEqual(lighting.command.call_args_list[1].args, ("clear",))
        lighting.command.reset_mock()
        frame = program.base_frame(41, 100, 255)
        lighting.render(frame)
        self.assertEqual([call.args for call in lighting.command.call_args_list],
                         [("set", 0, 2, 255), ("set", 0, 3, 255)])
        lighting.command.reset_mock()
        lighting.render(frame)
        lighting.command.assert_not_called()
        lighting.render(program.base_frame(21, 100, 255))
        lighting.command.assert_called_once_with("set", 0, 3, 0)
        lighting.stop()
        self.assertEqual(lighting.command.call_args.args, ("clear",))

    def test_failed_write_is_not_cached(self):
        lighting = program.Lighting()
        lighting.command = Mock(side_effect=RuntimeError("disconnected"))
        with self.assertRaises(RuntimeError):
            lighting.render({(0, 2): 255})
        self.assertNotIn((0, 2), lighting.previous)

    def test_refresh_reclaims_frame_after_keyboard_reboot(self):
        lighting = program.Lighting()
        lighting.previous = {(0, 2): 255}
        lighting.command = Mock(return_value="protocol=1 active=0 rows=6 cols=21")
        lighting.refresh()
        self.assertEqual([call.args for call in lighting.command.call_args_list],
                         [("info",), ("clear",)])
        lighting.command.reset_mock()
        lighting.render(program.base_frame(21, 100, 255))
        lighting.command.assert_called_once_with("set", 0, 2, 255)

    def test_refresh_does_not_clear_active_frame(self):
        lighting = program.Lighting()
        lighting.previous = {(0, 2): 255}
        lighting.command = Mock(return_value="protocol=1 active=1 rows=6 cols=21")
        lighting.refresh()
        lighting.command.assert_called_once_with("info")
        self.assertEqual(lighting.previous, {(0, 2): 255})

    def test_once_dry_run_never_uses_sudo(self):
        with patch.object(program, "read_cpu", side_effect=[(100, 40), (200, 100)]), \
             patch.object(program, "free_gb", return_value=75), \
             patch.object(program.time, "sleep"), \
             patch.object(program.subprocess, "run") as run:
            self.assertEqual(program.main(["base", "--dry-run", "--once"]), 0)
            run.assert_not_called()

    def test_flash_cadence_independent_of_cpu_sampling(self):
        clock = [0.0]
        sleeps = []

        def sleep(seconds):
            sleeps.append(seconds)
            if len(sleeps) == 4:
                raise KeyboardInterrupt
            clock[0] += seconds

        with patch.object(program, "read_cpu", side_effect=[(100, 40), (200, 100)]) as cpu, \
             patch.object(program, "free_gb", return_value=9), \
             patch.object(program.time, "monotonic", side_effect=lambda: clock[0]), \
             patch.object(program.time, "sleep", side_effect=sleep), \
             patch.object(program, "base_frame", wraps=program.base_frame) as render:
            self.assertEqual(program.main(["base", "--dry-run", "--interval", "2"]), 0)
            self.assertEqual(cpu.call_count, 2)
            self.assertEqual([call.args[-1] for call in render.call_args_list], [True, False, True])
            self.assertEqual(sleeps, [2, 0.5, 0.5, 0.5])

    def test_disk_polled_at_startup_and_every_twenty_seconds(self):
        clock = [0.0]
        polls = []

        def sleep(seconds):
            clock[0] += seconds
            if clock[0] > 41:
                raise KeyboardInterrupt

        def disk_read(path):
            polls.append(clock[0])
            return 9  # Flashing must not cause additional disk reads.

        with patch.object(program, "read_cpu", return_value=(100, 40)) as cpu, \
             patch.object(program, "free_gb", side_effect=disk_read), \
             patch.object(program.time, "monotonic", side_effect=lambda: clock[0]), \
             patch.object(program.time, "sleep", side_effect=sleep), \
             patch("builtins.print"):
            self.assertEqual(program.main(["base", "--dry-run"]), 0)
            self.assertEqual(polls, [0, 20, 40])
            self.assertEqual(cpu.call_count, 42)


if __name__ == "__main__":
    unittest.main()
