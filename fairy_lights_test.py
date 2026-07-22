#!/usr/bin/env python3
"""
Futurecast - fairy-light BENCH TEST (no Pixelblaze needed).

Drives the MOSFET on the fairy-light GPIO directly so you can check wiring,
the strands, and the warm-white 0402s, and pick a good FAIRY_MAX_BRIGHTNESS -
all without any network or Pixelblaze. Pin, PWM frequency, gamma, and
brightness cap come from config.py, so this matches fairy_lights.py exactly.

Dependencies:  pip install gpiozero
Usage:
    python3 fairy_lights_test.py           # slow fade up/down loop (default)
    python3 fairy_lights_test.py on        # full on, hold
    python3 fairy_lights_test.py off       # off
    python3 fairy_lights_test.py 0.4       # hold at 40% (0..1), gamma-corrected
    python3 fairy_lights_test.py blink     # 1 s on / 1 s off, to confirm switching
Ctrl-C exits and turns the lights off.
"""

import sys
import time

from gpiozero import PWMLED

import config

FADE_SECONDS = 4.0       # time for one up (or down) sweep in the fade loop


def apply(led, level):
    """Set perceived brightness 0..1 with gamma ~2, capped by FAIRY_MAX_BRIGHTNESS."""
    level = max(0.0, min(1.0, level))
    led.value = (level * level) * config.FAIRY_MAX_BRIGHTNESS


def fade_loop(led):
    print("Fade up/down loop - Ctrl-C to stop.")
    tick = 0.05
    steps = int(FADE_SECONDS / tick)
    while True:
        for i in range(steps + 1):      # up
            apply(led, i / steps)
            time.sleep(tick)
        time.sleep(0.5)
        for i in range(steps + 1):      # down
            apply(led, 1 - i / steps)
            time.sleep(tick)
        time.sleep(0.5)


def blink(led):
    print("Blink 1 s on / 1 s off - Ctrl-C to stop.")
    while True:
        apply(led, 1.0)
        time.sleep(1.0)
        apply(led, 0.0)
        time.sleep(1.0)


def main():
    led = PWMLED(config.FAIRY_GPIO, frequency=config.FAIRY_PWM_HZ)
    arg = sys.argv[1].lower() if len(sys.argv) > 1 else "fade"
    try:
        if arg == "fade":
            fade_loop(led)
        elif arg == "blink":
            blink(led)
        elif arg == "on":
            apply(led, 1.0)
            print("Full on - Ctrl-C to exit.")
            while True:
                time.sleep(1)
        elif arg == "off":
            apply(led, 0.0)
            print("Off - Ctrl-C to exit.")
            while True:
                time.sleep(1)
        else:
            level = float(arg)          # e.g. 0.4
            apply(led, level)
            print(f"Holding at {level:.0%} - Ctrl-C to exit.")
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        led.off()
        print("\nLights off.")


if __name__ == "__main__":
    main()
