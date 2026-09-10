# KM-G6 stock firmware backup

Captured on 2026-09-10 from the AUKEY KM-G6 UK B2 V1.1 with a BYK901
(SH68F90A-family) LQFP64 controller, using sinowisp 2.1.0.

## Verified USB-ISP captures

The two complete 64 KiB reads are byte-for-byte identical:

```text
SHA-256  cf2dcfe9b6830e254d031eaeefc8c6974d602a10b0a4c80b95f329ead7a258f5
MD5       8f0dde5b67bd80b3d0053b16f71c1850
files     km-g6-stock-full-1.bin
          km-g6-stock-full-2.bin
```

The 4 KiB bootloader region starts at `0xF000` and has MD5
`2d169670eae0d36eae8188562c1f66e8`, a bootloader recognized by sinowisp for
the SH68F90/SH68F90A platform.

These full captures are in USB-ISP representation. Keep an untouched copy;
do not pass a full 64 KiB file to `sinowisp write`, which expects only the
60 KiB application region.

`km-g6-stock-firmware-isp.bin` is that exact 60 KiB application region,
extracted from the verified full capture for possible USB-ISP restoration:

```text
SHA-256  d34032c10e8d483ac690079efc626266f2a561917bd15008f3b0402c49653f2a
MD5       219db648867596421c4675c3e7707003
```

It has not been written back to the device; restoration remains an emergency
operation, not a routine verification step.

## Physical-programmer representation

`km-g6-stock-full-jtag.bin` is the offline `sinowisp convert --direction
to_jtag` result. Its SHA-256 is:

```text
9570ad049d747856a3462f36720e3bb496ecc606a64fab006a266cb6841862f4
```

Converting it back with `--direction to_isp` reproduces the first USB-ISP
capture byte-for-byte. This file is reserved for physical recovery and must
not be written through the USB ISP command.

Store at least one copy of these files on another disk before experimental
firmware is flashed.
