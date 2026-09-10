#include <errno.h>
#include <fcntl.h>
#include <linux/hidraw.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>

enum { REPORT_ID = 8, REPORT_SIZE = 8, VERSION = 1, ROWS = 6, COLS = 21 };

static void usage(const char *name)
{
    fprintf(stderr,
            "usage: %s DEVICE info\n"
            "       %s DEVICE set ROW COL INTENSITY\n"
            "       %s DEVICE fill INTENSITY\n"
            "       %s DEVICE clear|on|off\n",
            name, name, name, name);
}

static int number(const char *text, int max, const char *label)
{
    char *end = NULL;
    long value = strtol(text, &end, 0);
    if (!end || *end || value < 0 || value > max) {
        fprintf(stderr, "%s must be between 0 and %d\n", label, max);
        return -1;
    }
    return (int)value;
}

static int send_report(int fd, unsigned char command, unsigned char offset,
                       unsigned char count, unsigned char a,
                       unsigned char b, unsigned char c)
{
    unsigned char report[REPORT_SIZE] = {
        REPORT_ID, VERSION, command, offset, count, a, b, c
    };
    int sent = -1;
    for (int attempt = 0; attempt < 4; ++attempt) {
        sent = ioctl(fd, HIDIOCSFEATURE(REPORT_SIZE), report);
        if (sent == REPORT_SIZE) {
            /* Give the keyboard's small control-transfer stack time to
             * return to idle before the next feature report. */
            usleep(20000);
            return 0;
        }
        if (sent >= 0 || (errno != EPIPE && errno != EBUSY)) {
            break;
        }
        usleep(50000);
    }
    fprintf(stderr, "lighting command: %s\n",
            sent < 0 ? strerror(errno) : "short report");
    return -1;
}

static int set_active(int fd, int active)
{
    return send_report(fd, 3, 0, 0, (unsigned char)active, 0, 0);
}

int main(int argc, char **argv)
{
    if (argc < 3) {
        usage(argv[0]);
        return 2;
    }

    int fd = open(argv[1], O_RDWR | O_CLOEXEC);
    if (fd < 0) {
        fprintf(stderr, "open %s: %s\n", argv[1], strerror(errno));
        return 1;
    }

    int result = 0;
    if (!strcmp(argv[2], "info") && argc == 3) {
        unsigned char report[REPORT_SIZE] = { REPORT_ID };
        int received = ioctl(fd, HIDIOCGFEATURE(REPORT_SIZE), report);
        if (received != REPORT_SIZE || report[0] != REPORT_ID ||
            report[1] != VERSION || report[3] != ROWS || report[4] != COLS) {
            fprintf(stderr, "compatible KM-G6 replacement firmware not found\n");
            result = 1;
        } else {
            printf("protocol=%u active=%u rows=%u cols=%u keys=%u chunk=%u\n",
                   report[1], report[2], report[3], report[4], report[5], report[6]);
        }
    } else if (!strcmp(argv[2], "set") && argc == 6) {
        int row = number(argv[3], ROWS - 1, "row");
        int col = number(argv[4], COLS - 1, "column");
        int val = number(argv[5], 255, "intensity");
        if (row < 0 || col < 0 || val < 0) result = 2;
        else if (send_report(fd, 1, (unsigned char)(row * COLS + col), 1,
                             (unsigned char)val, 0, 0) || set_active(fd, 1)) result = 1;
    } else if (!strcmp(argv[2], "fill") && argc == 4) {
        int val = number(argv[3], 255, "intensity");
        if (val < 0) result = 2;
        else if (send_report(fd, 2, 0, 0, (unsigned char)val, 0, 0) || set_active(fd, 1)) result = 1;
    } else if (!strcmp(argv[2], "clear") && argc == 3) {
        if (send_report(fd, 2, 0, 0, 0, 0, 0) || set_active(fd, 1)) result = 1;
    } else if (!strcmp(argv[2], "on") && argc == 3) {
        if (set_active(fd, 1)) result = 1;
    } else if (!strcmp(argv[2], "off") && argc == 3) {
        if (set_active(fd, 0)) result = 1;
    } else {
        usage(argv[0]);
        result = 2;
    }

    close(fd);
    return result;
}
