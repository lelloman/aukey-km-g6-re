/* Exercise the privileged API with mocked HID ioctls; never touches a keyboard. */
#define ioctl mock_ioctl
#define usleep mock_usleep
#define main helper_main
#include "km-g6-lighting.c"
#undef main
#undef ioctl
#undef usleep
#include <assert.h>
#include <stdarg.h>

static struct hidraw_devinfo identity = {BUS_USB, 0x258a, 0x002a};
static const char *physical = "usb-test/input1";
static unsigned char metadata[8] = {8, 1, 1, 6, 21, 126, 3, 0};
static unsigned char writes[4][8];
static int write_count;

int mock_usleep(useconds_t duration) { (void)duration; return 0; }

int mock_ioctl(int fd, unsigned long request, ...)
{
    (void)fd;
    va_list args;
    va_start(args, request);
    void *buffer = va_arg(args, void *);
    va_end(args);
    if (request == HIDIOCGRAWINFO) {
        memcpy(buffer, &identity, sizeof(identity));
        return 0;
    }
    if (request == HIDIOCGRAWPHYS(255)) {
        strcpy(buffer, physical);
        return (int)strlen(physical) + 1;
    }
    if (request == HIDIOCGFEATURE(8)) {
        memcpy(buffer, metadata, 8);
        return 8;
    }
    assert(request == HIDIOCSFEATURE(8));
    assert(write_count < 4);
    memcpy(writes[write_count++], buffer, 8);
    return 8;
}

int main(void)
{
    char *set[] = {"helper", "set", "4", "5", "255"};
    assert(valid_command(5, set));
    set[4] = "256"; assert(!valid_command(5, set));
    set[4] = ""; assert(!valid_command(5, set));
    set[4] = "9999999999999999999999999999"; assert(!valid_command(5, set));
    set[4] = "255";
    set[2] = "6"; assert(!valid_command(5, set));
    set[2] = "4";
    set[3] = "21"; assert(!valid_command(5, set));
    set[3] = "-1"; assert(!valid_command(5, set));
    char *bad[] = {"helper", "/dev/hidraw4", "clear"};
    assert(!valid_command(3, bad));
    bad[1] = "flash"; assert(!valid_command(2, bad));
    bad[1] = "clear"; assert(!valid_command(3, bad));

    int fd = open("/dev/null", O_RDWR);
    assert(fd >= 0 && compatible(fd));
    identity.vendor = 1; assert(!compatible(fd)); identity.vendor = 0x258a;
    identity.product = 1; assert(!compatible(fd)); identity.product = 0x002a;
    identity.bustype = BUS_BLUETOOTH; assert(!compatible(fd)); identity.bustype = BUS_USB;
    physical = "usb-test/input0"; assert(!compatible(fd)); physical = "usb-test/input1";
    for (int i = 0; i < 7; ++i) {
        if (i == 2) continue; /* Active state does not affect compatibility. */
        metadata[i] ^= 1; assert(!compatible(fd)); metadata[i] ^= 1;
    }
    assert(compatible(fd));
    close(fd);

    char *frame[] = {"helper", NULL, "set", "4", "5", "255"};
    assert(run_command(-1, 6, frame) == 0 && write_count == 2);
    const unsigned char expected_set[] = {8, 1, 1, 89, 1, 255, 0, 0};
    const unsigned char expected_on[] = {8, 1, 3, 0, 0, 1, 0, 0};
    assert(!memcmp(writes[0], expected_set, 8));
    assert(!memcmp(writes[1], expected_on, 8));
    write_count = 0;
    frame[2] = "clear";
    assert(run_command(-1, 3, frame) == 0 && write_count == 2);
    const unsigned char expected_clear[] = {8, 1, 2, 0, 0, 0, 0, 0};
    assert(!memcmp(writes[0], expected_clear, 8));
    assert(!memcmp(writes[1], expected_on, 8));
    puts("PASS: command bounds, device/protocol validation, exact lighting-only reports");
}
