# Futurecast — audio

The Pi's audio brain: a looping ambience bed with channel buttons that each
play one track once, then drop back to ambience.

## Files
- `config.py` — paths, channel map, volume/ducking, button-board pins. **Edit this.**
- `audio_engine.py` — the playback model (ambience loop, one-shot tracks,
  volume, ducking). Knows nothing about buttons.
- `main.py` — keyboard test harness with a status window, for bench-testing
  without the button board.
- `mcp23017.py` — minimal I2C driver for the button board's expander.
- `button_service.py` — reads the real buttons (time-shared button/LED pins,
  debounce); `--map` = interactive pin→channel mapping helper.
- `run.py` — headless operation mode: engine + buttons, no window. This is
  what autostarts.
- `futurecast.service` — systemd user unit for autostart (install notes inside).
- `audio/` — placeholder sounds (generated tones). Swap in real `.ogg`/`.wav`.

## Run it
```bash
python3 -m pip install -r requirements.txt   # pygame-ce
python3 main.py
```
A small window opens. Keys **1-9 0 q w e r** trigger channels 1..14,
**+ / -** change volume, **ESC** quits. You should hear ambience immediately,
with each key layering a tone on top.

## Swapping in real audio
Drop real files into `audio/` and point `config.py` at them (keep names, or
change the paths in `CHANNELS` / `AMBIENCE`). Prefer `.ogg` or `.wav`;
avoid `.mp3` (unreliable in pygame). Ambience should loop cleanly.

## Real buttons (MCP23017 @ 0x21, SDA/SCL on header pins 3/5)
One-time, after wiring (needs `i2cdetect -y 1` to show `21`):
```bash
python3 -m pip install -r requirements.txt   # adds smbus2
python3 button_service.py --map              # press each button as prompted
```
Paste the printed `PIN_TO_CHANNEL` into `config.py`, then run for real:
```bash
python3 run.py
```
Channel buttons play their track (and hold their LED as the selected
indicator); the two volume buttons nudge the master level.

## Autostart
`futurecast.service` is a systemd **user** unit — install instructions are in
comments at the top of the file. Short version: copy to
`~/.config/systemd/user/`, `systemctl --user enable --now futurecast`, and
`loginctl enable-linger $USER` so it starts at boot without a login.
