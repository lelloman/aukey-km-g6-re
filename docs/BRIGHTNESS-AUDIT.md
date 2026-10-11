# Brightness audit — 2026-09-11

This is an offline source and backup inspection, not an optical measurement.
No firmware was flashed as part of this audit.

## Previously built replacement firmware (before stock-PWM candidate)

The previously built target set the PWM period to 0x0400 (1024), DUTY1 to
1024, and DUTY2 to `1024 - (intensity << 2)`:

| Intensity | DUTY2 compare value |
| ---: | ---: |
| 0 | 1024 |
| 32 | 896 |
| 100 | 624 |
| 128 | 512 |
| 255 | 4 |

Thus 255 is the host protocol maximum, but does not reach a zero compare
value. Under the intended active interval interpretation, the programmed
span is 1020/1024, or 99.609375% of a PWM period. This is not a measurement
of LED duty over a complete multiplexed frame. Endpoint behavior, output
polarity, counter restart behavior, and blanking also matter.

The pinned SMK revision is 2876de0684c1fb60af010ef0fb9426bb8951fb34.
Its `src/platform/sh68f90/systick.c` arms the LED timer for 801 timer ticks,
nominally about 400 microseconds. `src/smk/tick.c` arms that timer *before*
executing the LED update. Column-register programming therefore consumes
part of the scheduled interval. Six LED subframes are requested between
full matrix scans. This improves the scan/subframe ratio but does not
extend the individual subframe duration or establish the actual LED duty.

The full scan contains two 10-microsecond settle delays per column: at
least 420 microseconds for 21 columns, plus execution overhead. LED rows
are blanked during that scan. Per-key average brightness is consequently
lower than its within-row PWM setting. Exact timing needs measurement or
cycle-accurate analysis of the generated firmware.

The target also enables the PWM0 interrupt while upstream's PWM handler is
empty. This is another timing detail to investigate before claiming an
optimal refresh schedule; its runtime impact is not established here.

## Stock comparison

Verified stock application SHA-256:
`d34032c10e8d483ac690079efc626266f2a561917bd15008f3b0402c49653f2a`.

At stock address 0x24A7, the startup routine writes 0x82 to PWM00CON
(XRAM register 0xFF80). At 0x24DA it loads DPTR with 0xFF9C
(PWM0PERDH); accumulator increment after the preceding clear produces 1.
The subsequent write to 0xFF98 (PWM0PERDL) uses zero. The initial PWM0
period is therefore 0x0100 (256), versus replacement firmware's 0x0400.
These register addresses are from the pinned SH68F90 header.

This proves that initial period settings differ. It does not establish
stock maximum brightness: runtime period/duty writes and row dwell timing
have not been fully traced. The earlier documentation's GPIO/current-mode
comparison is insufficient to establish equal brightness.

## Conclusion

## Follow-up: runtime discrepancies

Direct decoding of the stock routine at 0x2BEC (21-column jump table)
establishes the following runtime behavior. For example, column 8 enters
0x2C3C: write 0x8F to PWM00CON, zero DUTY1L/H and DUTY2H, then jump
to 0x2DF6 to write RAM byte 0x2F into DUTY2L. The other columns follow
the same pattern, including bank 4 through direct SFR writes at 0x2DFA.

| Detail | Stock LED update | Current replacement |
| --- | --- | --- |
| Control byte for lit channels | 0x8F | Bank 0 leader 0xCA; other leaders 0x8A; other channels 0x08 |
| Low three control bits | 7 | Bank leaders 2; other channels 0 |
| DUTY1 | 0 | 1024 |
| DUTY2 | brightness byte directly, high byte 0 | 1024 minus four times brightness |
| Zero brightness | skips channel-enable helper | programs compare value 1024 and enables channel |
| Row selection order | program columns, then assert row | assert row, then program columns |

The upstream header identifies selector 2 as SYS_CLK/4. Selector 7's
hardware meaning has not been verified here; no frequency ratio is claimed.
The different control bytes also differ in interrupt-enable and per-channel
mode-enable bits, so describing this simply as a period difference misses
important behavior.

At 0x5258 stock first calls 0x6DF4, then traverses the selected 21-byte
framebuffer row. It calls the column helper only for nonzero bytes.
At 0x52D9 onward it asserts the selected P6 row low. The 0x6DF4 helper
blanks P6 to 0xFF, writes 0x87 to the 18 PWM controls in banks 0–2
and three bank-4 controls, and clears the shared column GPIO latches.
Replacement blanking instead writes leader controls 0x02 and other controls
0x00; its zero framebuffer entries are still enabled by the later blanket
PWM enable routine. These different off mechanisms deserve inspection
even though replacement clear has passed visual testing.

The stock interrupt at 0x5DE6 calls the incremental key scanner at 0x7129,
conditionally calls the row renderer at 0x5258, and advances RAM row
index 0x2E. The common increment path wraps at 7; the renderer handles
indices 0–5 and blanks without selecting a row for index 6. Additional
conditions affect the schedule. Replacement instead performs a full
21-column scan between groups of six LED subframes. Exact stock dwell
time and dynamic period updates remain unverified.

