#include <ctype.h>
#include <errno.h>
#include <fcntl.h>
#include <linux/hidraw.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <time.h>
#include <unistd.h>

enum {
    STATE_SIZE = 42,
    KEYMAP_SIZE = 505,
    MASK_SIZE = 127,
    FIRST_SLOT = 1,
    LAST_SLOT = 124
};

struct named_key { const char *name; uint32_t usage; };

static const struct named_key named_keys[] = {
    {"enter",0x28},{"esc",0x29},{"escape",0x29},{"backspace",0x2a},
    {"tab",0x2b},{"space",0x2c},{"minus",0x2d},{"equal",0x2e},
    {"leftbracket",0x2f},{"rightbracket",0x30},{"backslash",0x31},
    {"semicolon",0x33},{"apostrophe",0x34},{"quote",0x34},{"grave",0x35},
    {"comma",0x36},{"dot",0x37},{"period",0x37},{"slash",0x38},
    {"capslock",0x39},{"printscreen",0x46},{"scrolllock",0x47},
    {"pause",0x48},{"insert",0x49},{"home",0x4a},{"pageup",0x4b},
    {"delete",0x4c},{"end",0x4d},{"pagedown",0x4e},{"right",0x4f},
    {"left",0x50},{"down",0x51},{"up",0x52},{"numlock",0x53},
    {"kp/",0x54},{"kp*",0x55},{"kp-",0x56},{"kp+",0x57},
    {"kpenter",0x58},{"kp1",0x59},{"kp2",0x5a},{"kp3",0x5b},
    {"kp4",0x5c},{"kp5",0x5d},{"kp6",0x5e},{"kp7",0x5f},
    {"kp8",0x60},{"kp9",0x61},{"kp0",0x62},{"kp.",0x63},
    {"menu",0x65},{"leftctrl",0x0100},{"leftshift",0x0200},
    {"leftalt",0x0400},{"leftwin",0x0800},{"leftmeta",0x0800},
    {"rightctrl",0x1000},{"rightshift",0x2000},{"rightalt",0x4000},
    {"rightwin",0x8000},{"rightmeta",0x8000}
};

static uint32_t key_usage(const char *input)
{
    char name[64];
    size_t length = strlen(input);
    if (length >= sizeof(name))
        return UINT32_MAX;
    for (size_t i = 0; i <= length; ++i)
        name[i] = (char)tolower((unsigned char)input[i]);

    if (length == 1 && name[0] >= 'a' && name[0] <= 'z')
        return 0x04u + (uint32_t)(name[0] - 'a');
    if (length == 1 && name[0] >= '1' && name[0] <= '9')
        return 0x1eu + (uint32_t)(name[0] - '1');
    if (strcmp(name, "0") == 0)
        return 0x27;
    if (name[0] == 'f' && length >= 2 && length <= 3) {
        char *end = NULL;
        long number = strtol(name + 1, &end, 10);
        if (end && !*end && number >= 1 && number <= 12)
            return 0x3au + (uint32_t)(number - 1);
    }
    for (size_t i = 0; i < sizeof(named_keys) / sizeof(named_keys[0]); ++i)
        if (strcmp(name, named_keys[i].name) == 0)
            return named_keys[i].usage;
    return UINT32_MAX;
}

static uint32_t slot_usage(const unsigned char *keymap, int slot)
{
    int offset = 4 + ((slot - 1) * 4);
    return ((uint32_t)keymap[offset] << 24)
         | ((uint32_t)keymap[offset + 1] << 16)
         | ((uint32_t)keymap[offset + 2] << 8)
         | keymap[offset + 3];
}

static int find_slot(const unsigned char *keymap, uint32_t usage)
{
    for (int slot = FIRST_SLOT; slot <= LAST_SLOT; ++slot)
        if (slot_usage(keymap, slot) == usage)
            return slot;
    return -1;
}

int main(int argc, char **argv)
{
    if (argc < 3) {
        fprintf(stderr,
                "usage: %s DEVICE [--duration SECONDS] KEY... | --all | --clear\n",
                argv[0]);
        return 2;
    }

    int first_key = 2;
    int duration = 0;
    if (argc >= 5 && strcmp(argv[2], "--duration") == 0) {
        char *end = NULL;
        long parsed = strtol(argv[3], &end, 10);
        if (!end || *end || parsed < 1 || parsed > 60) {
            fprintf(stderr, "duration must be between 1 and 60 seconds\n");
            return 2;
        }
        duration = (int)parsed;
        first_key = 4;
    }

    int fd = open(argv[1], O_RDWR | O_CLOEXEC);
    if (fd < 0) {
        fprintf(stderr, "open %s: %s\n", argv[1], strerror(errno));
        return 1;
    }

    unsigned char keymap[KEYMAP_SIZE] = { 0x09 };
    int received = ioctl(fd, HIDIOCGFEATURE(KEYMAP_SIZE), keymap);
    if (received != KEYMAP_SIZE || find_slot(keymap, 0x14) != 8) {
        fprintf(stderr, "unexpected KM-G6 keymap; refusing to write\n");
        close(fd);
        return 1;
    }

    unsigned char mask[MASK_SIZE] = { 0x0b };
    if (argc == first_key + 1 && strcmp(argv[first_key], "--all") == 0) {
        for (int slot = FIRST_SLOT; slot <= LAST_SLOT; ++slot)
            if (slot_usage(keymap, slot) != 0)
                mask[2 + slot] = 0xff;
    } else if (!(argc == first_key + 1 && strcmp(argv[first_key], "--clear") == 0)) {
        for (int arg = first_key; arg < argc; ++arg) {
            uint32_t usage = key_usage(argv[arg]);
            int slot = usage == UINT32_MAX ? -1 : find_slot(keymap, usage);
            if (slot < 0) {
                fprintf(stderr, "unknown or unavailable key: %s\n", argv[arg]);
                close(fd);
                return 2;
            }
            mask[2 + slot] = 0xff;
        }
    }

    unsigned char state[STATE_SIZE] = { 0x0a };
    received = ioctl(fd, HIDIOCGFEATURE(STATE_SIZE), state);
    if (received != STATE_SIZE) {
        fprintf(stderr, "cannot read lighting state: %s\n",
                received < 0 ? strerror(errno) : "short report");
        close(fd);
        return 1;
    }
    if (state[1] != 4 || (state[2] != 9 && state[2] != 10)) {
        fprintf(stderr,
                "custom mode is not active (mode=%u profile=%u); "
                "press Fn+PgUp, then Fn+9, and retry\n",
                state[1], state[2]);
        close(fd);
        return 1;
    }

    int frames = duration ? duration * 200 : 1;
    const struct timespec frame_delay = { .tv_sec = 0, .tv_nsec = 5000000 };
    for (int frame = 0; frame < frames; ++frame) {
        if (ioctl(fd, HIDIOCSFEATURE(MASK_SIZE), mask) != MASK_SIZE) {
            fprintf(stderr, "cannot write key mask: %s\n", strerror(errno));
            close(fd);
            return 1;
        }
        if (duration && frame + 1 < frames)
            nanosleep(&frame_delay, NULL);
    }

    printf("KM-G6 sent %d lighting frame%s.\n", frames, frames == 1 ? "" : "s");
    close(fd);
    return 0;
}
