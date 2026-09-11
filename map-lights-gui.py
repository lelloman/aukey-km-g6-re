#!/usr/bin/env python3
"""Interactive physical-key mapper for the AUKEY KM-G6 lighting matrix."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox


ROOT = pathlib.Path(__file__).resolve().parent
FRAME = pathlib.Path("/usr/local/sbin/km-g6-lighting")
UNUSED_MODE = "--unused" in sys.argv[1:]
OUTPUT = ROOT / ("lighting-map-unused.json" if UNUSED_MODE else "lighting-map.json")

# Firmware lighting slots. A dot is an unused slot and is not presented.
MATRIX = (
    ".,ESC,F1,F2,F3,F4,F5,F6,F7,F8,F9,F10,F11,F12,PRTSC,SCROLL,PAUSE,.,.,.,.",
    "GRAVE,1,2,3,4,5,6,7,8,9,0,MINUS,EQUAL,BACKSPACE,INSERT,HOME,PAGEUP,NUMLOCK,KP_SLASH,KP_STAR,KP_MINUS",
    "TAB,Q,W,E,R,T,Y,U,I,O,P,LBRACKET,RBRACKET,ENTER,DELETE,END,PAGEDOWN,KP_7,KP_8,KP_9,KP_PLUS",
    "CAPSLOCK,A,S,D,F,G,H,J,K,L,SEMICOLON,APOSTROPHE,ISO_HASH,ISO_BACKSLASH,.,.,.,KP_4,KP_5,KP_6,.",
    "LSHIFT,Z,X,C,V,B,N,M,COMMA,DOT,SLASH,INTL_BACKSLASH,RSHIFT,MENU,.,UP,.,KP_1,KP_2,KP_3,.",
    "LCTRL,LGUI,LALT,.,.,SPACE,.,.,RALT,FN,MENU,.,RCTRL,.,LEFT,DOWN,RIGHT,KP_0,.,KP_DOT,.",
)


def key(label: str, code: int | None, width: float = 1.0) -> tuple[str, int | None, float]:
    return label, code, width


# Standard Linux/X11 physical keycodes. Labels show the Italian ISO legends.
LAYOUT = (
    (
        key("Esc", 9), key("F1", 67), key("F2", 68), key("F3", 69),
        key("F4", 70), key("F5", 71), key("F6", 72), key("F7", 73),
        key("F8", 74), key("F9", 75), key("F10", 76), key("F11", 95),
        key("F12", 96), key("Stamp", 107), key("Bloc Scorr", 78), key("Pausa", 127),
    ),
    (
        key("\\\n|", 49), key("1\n!", 10), key('2\n"', 11), key("3\n£", 12),
        key("4\n$", 13), key("5\n%", 14), key("6\n&", 15), key("7\n/", 16),
        key("8\n(", 17), key("9\n)", 18), key("0\n=", 19), key("'\n?", 20),
        key("ì\n^", 21), key("Backspace", 22, 2),
        key("Ins", 118), key("Home", 110), key("Pag ↑", 112),
        key("Bloc Num", 77), key("/", 106), key("*", 63), key("-", 82),
    ),
    (
        key("Tab", 23, 1.5), key("Q", 24), key("W", 25), key("E", 26),
        key("R", 27), key("T", 28), key("Y", 29), key("U", 30), key("I", 31),
        key("O", 32), key("P", 33), key("è\né", 34), key("+\n*", 35),
        key("Invio", 36, 1.5), key("Canc", 119), key("Fine", 115), key("Pag ↓", 117),
        key("7\nHome", 79), key("8\n↑", 80), key("9\nPag ↑", 81), key("+", 86),
    ),
    (
        key("Bloc Maiusc", 66, 1.8), key("A", 38), key("S", 39), key("D", 40),
        key("F", 41), key("G", 42), key("H", 43), key("J", 44), key("K", 45),
        key("L", 46), key("ò\nç", 47), key("à\n°", 48), key("ù\n§", 51),
        key("4\n←", 83), key("5", 84), key("6\n→", 85),
    ),
    (
        key("Maiusc", 50, 1.25), key("<\n>", 94), key("Z", 52), key("X", 53),
        key("C", 54), key("V", 55), key("B", 56), key("N", 57), key("M", 58),
        key(",\n;", 59), key(".\n:", 60), key("-\n_", 61), key("Maiusc", 62, 2.2),
        key("↑", 111), key("1\nFine", 87), key("2\n↓", 88), key("3\nPag ↓", 89),
        key("Invio tast.", 104, 1.3),
    ),
    (
        key("Ctrl", 37, 1.3), key("Win", 133, 1.2), key("Alt", 64, 1.2),
        key("Spazio", 65, 5.5), key("Alt Gr", 108, 1.3), key("Fn", None, 1.1),
        key("Menu", 135, 1.1), key("Ctrl", 105, 1.3),
        key("←", 113), key("↓", 116), key("→", 114),
        key("0\nIns", 90, 2.0), key(".\nCanc", 91),
    ),
)

EXPECTED_KEYCODE = {
    "ESC": 9, "F1": 67, "F2": 68, "F3": 69, "F4": 70, "F5": 71,
    "F6": 72, "F7": 73, "F8": 74, "F9": 75, "F10": 76, "F11": 95,
    "F12": 96, "PRTSC": 107, "SCROLL": 78, "PAUSE": 127,
    "GRAVE": 49, "1": 10, "2": 11, "3": 12, "4": 13, "5": 14,
    "6": 15, "7": 16, "8": 17, "9": 18, "0": 19, "MINUS": 20,
    "EQUAL": 21, "BACKSPACE": 22, "INSERT": 118, "HOME": 110,
    "PAGEUP": 112, "NUMLOCK": 77, "KP_SLASH": 106, "KP_STAR": 63,
    "KP_MINUS": 82, "TAB": 23, "Q": 24, "W": 25, "E": 26, "R": 27,
    "T": 28, "Y": 29, "U": 30, "I": 31, "O": 32, "P": 33,
    "LBRACKET": 34, "RBRACKET": 35, "ENTER": 36, "DELETE": 119,
    "END": 115, "PAGEDOWN": 117, "KP_7": 79, "KP_8": 80, "KP_9": 81,
    "KP_PLUS": 86, "CAPSLOCK": 66, "A": 38, "S": 39, "D": 40,
    "F": 41, "G": 42, "H": 43, "J": 44, "K": 45, "L": 46,
    "SEMICOLON": 47, "APOSTROPHE": 48, "ISO_HASH": 51,
    "ISO_BACKSLASH": 94, "KP_4": 83, "KP_5": 84, "KP_6": 85,
    "LSHIFT": 50, "Z": 52, "X": 53, "C": 54, "V": 55, "B": 56,
    "N": 57, "M": 58, "COMMA": 59, "DOT": 60, "SLASH": 61,
    "INTL_BACKSLASH": 94, "RSHIFT": 62, "MENU": 135, "UP": 111,
    "KP_1": 87, "KP_2": 88, "KP_3": 89, "LCTRL": 37, "LGUI": 133,
    "LALT": 64, "SPACE": 65, "RALT": 108, "RCTRL": 105, "LEFT": 113,
    "DOWN": 116, "RIGHT": 114, "KP_0": 90, "KP_DOT": 91,
}


def slots() -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for row, line in enumerate(MATRIX):
        for col, label in enumerate(line.split(",")):
            if UNUSED_MODE and label == ".":
                result.append({"row": row, "col": col, "expected": "UNKNOWN"})
            elif not UNUSED_MODE and label != ".":
                result.append({"row": row, "col": col, "expected": label})
    return result


def find_device() -> str:
    for uevent in pathlib.Path("/sys/class/hidraw").glob("hidraw*/device/uevent"):
        text = uevent.read_text(errors="replace")
        if "HID_ID=0003:0000258A:0000002A" in text and "input1" in text:
            return f"/dev/{uevent.parents[1].name}"
    raise RuntimeError("AUKEY KM-G6 vendor HID interface not found")


class Mapper:
    def __init__(self, root: tk.Tk, device: str) -> None:
        self.root = root
        self.device = device
        self.items = slots()
        self.results: list[dict[str, object]] = []
        self.index = 0
        self.mapping = False
        self.busy = False
        self.buttons: dict[int, tk.Button] = {}
        self.button_labels: dict[int, str] = {}
        self.fn_button: tk.Button | None = None
        self.marked_button: tk.Button | None = None

        root.title("AUKEY KM-G6 — Italian layout LED mapper")
        root.configure(bg="#17191c")
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        root.geometry(f"{min(1500, screen_w - 80)}x{min(760, screen_h - 100)}")
        root.minsize(850, 480)
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.bind("<KeyPress>", self.key_pressed)

        initial_title = ("Probe currently unused lighting slots" if UNUSED_MODE
                         else "Verify the Italian keyboard layout")
        self.title = tk.Label(root, text=initial_title,
                              fg="white", bg="#17191c", font=("Sans", 18, "bold"))
        self.title.pack(padx=16, pady=(14, 4))
        self.help = tk.Label(
            root,
            text="Check that the key shapes and legends below match your keyboard.\n"
                 "During mapping, press the physical key whose LED is lit, or click it here.",
            fg="#c7cbd1", bg="#17191c", font=("Sans", 11),
        )
        self.help.pack(padx=16, pady=(0, 12))

        viewport = tk.Frame(root, bg="#101215")
        viewport.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        canvas = tk.Canvas(viewport, bg="#101215", highlightthickness=0)
        horizontal = tk.Scrollbar(viewport, orient="horizontal", command=canvas.xview)
        vertical = tk.Scrollbar(viewport, orient="vertical", command=canvas.yview)
        canvas.configure(xscrollcommand=horizontal.set, yscrollcommand=vertical.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        viewport.grid_rowconfigure(0, weight=1)
        viewport.grid_columnconfigure(0, weight=1)

        keyboard = tk.Frame(canvas, bg="#101215", padx=8, pady=8)
        keyboard_window = canvas.create_window((0, 0), window=keyboard, anchor="nw")
        keyboard.bind(
            "<Configure>",
            lambda _event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.bind(
            "<Configure>",
            lambda event: canvas.itemconfigure(
                keyboard_window,
                width=max(event.width, keyboard.winfo_reqwidth()),
            ),
        )
        for r, row in enumerate(LAYOUT):
            x = 0
            for label, code, width in row:
                button = tk.Button(
                    keyboard, text=label, width=max(4, round(width * 5)), height=2,
                    bg="#30343a", fg="white", activebackground="#54606d",
                    activeforeground="white", relief="raised",
                    command=lambda c=code, l=label: self.choose(c, l),
                )
                button.grid(row=r, column=x, columnspan=max(1, round(width * 2)),
                            padx=2, pady=2, sticky="nsew")
                if code is not None:
                    self.buttons[code] = button
                    self.button_labels[code] = label
                elif label == "Fn":
                    self.fn_button = button
                x += max(1, round(width * 2))

        controls = tk.Frame(root, bg="#17191c")
        controls.pack(fill="x", padx=14, pady=(0, 12), before=viewport)
        self.start_button = tk.Button(
            controls,
            text=("START UNUSED-SLOT PROBE" if UNUSED_MODE
                  else "START MAPPING — layout matches"),
            command=self.start,
            bg="#2d7d46", fg="white", font=("Sans", 12, "bold"), padx=12, pady=8,
        )
        self.start_button.pack(side="left")
        self.none_button = tk.Button(
            controls, text="None lit", command=self.none_lit, state="disabled",
            bg="#8c3e3e", fg="white", font=("Sans", 12, "bold"), padx=12, pady=8,
        )
        self.none_button.pack(side="left", padx=10)
        self.undo_button = tk.Button(
            controls, text="Back", command=self.back, state="disabled", padx=10, pady=8,
        )
        self.undo_button.pack(side="left")
        self.progress = tk.Label(controls, text=f"{self.index} / {len(self.items)}", fg="white",
                                 bg="#17191c", font=("Sans", 12))
        self.progress.pack(side="right")

    def command(self, *args: str) -> None:
        completed = subprocess.run(
            ["sudo", "-n", str(FRAME), *args],
            text=True, capture_output=True,
        )
        if completed.returncode:
            raise RuntimeError(completed.stderr.strip() or "lighting command failed")

    def start(self) -> None:
        if not messagebox.askokcancel(
            "Start mapping",
            "The GUI will clear the keyboard and light one firmware slot at a time.\n\n"
            "Keep this window focused. Press the key that physically lights, or click None lit.",
        ):
            return
        self.results = []
        self.index = 0
        OUTPUT.unlink(missing_ok=True)
        self.mapping = True
        self.start_button.configure(state="disabled")
        self.none_button.configure(state="normal")
        self.undo_button.configure(state="normal")
        self.command("clear")
        self.show_current()

    def show_current(self) -> None:
        if self.index >= len(self.items):
            self.finish()
            return
        item = self.items[self.index]
        self.command("clear")
        self.command("set", str(item["row"]), str(item["col"]), "255")
        if item["expected"] == "UNKNOWN":
            self.mark_expected("")
            self.title.configure(text="Unassigned slot — identify any lit key")
        else:
            self.mark_expected(str(item["expected"]))
            self.title.configure(text="Find the key marked ●")
        self.help.configure(
            text=f'Firmware slot row {item["row"]}, column {item["col"]}\n'
                 "Press or click the key that is ACTUALLY lit. Use “None lit” if no LED is on."
        )
        self.progress.configure(text=f"{self.index + 1} / {len(self.items)}")
        self.root.focus_force()

    def mark_expected(self, expected: str) -> None:
        if self.marked_button is not None:
            old_code = next((code for code, button in self.buttons.items()
                             if button is self.marked_button), None)
            old_text = self.button_labels.get(old_code, "Fn")
            self.marked_button.configure(text=old_text, bg="#30343a", fg="white",
                                         relief="raised")
        if expected == "FN":
            button = self.fn_button
            original = "Fn"
        else:
            code = EXPECTED_KEYCODE.get(expected)
            button = self.buttons.get(code) if code is not None else None
            original = self.button_labels.get(code, expected) if code is not None else expected
        self.marked_button = button
        if button is not None:
            button.configure(text=f"● {original}", bg="#ffd34d", fg="#111111",
                             relief="sunken")

    def key_pressed(self, event: tk.Event) -> str:
        if not self.mapping or self.busy:
            return "break"
        code = int(event.keycode)
        button = self.buttons.get(code)
        label = button.cget("text") if button else event.keysym
        self.record({"kind": "key", "label": label.replace("\n", " / "),
                     "x_keycode": code, "keysym": event.keysym})
        return "break"

    def choose(self, code: int | None, label: str) -> None:
        if not self.mapping or self.busy:
            return
        self.record({"kind": "layout_click", "label": label.replace("\n", " / "),
                     "x_keycode": code})

    def none_lit(self) -> None:
        if self.mapping and not self.busy:
            self.record({"kind": "none"})

    def record(self, observed: dict[str, object]) -> None:
        self.busy = True
        entry = dict(self.items[self.index])
        entry["observed"] = observed
        if self.index < len(self.results):
            self.results[self.index] = entry
        else:
            self.results.append(entry)
        self.index += 1
        self.save(False)
        self.root.after(180, self.advance)

    def advance(self) -> None:
        self.busy = False
        try:
            self.show_current()
        except Exception as error:
            messagebox.showerror("Lighting error", str(error))
            self.close()

    def back(self) -> None:
        if not self.mapping or self.busy or self.index == 0:
            return
        self.index -= 1
        self.results = self.results[:self.index]
        self.save(False)
        self.show_current()

    def save(self, complete: bool) -> None:
        data = {"format": 1, "complete": complete, "device": self.device,
                "mapped": len(self.results), "total": len(self.items),
                "slots": self.results}
        temporary = OUTPUT.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        temporary.replace(OUTPUT)

    def finish(self) -> None:
        self.mapping = False
        self.command("clear")
        self.save(True)
        self.mark_expected("")
        self.title.configure(text="Mapping complete")
        self.help.configure(text=f"Saved {len(self.results)} observations to {OUTPUT.name}")
        self.none_button.configure(state="disabled")
        messagebox.showinfo("Complete", f"Mapping saved to:\n{OUTPUT}")

    def close(self) -> None:
        try:
            if self.mapping:
                OUTPUT.unlink(missing_ok=True)
            self.command("clear")
        except Exception:
            pass
        self.root.destroy()


def main() -> int:
    if not FRAME.is_file():
        print("Install the lighting helper first; see docs/LIGHTING-HELPER.md", file=sys.stderr)
        return 1
    try:
        device = find_device()
        subprocess.run(["sudo", str(FRAME), "info"], check=True)
    except (RuntimeError, subprocess.CalledProcessError) as error:
        print(error, file=sys.stderr)
        return 1

    root = tk.Tk()
    Mapper(root, device)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
