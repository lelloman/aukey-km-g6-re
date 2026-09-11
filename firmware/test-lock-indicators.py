#!/usr/bin/env python3
"""Host-side checks of the actual lock-LED statements in the target patch."""
from pathlib import Path
import re
import subprocess
import tempfile

patch = Path(__file__).with_name("smk-aukey-km-g6.patch").read_text()


def added_source(suffix):
    for section in patch.split("diff --git ")[1:]:
        if section.splitlines()[0].endswith(suffix):
            return "\n".join(line[1:] for line in section.splitlines()
                             if line.startswith("+") and not line.startswith("+++"))
    raise AssertionError(suffix)


indicators = added_source("/layouts/default/indicators.c")
init = added_source("/user_init.c")
kbdef = added_source("/kbdef.h")
body = indicators.split("bool indicators_update_step(", 1)[1].split("{", 1)[1]
# Test the actual statements before the backlight-off early return.
updates = body.split("if (!host_lighting_is_active()", 1)[0]
setup = "\n".join(re.findall(r"^\s*GPIO_(?:HIGH|PULLUP_ON|OUTPUT)\(0, LED_LOCK_MASK\);", init, re.M))
assert len(setup.splitlines()) == 3
defines = "\n".join(line for line in kbdef.splitlines()
                    if line.startswith(("#define LED_NUM ", "#define LED_CAPS ",
                                        "#define LED_SCROLL ", "#define LED_LOCK_MASK ")))
source = r'''
#include <assert.h>
#include <stdint.h>
static uint8_t P0_2, P0_3, P0_4, latch, pullups, direction;
#define _P0_2 4
#define _P0_3 8
#define _P0_4 16
#define GPIO_HIGH(port, mask) (latch |= (mask))
#define GPIO_PULLUP_ON(port, mask) (pullups |= (mask))
#define GPIO_OUTPUT(port, mask) (direction |= (mask))
typedef struct { uint8_t led_state; } keyboard_state_t;
''' + defines + '\nstatic void update(keyboard_state_t *keyboard) {\n' + updates.replace('current_step;', '') + '\n}\nstatic void setup(void) {\n' + setup + r'''
}
int main(void) {
    for (unsigned state = 0; state < 256; ++state) {
        keyboard_state_t keyboard = { state };
        update(&keyboard);
        assert(P0_2 == !(state & 1));
        assert(P0_3 == !(state & 2));
        assert(P0_4 == !(state & 4));
        latch = pullups = direction = state;
        setup();
        assert(latch == (state | 0x1c));
        assert(pullups == (state | 0x1c));
        assert(direction == (state | 0x1c));
    }
}
'''
with tempfile.TemporaryDirectory(prefix="km-g6-lock-test-") as directory:
    binary = str(Path(directory) / "test")
    subprocess.run(["cc", "-std=c99", "-Wall", "-Wextra", "-Werror",
                    "-x", "c", "-", "-o", binary], input=source, text=True, check=True)
    subprocess.run([binary], check=True)
print("PASS: all 256 LED states; GPIO setup preserves unrelated pins; updates precede backlight-off return")
