"""
Futurecast audio configuration.

Everything project-specific lives here so the engine and the test harness
stay generic. Edit this file to point at real audio and to remap channels.
"""

from pathlib import Path

AUDIO_DIR = Path(__file__).parent / "audio"

# The idle bed: loops forever underneath everything.
AMBIENCE = AUDIO_DIR / "ambience.wav"

# channel_id -> audio file. channel_id is whatever you press (1..14).
# Currently placeholder tones; swap the files (keep the names, or change paths).
CHANNELS = {i: AUDIO_DIR / f"channel_{i:02d}.wav" for i in range(1, 15)}

# --- Volume ---
MASTER_VOLUME = 0.7    # starting master level (0.0 - 1.0)
VOLUME_STEP = 0.1      # how much each volume-button press moves it
VOLUME_FLOOR = 0.1     # lowest master level (never fully mutes, per design)
VOLUME_CEIL = 1.0

# --- Ambience ducking ---
# When a channel track plays, drop the ambience to this fraction of its level
# so the track sits on top. Set DUCK = 1.0 to disable ducking entirely.
# This is an instant level change (no fade engine).
DUCK = 0.5

# --- Button board (MCP23017 over I2C) ---
I2C_BUS = 1           # Pi header I2C (pins 3/5) is bus 1
MCP23017_ADDR = 0x21

# Expander pin numbers: 0-7 = port A (GPA0-7), 8-15 = port B (GPB0-7).
# Measured on the real board with `button_service.py --map`, 2026-07-12.
VOL_UP_PIN = 15       # GPB7, no LED
VOL_DOWN_PIN = 14     # GPB6, no LED

# Expander pin -> channel id (1..14). Board is wired mostly in reverse
# order, except channel 10 on GPB0.
PIN_TO_CHANNEL = {
     0: 14,
     1: 13,
     2: 12,
     3: 11,
     4:  9,
     5:  8,
     6:  7,
     7:  6,
     8: 10,
     9:  5,
    10:  4,
    11:  3,
    12:  2,
    13:  1,
}

POLL_HZ = 50          # button scan rate; debounce = two consecutive reads

# --- Fairy lights (non-addressable strands, PWM via 2N7000 MOSFET) ---
# Synced to the Pixelblaze day/night cycle by polling its exported `phase`
# var over WebSocket (read-only — the Pixelblaze keeps its own timing).
PIXELBLAZE_URL = "ws://10.42.0.50:81"   # Futurecast AP (was ws://192.168.1.49:81 on home Wi-Fi)
FAIRY_GPIO = 18            # MOSFET gate pin
FAIRY_PWM_HZ = 400
FAIRY_POLL_S = 2.0         # how often to ask the Pixelblaze for phase
FAIRY_TICK_S = 0.05        # LED update rate (smooths between polls)
FAIRY_SLEW_PER_S = 0.25    # max brightness change per second
FAIRY_MAX_BRIGHTNESS = 1.0 # cap if the strands are too bright at full

# Night window, in phase terms — matches the pattern keyframes
# (sunset 0.72, dusk 0.84, first light 0.12, sunrise 0.22):
FAIRY_FADE_UP_START = 0.80   # begin fading up (late sunset)
FAIRY_FADE_UP_END = 0.90     # fully on (nightfall)
FAIRY_FADE_DOWN_START = 0.08 # begin fading out (pre-dawn)
FAIRY_FADE_DOWN_END = 0.18   # fully off (early dawn)

# Audio format used for real tracks: prefer .ogg or .wav (reliable in pygame-ce).
# Avoid .mp3 (patchy support across builds).
