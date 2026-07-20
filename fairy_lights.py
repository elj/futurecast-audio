"""
Fairy-light night fade, synced to the Pixelblaze day/night cycle.

A background thread polls the Pixelblaze WebSocket API for the exported
`phase` variable (0..1, one full day/night cycle) and PWM-dims the
non-addressable fairy-light strands (2N7000 MOSFET on a GPIO pin):
fade up through dusk, hold overnight, fade out through dawn.

Read-only sync: the Pixelblaze keeps its own timing. If the Pixelblaze is
unreachable, the lights hold their last level and recover on reconnect.
Errors never propagate out of the thread — audio is unaffected.

Standalone test:  python3 fairy_lights.py
"""

import json
import threading
import time

import config


def night_amt(phase):
    """Target fairy-light level (0..1) for a given day/night phase."""
    up0, up1 = config.FAIRY_FADE_UP_START, config.FAIRY_FADE_UP_END
    dn0, dn1 = config.FAIRY_FADE_DOWN_START, config.FAIRY_FADE_DOWN_END
    if up0 <= phase < up1:
        return (phase - up0) / (up1 - up0)
    if phase >= up1 or phase < dn0:
        return 1.0
    if dn0 <= phase < dn1:
        return 1.0 - (phase - dn0) / (dn1 - dn0)
    return 0.0


class FairyLights:
    """Background fairy-light controller. start() it; stop() on shutdown."""

    def __init__(self):
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=2)

    # ---- internals ----

    def _run(self):
        try:
            from gpiozero import PWMLED
            led = PWMLED(config.FAIRY_GPIO, frequency=config.FAIRY_PWM_HZ)
        except Exception as e:
            print(f"fairy: GPIO unavailable, fairy lights disabled ({e})")
            return

        current = 0.0
        target = 0.0
        last_poll = 0.0
        ws = None

        while not self._stop.is_set():
            now = time.monotonic()

            if now - last_poll >= config.FAIRY_POLL_S:
                last_poll = now
                try:
                    if ws is None:
                        import websocket
                        ws = websocket.create_connection(
                            config.PIXELBLAZE_URL, timeout=3)
                    phase = self._get_phase(ws)
                    if phase is not None:
                        target = night_amt(phase)
                except Exception:
                    # unreachable: hold last level, retry next poll
                    try:
                        if ws:
                            ws.close()
                    except Exception:
                        pass
                    ws = None

            # ease toward the target so poll steps never show
            step = config.FAIRY_SLEW_PER_S * config.FAIRY_TICK_S
            if current < target:
                current = min(current + step, target)
            elif current > target:
                current = max(current - step, target)

            # gamma ~2 for a perceptually smooth fade
            led.value = (current * current) * config.FAIRY_MAX_BRIGHTNESS

            self._stop.wait(config.FAIRY_TICK_S)

        led.off()

    @staticmethod
    def _get_phase(ws):
        ws.send(json.dumps({"getVars": True}))
        # the Pixelblaze streams other frames too (previews etc.) — skip non-vars
        for _ in range(10):
            msg = ws.recv()
            if isinstance(msg, bytes):
                continue
            data = json.loads(msg)
            if "vars" in data:
                return data["vars"].get("phase")
        return None


if __name__ == "__main__":
    fairy = FairyLights()
    fairy.start()
    print("Fairy lights running standalone. Ctrl-C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        fairy.stop()
