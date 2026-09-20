#!/usr/bin/env python3
"""Compile and exercise the patched SMK matrix code; pass a patched SMK tree."""
from pathlib import Path
import subprocess
import sys
import tempfile

smk = Path(sys.argv[1])
matrix = (smk / 'src/smk/matrix.c').read_text()
layout = (smk / 'src/keyboards/aukey-km-g6/layouts/default/layout.c').read_text()
def without_includes(source):
    return '\n'.join(line for line in source.splitlines()
                     if not line.startswith('#include'))

# Keep the actual event-processing code, replacing only hardware/report IO.
source = r'''
#include <assert.h>
#include <stdint.h>
#include <stdbool.h>
#include "keycodes.h"
#define MATRIX_COLS 21
#define MATRIX_ROWS 6
static uint16_t consumer;
static bool keys[256];
static unsigned consumer_releases;
static void add_mods(uint8_t x) { (void)x; }
static void del_mods(uint8_t x) { (void)x; }
static void add_key(uint8_t x) { keys[x] = true; }
static void del_key(uint8_t x) { keys[x] = false; }
static void clear_keys(void) { for (int i=0; i<256; i++) keys[i]=false; }
static void send_keyboard_report(void) {}
static void host_system_send(uint16_t x) { (void)x; }
static uint16_t keycode_to_system(uint8_t x) { return x; }
static uint16_t keycode_to_consumer(uint8_t x) { return x; }
static void host_consumer_send(uint16_t x) { consumer=x; if (!x) consumer_releases++; }
static bool kb_process_record(uint16_t x, bool p) { (void)x; (void)p; return true; }
static bool layout_process_record(uint16_t x, bool p) { (void)x; (void)p; return true; }
'''
source += without_includes(layout)
source += without_includes(matrix.split('void matrix_scan_full(void)')[0])
source += r'''
static void fn(bool down) { process_key_state(5, 9, down); }
static void key(int col, bool down) { process_key_state(0, col, down); }
int main(void) {
    matrix_init();
    for (int col=11; col<=12; col++) {
        for (int fn_first=0; fn_first<2; fn_first++) {
            unsigned before = consumer_releases;
            fn(true); key(col, true);
            assert(consumer == (col==11 ? KC_VOLD : KC_VOLU));
            if (fn_first) { fn(false); key(col, false); }
            else { key(col, false); fn(false); }
            assert(consumer == 0);
            assert(consumer_releases == before+1);
            assert(!keys[KC_F10] && !keys[KC_F11]);
        }
        // A base-layer press must still release on the base layer after Fn.
        key(col, true); fn(true); key(col, false); fn(false);
        assert(!keys[KC_F10] && !keys[KC_F11]);
        // Releasing Fn must not clear unrelated held keys.
        process_key_state(3, 1, true);
        fn(true); key(col, true); fn(false);
        assert(keys[KC_A]);
        key(col, false); process_key_state(3, 1, false);
        assert(!keys[KC_A] && consumer == 0);
    }
}
'''
with tempfile.TemporaryDirectory(prefix='km-g6-fn-test-') as directory:
    binary = str(Path(directory) / 'test')
    subprocess.run(['cc', '-std=c99', '-Wall', '-Wextra', '-Werror',
                    '-Wno-unused-function', '-I', str(smk / 'src/smk'),
                    '-x', 'c', '-', '-o', binary], input=source, text=True, check=True)
    subprocess.run([binary], check=True)
print('PASS: both volume keys, both release orders, base-key release across Fn, unrelated held keys')
