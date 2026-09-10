#include <errno.h>
#include <fcntl.h>
#include <linux/hidraw.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>

static void usage(const char *name)
{
    fprintf(stderr, "usage: %s DEVICE REPORT_ID LENGTH\n", name);
}

int main(int argc, char **argv)
{
    if (argc != 4) {
        usage(argv[0]);
        return 2;
    }

    char *end = NULL;
    unsigned long report_id = strtoul(argv[2], &end, 0);
    if (!end || *end || report_id > 255) {
        fprintf(stderr, "invalid report id: %s\n", argv[2]);
        return 2;
    }

    unsigned long payload_len = strtoul(argv[3], &end, 0);
    if (!end || *end || payload_len == 0 || payload_len > 65535) {
        fprintf(stderr, "invalid report length: %s\n", argv[3]);
        return 2;
    }

    size_t buffer_len = payload_len + 1;
    unsigned char *buffer = calloc(buffer_len, 1);
    if (!buffer) {
        perror("calloc");
        return 1;
    }
    buffer[0] = (unsigned char)report_id;

    int fd = open(argv[1], O_RDONLY | O_CLOEXEC);
    if (fd < 0) {
        fprintf(stderr, "open %s: %s\n", argv[1], strerror(errno));
        free(buffer);
        return 1;
    }

    int received = ioctl(fd, HIDIOCGFEATURE(buffer_len), buffer);
    if (received < 0) {
        fprintf(stderr, "HIDIOCGFEATURE 0x%02lx: %s\n", report_id,
                strerror(errno));
        close(fd);
        free(buffer);
        return 1;
    }

    for (int i = 0; i < received; ++i) {
        printf("%02x%s", buffer[i], (i + 1) % 16 ? " " : "\n");
    }
    if (received % 16)
        putchar('\n');

    close(fd);
    free(buffer);
    return 0;
}
