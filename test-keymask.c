#include <errno.h>
#include <fcntl.h>
#include <linux/hidraw.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>

enum {
    STATE_REPORT_SIZE = 42,
    MASK_REPORT_SIZE = 127,
    Q_SLOT = 8
};

int main(int argc, char **argv)
{
    if (argc != 2) {
        fprintf(stderr, "usage: %s DEVICE\n", argv[0]);
        return 2;
    }

    int fd = open(argv[1], O_RDWR | O_CLOEXEC);
    if (fd < 0) {
        fprintf(stderr, "open %s: %s\n", argv[1], strerror(errno));
        return 1;
    }

    unsigned char state[STATE_REPORT_SIZE] = { 0x0a };
    int received = ioctl(fd, HIDIOCGFEATURE(STATE_REPORT_SIZE), state);
    if (received != STATE_REPORT_SIZE) {
        fprintf(stderr, "cannot read lighting state: %s\n",
                received < 0 ? strerror(errno) : "short report");
        close(fd);
        return 1;
    }

    if (state[1] != 4 || (state[2] != 9 && state[2] != 10)) {
        fprintf(stderr,
                "refusing write: select custom profile Fn+9 or Fn+0 first "
                "(state is mode=%u profile=%u)\n",
                state[1], state[2]);
        close(fd);
        return 1;
    }

    unsigned char mask[MASK_REPORT_SIZE] = { 0x0b };
    mask[1 + Q_SLOT] = 1;

    int sent = ioctl(fd, HIDIOCSFEATURE(MASK_REPORT_SIZE), mask);
    if (sent != MASK_REPORT_SIZE) {
        fprintf(stderr, "cannot write key mask: %s\n",
                sent < 0 ? strerror(errno) : "short report");
        close(fd);
        return 1;
    }

    printf("Sent a 126-slot custom-light mask with only Q (slot %d) enabled.\n",
           Q_SLOT);
    close(fd);
    return 0;
}
