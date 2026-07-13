"""
Button board service — MCP23017 (I2C, 0x21) feeding the AudioEngine.

The board is 16 expander pins: 14 channel button+LED pairs that TIME-SHARE
one pin each, plus 2 volume buttons (no LEDs). Scheme ported from
Arduino/Channel_board_demo.ino:

  - All pins idle as input w/ pull-up; a press reads LOW.
  - The selected channel's pin is held OUTPUT LOW so its LED stays lit.
  - Each poll, the lit pin is flipped back to input for one read
    (sub-millisecond — the LED blink is invisible), so every button,
    including the selected one, stays readable.

Nothing here plays audio; ButtonBoard just fires callbacks. run.py wires
those to engine.trigger() / volume_up() / volume_down().

Run `python button_service.py --map` on the Pi for the interactive helper
that records which expander pin belongs to which channel number.
"""

import sys
import time

import config
from mcp23017 import MCP23017


class ButtonBoard:
    def __init__(self, mcp, pin_to_channel, vol_up_pin, vol_down_pin,
                 on_channel=None, on_vol_up=None, on_vol_down=None):
        self._mcp = mcp
        self._pin_to_channel = dict(pin_to_channel)
        self._vol_up = vol_up_pin
        self._vol_down = vol_down_pin
        self._on_channel = on_channel
        self._on_vol_up = on_vol_up
        self._on_vol_down = on_vol_down

        self._selected = None    # pin currently holding its LED lit
        self._raw_prev = 0xFFFF  # last raw sample (1 = released)
        self._stable = 0xFFFF    # debounced state

        for pin in range(16):
            mcp.input_pullup(pin)

    def poll(self):
        """Read the board once; fire callbacks on fresh presses. Call ~50x/s."""
        # Flip the lit pin to input for the read so its button stays readable.
        if self._selected is not None:
            self._mcp.input_pullup(self._selected)
        raw = self._mcp.read_all()
        if self._selected is not None:
            self._mcp.output_low(self._selected)

        # Debounce: a bit must read the same on two consecutive polls
        # (2 x poll period) before the debounced state moves.
        settled = ~(raw ^ self._raw_prev) & 0xFFFF
        new_stable = (self._stable & ~settled) | (raw & settled)
        presses = self._stable & ~new_stable  # bits that went 1 -> 0
        self._raw_prev = raw
        self._stable = new_stable

        if not presses:
            return
        for pin in range(16):
            if not (presses >> pin) & 1:
                continue
            if pin == self._vol_up:
                if self._on_vol_up:
                    self._on_vol_up()
            elif pin == self._vol_down:
                if self._on_vol_down:
                    self._on_vol_down()
            elif pin in self._pin_to_channel:
                self._select(pin)
                if self._on_channel:
                    self._on_channel(self._pin_to_channel[pin])

    def _select(self, pin):
        """Move the selected-channel LED to `pin`."""
        if self._selected is not None and self._selected != pin:
            self._mcp.input_pullup(self._selected)
        self._selected = pin
        self._mcp.output_low(pin)


# --- mapping helper ----------------------------------------------------------

def _wait_press(mcp):
    """Block until a fresh press appears; return its pin after release."""
    prev = mcp.read_all()
    while True:
        time.sleep(0.02)
        raw = mcp.read_all()
        pressed = prev & ~raw
        prev = raw
        for pin in range(16):
            if (pressed >> pin) & 1:
                while not (mcp.read_all() >> pin) & 1:  # wait for release
                    time.sleep(0.02)
                return pin


def _pin_name(pin):
    port, bit = divmod(pin, 8)
    return f"pin {pin:2d} (GP{'AB'[port]}{bit})"


def _capture(mcp, label, taken):
    """Prompt for `label`, wait for a press on a pin not already captured."""
    print(f"Press the button for {label} ... ", end="", flush=True)
    while True:
        pin = _wait_press(mcp)
        if pin in taken:
            print(f"\n  ({_pin_name(pin)} is already {taken[pin]} - "
                  "press a different button) ... ", end="", flush=True)
            continue
        print(_pin_name(pin))
        return pin


def run_mapping():
    """Identify every button by pressing it - no assumptions about wiring."""
    mcp = MCP23017(config.I2C_BUS, config.MCP23017_ADDR)
    for pin in range(16):
        mcp.input_pullup(pin)

    print("Button mapping mode - press each button when asked.")
    print("Captured channel buttons light their LED as confirmation. "
          "Ctrl-C aborts.\n")

    taken = {}  # pin -> description, for duplicate rejection

    vol_up = _capture(mcp, "VOLUME UP", taken)
    taken[vol_up] = "VOLUME UP"
    vol_down = _capture(mcp, "VOLUME DOWN", taken)
    taken[vol_down] = "VOLUME DOWN"

    mapping = {}  # pin -> channel
    for channel in range(1, 15):
        pin = _capture(mcp, f"CHANNEL {channel:2d}", taken)
        taken[pin] = f"channel {channel}"
        mapping[pin] = channel
        mcp.output_low(pin)  # leave the LED on as feedback

    print("\nDone. Paste this into config.py:\n")
    print(f"VOL_UP_PIN = {vol_up}")
    print(f"VOL_DOWN_PIN = {vol_down}")
    print("PIN_TO_CHANNEL = {")
    for pin in sorted(mapping):
        print(f"    {pin:2d}: {mapping[pin]:2d},")
    print("}")

    for pin in mapping:
        mcp.input_pullup(pin)
    mcp.close()


if __name__ == "__main__":
    if "--map" in sys.argv:
        try:
            run_mapping()
        except KeyboardInterrupt:
            print("\nAborted.")
    else:
        print("This module is imported by run.py. "
              "Use `python button_service.py --map` for the mapping helper.")
