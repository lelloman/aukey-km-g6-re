CC ?= cc
CFLAGS ?= -O2 -Wall -Wextra -Wpedantic

.PHONY: all clean

all: hid-feature km-g6ctl km-g6-keys km-g6-frame test-keymask

hid-feature: hid-feature.c
	$(CC) $(CFLAGS) -o $@ $<

km-g6ctl: km-g6ctl.c
	$(CC) $(CFLAGS) -o $@ $<

km-g6-keys: km-g6-keys.c
	$(CC) $(CFLAGS) -o $@ $<

km-g6-frame: km-g6-frame.c
	$(CC) $(CFLAGS) -o $@ $<

test-keymask: test-keymask.c
	$(CC) $(CFLAGS) -o $@ $<

clean:
	$(RM) hid-feature km-g6ctl km-g6-keys km-g6-frame test-keymask
