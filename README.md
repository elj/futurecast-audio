# Futurecast — audio

The Pi's audio brain: a looping ambience bed with channel buttons that each
play one track once, then drop back to ambience.

## Files
- `config.py` — paths, channel map, volume + ducking settings. **Edit this.**
- `audio_engine.py` — the playback model (ambience loop, one-shot tracks,
  volume, ducking). Knows nothing about buttons.
- `main.py` — keyboard test harness with a status window, for bench-testing
  before the GPIO buttons are wired.
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

## Next: GPIO
When the button board is mapped, a small GPIO service replaces the keyboard:
it calls `engine.trigger(channel_id)`, `engine.volume_up()`,
`engine.volume_down()`. The engine itself doesn't change.
