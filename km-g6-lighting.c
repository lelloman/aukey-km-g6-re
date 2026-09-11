/* Root-owned, narrowly scoped sudo entry point. Never executes other programs. */
#define KM_G6_RESTRICTED_HELPER
#include "km-g6-frame.c"
#include <glob.h>
#include <sys/stat.h>
#include <linux/input.h>

static int valid_command(int argc, char **argv)
{
    if (argc == 2 && (!strcmp(argv[1], "info") || !strcmp(argv[1], "clear") ||
                     !strcmp(argv[1], "on") || !strcmp(argv[1], "off"))) return 1;
    if (argc == 3 && !strcmp(argv[1], "fill"))
        return number(argv[2], 255, "intensity") >= 0;
    if (argc == 5 && !strcmp(argv[1], "set"))
        return number(argv[2], ROWS - 1, "row") >= 0 &&
               number(argv[3], COLS - 1, "column") >= 0 &&
               number(argv[4], 255, "intensity") >= 0;
    return 0;
}

static int compatible(int fd)
{
    struct stat st;
    struct hidraw_devinfo device = {0};
    char phys[256] = {0};
    if (fstat(fd, &st) || !S_ISCHR(st.st_mode) ||
        ioctl(fd, HIDIOCGRAWINFO, &device) < 0 || device.bustype != BUS_USB ||
        (unsigned short)device.vendor != 0x258a ||
        (unsigned short)device.product != 0x002a ||
        ioctl(fd, HIDIOCGRAWPHYS(sizeof(phys) - 1), phys) < 0) return 0;
    size_t length = strlen(phys);
    if (length < 7 || strcmp(phys + length - 7, "/input1")) return 0;
    unsigned char report[REPORT_SIZE] = {REPORT_ID};
    return ioctl(fd, HIDIOCGFEATURE(REPORT_SIZE), report) == REPORT_SIZE &&
           report[0] == REPORT_ID && report[1] == VERSION &&
           report[3] == ROWS && report[4] == COLS &&
           report[5] == ROWS * COLS && report[6] == 3;
}

int main(int argc, char **argv)
{
    /* Reject everything outside the lighting API before any device access. */
    if (!valid_command(argc, argv)) {
        fprintf(stderr, "usage: %s info|clear|on|off\n"
                        "       %s fill INTENSITY\n"
                        "       %s set ROW COL INTENSITY\n", argv[0], argv[0], argv[0]);
        return 2;
    }
    glob_t nodes = {0};
    int selected = -1;
    if (glob("/dev/hidraw*", 0, NULL, &nodes) == 0) {
        for (size_t i = 0; i < nodes.gl_pathc; ++i) {
            int fd = open(nodes.gl_pathv[i], O_RDWR | O_CLOEXEC | O_NOFOLLOW | O_NONBLOCK);
            if (fd < 0) continue;
            if (!compatible(fd)) { close(fd); continue; }
            if (selected >= 0) {
                fprintf(stderr, "Multiple compatible KM-G6 keyboards; refusing ambiguous target.\n");
                close(fd);
                close(selected);
                globfree(&nodes);
                return 1;
            }
            selected = fd;
        }
    }
    globfree(&nodes);
    if (selected < 0) {
        fprintf(stderr, "No accessible KM-G6 with compatible replacement lighting firmware.\n");
        return 1;
    }
    /* Retain the validated descriptor; do not reopen a path after checking. */
    char *command[7] = {argv[0], NULL};
    for (int i = 1; i < argc; ++i) command[i + 1] = argv[i];
    int result = run_command(selected, argc + 1, command);
    close(selected);
    return result;
}
