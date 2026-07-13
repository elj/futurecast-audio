"""
Futurecast — headless operation mode (what systemd runs on boot).

No window, no keyboard: ambience starts looping and the MCP23017 button
board drives the engine. Ctrl-C / SIGTERM exits cleanly.
"""

import signal
import time

import config
from audio_engine import AudioEngine
from button_service import ButtonBoard
from mcp23017 import MCP23017


def main():
    engine = AudioEngine(config.AMBIENCE, config.CHANNELS)
    engine.start_ambience()

    mcp = MCP23017(config.I2C_BUS, config.MCP23017_ADDR)
    board = ButtonBoard(
        mcp, config.PIN_TO_CHANNEL, config.VOL_UP_PIN, config.VOL_DOWN_PIN,
        on_channel=engine.trigger,
        on_vol_up=engine.volume_up,
        on_vol_down=engine.volume_down,
    )

    running = True

    def stop(signum, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    print("Futurecast running (headless). Ctrl-C to stop.")
    period = 1.0 / config.POLL_HZ
    while running:
        board.poll()
        engine.update()
        time.sleep(period)

    mcp.close()


if __name__ == "__main__":
    main()
