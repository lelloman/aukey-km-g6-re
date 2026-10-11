#!/usr/bin/env python3
"""Compile the patched SMK matrix scan and check that switch bounce is filtered; pass a patched SMK tree."""
from pathlib import Path
import subprocess
import sys
import tempfile

smk = Path(sys.argv[1])
matrix = (smk / 'src/smk/matrix.c').read_text()
def without_includes(source):
    return '\n'.join(line for line in source.splitlines()
                     if not line.startswith('#include'))

# Keep the actual scan and event-processing code, replacing only hardware/report IO.
source = r'''
#include <assert.h>
#include <stdint.h>
#include <stdbool.h>
#include "keycodes.h"
#define MATRIX_COLS 21
#define MATRIX_ROWS 6
static const uint16_t keymaps[1][MATRIX_ROWS][MATRIX_COLS] = { [0][3][1] = KC_A };
static uint8_t rows_low[MATRIX_COLS];
static uint8_t selected;
static unsigned presses, releases;
static void indicators_pwm_disable(void) {}
static void indicators_pwm_enable(void) {}
static void user_matrix_sinks_off(void) {}
static void user_matrix_scan_pre(void) {}
static void user_matrix_scan_post(void) {}
static void user_matrix_cols_deselect_all(void) {}
static void user_matrix_col_select(uint8_t col) { selected = col; }
static void user_matrix_col_deselect(uint8_t col) { (void)col; }
static uint8_t user_matrix_read_rows(void) { return (uint8_t)~rows_low[selected]; }
static void delay_us(uint8_t x) { (void)x; }
static void sleep_note_activity(void) {}
static void add_mods(uint8_t x) { (void)x; }
static void del_mods(uint8_t x) { (void)x; }
static void add_key(uint8_t x) { (void)x; presses++; }
static void del_key(uint8_t x) { (void)x; releases++; }
static void send_keyboard_report(void) {}
static void host_system_send(uint16_t x) { (void)x; }
static uint16_t keycode_to_system(uint8_t x) { return x; }
static uint16_t keycode_to_consumer(uint8_t x) { return x; }
static void host_consumer_send(uint16_t x) { (void)x; }
static bool kb_process_record(uint16_t x, bool p) { (void)x; (void)p; return true; }
static bool layout_process_record(uint16_t x, bool p) { (void)x; (void)p; return true; }
'''
source += without_includes(matrix)
source += r'''
static void scan(bool down) { rows_low[1] = down ? (1 << 3) : 0; matrix_scan_full(); matrix_task(); }
int main(void) {
    matrix_init();
    for (int i = 0; i < 20; i++) scan(false);
    // Contacts chatter on press, then settle closed.
    const bool press_bounce[] = {1, 0, 1, 1, 0, 1, 0, 1};
    for (unsigned i = 0; i < sizeof press_bounce; i++) scan(press_bounce[i]);
    for (int i = 0; i < 20; i++) scan(true);
    assert(presses == 1 && releases == 0);
    // Contacts chatter on release, then settle open.
    const bool release_bounce[] = {0, 1, 0, 0, 1, 0};
    for (unsigned i = 0; i < sizeof release_bounce; i++) scan(release_bounce[i]);
    for (int i = 0; i < 20; i++) scan(false);
    assert(presses == 1 && releases == 1);
    // A short but clean tap still registers.
    for (int i = 0; i < DEBOUNCE_SCANS + 1; i++) scan(true);
    for (int i = 0; i < DEBOUNCE_SCANS + 1; i++) scan(false);
    assert(presses == 2 && releases == 2);
}
'''
with tempfile.TemporaryDirectory(prefix='km-g6-debounce-test-') as directory:
    binary = str(Path(directory) / 'test')
    subprocess.run(['cc', '-std=c99', '-Wall', '-Wextra', '-Werror',
                    '-Wno-unused-function', '-I', str(smk / 'src/smk'),
                    '-x', 'c', '-', '-o', binary], input=source, text=True, check=True)
    subprocess.run([binary], check=True)
print('PASS: press bounce, release bounce, and short taps each yield one press/release')
