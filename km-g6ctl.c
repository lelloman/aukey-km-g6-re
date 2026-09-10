#include <errno.h>
#include <fcntl.h>
#include <linux/hidraw.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>

enum { REPORT_SIZE = 42 };

static void usage(const char *name)
{
    fprintf(stderr,
            "usage: %s DEVICE brightness 0..4\n"
            "       %s DEVICE mode 1..9\n"
            "       %s DEVICE speed 0..4\n",
            name, name,
            name);
}

static int parse_range(const char *text, int min, int max, const char *name)
{
    char *end = NULL;
    long value = strtol(text, &end, 0);
    if (!end || *end || value < min || value > max) {
        fprintf(stderr, "%s must be between %d and %d\n", name, min, max);
        return -1;
    }
    return (int)value;
}

int main(int argc, char **argv)
{
    if (argc != 4) {
        usage(argv[0]);
        return 2;
    }

    int offset;
    int min;
    int max;
    if (strcmp(argv[2], "brightness") == 0) {
        offset = 4;
        min = 0;
        max = 4;
    } else if (strcmp(argv[2], "mode") == 0) {
        offset = 1;
        min = 1;
        max = 9;
    } else if (strcmp(argv[2], "speed") == 0) {
        offset = 3;
        min = 0;
        max = 4;
    } else {
        usage(argv[0]);
        return 2;
    }

    int value = parse_range(argv[3], min, max, argv[2]);
    if (value < 0)
        return 2;

    int fd = open(argv[1], O_RDWR | O_CLOEXEC);
    if (fd < 0) {
        fprintf(stderr, "open %s: %s\n", argv[1], strerror(errno));
        return 1;
    }

    unsigned char report[REPORT_SIZE] = { 0x0a };
    int received = ioctl(fd, HIDIOCGFEATURE(REPORT_SIZE), report);
    if (received != REPORT_SIZE) {
        fprintf(stderr, "read lighting state: %s\n",
                received < 0 ? strerror(errno) : "short report");
        close(fd);
        return 1;
    }

    unsigned int old_value = report[offset];
    report[offset] = (unsigned char)value;

    int sent = ioctl(fd, HIDIOCSFEATURE(REPORT_SIZE), report);
    if (sent != REPORT_SIZE) {
        fprintf(stderr, "write lighting state: %s\n",
                sent < 0 ? strerror(errno) : "short report");
        close(fd);
        return 1;
    }

    printf("KM-G6 %s: %u -> %d\n", argv[2], old_value, value);
    close(fd);
    return 0;
}