Replacement-specific timing concerns:

- Timer2 is armed before column programming. The available PWM dwell is
  shorter than the nominal 400-microsecond slot by the execution time of
  rendering and other work inside the callback.
- The SET_PWM_DUTY_2 macro evaluates its value expression twice (high and
  low writes). Each host row therefore invokes host_lighting_get 42 times,
  in addition to calculating a background-animation sample even in host
  mode. This adds overhead; its exact duration has not been measured.
- PWM0 interrupt enable remains set although the upstream PWM0 handler is
  empty and scheduling is driven by Timer2. Whether hardware clears its
  flag automatically and the resulting interrupt load need verification.

These findings supersede earlier conversational claims that period alone,
row polarity alone, or six subframes necessarily explain the low-end cutoff.
They do not establish a single proven cause. The inspection above describes
the pre-candidate implementation; subsequent changes are recorded below.

## Assessment

255 is the largest accepted intensity and nearly spans the programmed PWM
period under the intended interpretation. Absolute maximum physical
brightness, or equality with stock maximum, is **not verified**. Merely
removing the four-count endpoint gap would be a very small change in the
ideal PWM span; it cannot explain the observed low-end visibility threshold
by itself. The user's approximate visible threshold of 100 remains an
observation, not a calibrated transfer curve.

To establish parity with stock maximum, measure a selected LED's row and
column waveforms at 0/128/255 and compare with stock at maximum, or obtain
a controlled optical comparison. Preserve keyboard scan timing while
investigating; source changes are not justified solely by a perceived
brightness threshold.

## Stock-PWM candidate implementation

The target patch now uses period 256 in LED banks 0, 1, 2 and 4, DUTY1
zero, and the intensity byte directly as DUTY2. Blanking writes control
0x87 to all 21 channels and clears the shared column GPIO latches with
the rows deselected. Only nonzero intensities start channels with 0x8F;
columns are programmed before selecting the row. The unused PWM0 interrupt
is disabled. Each intensity is fetched once, and background animation
generation is skipped while host lighting is active.

The working keymap and host protocol are unchanged. This is **not** a full
stock scheduler port: the six-subframe/full-matrix scan remains, and Timer2
is still armed before rendering. Selector 7's frequency, actual dwell time,
and stock-equivalent maximum remain unmeasured. Subsequent visual testing
is recorded below.

SDCC compilation succeeded and the interrupt checker reported all 14 vectors
claimed with no overlay collisions. The patch was checked against the built
source. No keyboard writes or flashing were performed during the build;
the user subsequently tested the candidate on hardware.

Candidate: `firmware/build/aukey-km-g6_stock-pwm-candidate.hex`
SHA-256 (including lock indicators, the Fn+F10/F11 release-order fix and
~5 ms key debounce): `7dd6dada98cc4c5bd846ba496e362f3a418918a1eeae5843aedc9ab907a2065f`.
The release-order-fix image without debounce had SHA-256
`7d6946742519bcfba783049e5072b640a3c09034bb1c23709f6fc9af2fd83e80`;
it repeated characters when switch contacts bounced.
The previously tested lock-indicator image had SHA-256
`3409b2abbf94231fb93c0625076f248f91e4adc4dbb7818ba98ce8defd5fafb3`;
it is retained locally as `firmware/build/aukey-km-g6_stock-pwm-before-fn-volume.hex`.
The original volume shortcuts could remain held when Fn was released first.
The matrix now caches each keycode on press and uses it on release, and no
longer clears unrelated held keys when Fn is released. Regression tests
reproduce the original stuck-volume bug and pass with the fix for both volume
keys, both release orders, base-layer presses across Fn changes, and unrelated
held keys. SDCC compilation and the 14-vector interrupt check pass; hardware
validation of the fix is pending. The keycode cache uses 252 bytes of RAM.
The guarded flash command now writes only this candidate, checking its pinned
hash; the earlier default image is no longer built or selectable. Add
`--dry-run` to verify hashes without device access.

### Lock indicators

Stock routine 0x7269 maps RAM 0x1E bits 0/1/2 to active-low P0.2/P0.3/P0.4
(Num/Caps/Scroll Lock). Stock initialization at 0x6336 enables direction
and pull-ups with mask 0x1C. The candidate now implements all three outputs,
initially high/off, and enables their pull-ups while preserving unrelated
P0 bits. Updates run before the backlight-off early return, including in
host-lighting mode. The existing one-byte USB HID LED-state receiver is
unchanged; no protocol discrepancy has been established for Caps Lock.

`python3 firmware/test-lock-indicators.py` checks the actual target statements
for all 256 LED-state bytes and preservation of unrelated GPIO bits.
SDCC compilation and all 14 interrupt-vector checks pass.

### User hardware validation — 2026-09-11

After testing the updated candidate, the user reported that the lock
indicators work and brightness now visibly spans the whole 0–255 range.
The earlier low-end cutoff is no longer observed. Scroll Lock was not
separately confirmed. This is visual validation, not a calibrated brightness
curve or proof of equality with stock maximum.
