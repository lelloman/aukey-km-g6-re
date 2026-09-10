# Teardown, cleaning, and photography

The goal of the first teardown is inspection only. Do not desolder switches,
connect a programmer, or power the exposed board.

## References

- [Exact KM-G6 complete teardown and switch-mod video](https://www.youtube.com/watch?v=Q3IOGxfu5AY)
- [KM-G6 owner discussing a USB-C conversion after disassembly](https://foro.elchapuzasinformatico.com/threads/convertir-teclado-aukey-alambrico-en-alambrico-usb-c.146886/)

## Prepare

- Keycap puller
- Small Phillips screwdrivers (PH0 and PH1 if available)
- Plastic pick or old bank card; avoid a metal knife
- Several cups or a compartment tray for different screw groups
- Soft brush, microfiber cloth, and compressed air or a hand blower
- Mild dish soap and a bowl for the keycaps
- Phone/camera with macro focus and a strong movable light
- A towel or nonconductive mat

Before starting, photograph the complete key layout. This matters especially
for the modifiers, navigation cluster, and numpad.

## Open the case

1. Shut down anything that depends on this keyboard, unplug it, and move the
   cable away from power.
2. Remove the rear plastic strip and its screws. Keep those screws together.
3. Pull all keycaps straight upward. For large stabilized keys, work gently
   from both sides and stop if a wire resists.
4. Find and remove the small screws between the exposed switches. Keep these
   separate from the rear-strip screws.
5. Check again for screws hidden under labels, rubber feet, or the keycaps if
   one area of the seam remains firmly closed.
6. Start opening the case at the edge farthest from the USB cable. Use a
   plastic pick and lift only a few millimetres.
7. Look inside for the USB cable/connector before separating the halves. Never
   use the cable as a hinge and never pull on its wires.
8. Stop as soon as the back of the PCB is visible. Removing the soldered
   switch/plate assembly should not be necessary for controller identification.

If the case needs significant force, a screw or clip is still engaged. Stop
and photograph that area instead of forcing it.

## Required photographs

Save the original, full-resolution files under `hardware/photos/` using these
names where possible:

```text
01-key-layout.jpg
02-back-strip-removed.jpg
03-whole-pcb.jpg
04-controller-top.jpg
05-controller-angle.jpg
06-pcb-model-revision.jpg
07-usb-area.jpg
08-led-driver-area.jpg
09-other-large-chips.jpg
```

For chip markings:

- Wipe the camera lens.
- Use maximum optical resolution, not digital zoom.
- Photograph directly overhead, then again with light arriving from the side.
- Tap the chip text to focus and ensure the lettering is readable before
  reassembling.
- Include one full-board photo so every close-up has spatial context.

Record any text printed on stickers, the PCB, and the controller package in
`hardware/NOTES.md`.

## Cleaning while it is open

- Clean keycaps separately in lukewarm water with a small amount of dish soap.
- Do not use hot water, alcohol, or a dishwasher on the keycaps.
- Rinse and allow the keycaps to dry completely, preferably 24–48 hours.
- Use a dry soft brush and blower around the switches and PCB.
- Do not soak the assembled keyboard or spray cleaner directly on electronics.
- If electronics require cleaning, use a small amount of high-purity
  isopropyl alcohol on a brush and let it evaporate completely before power.

## Reassemble and verify

1. Reconnect any internal plug exactly as photographed.
2. Close the case without trapping or pinching the USB cable.
3. Install the case screws snugly, not aggressively.
4. Replace the keycaps using the layout photo.
5. Only after the case is fully closed, reconnect USB and test every key with a
   keyboard-testing application.

