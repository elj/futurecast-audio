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

# Audio format used for real tracks: prefer .ogg or .wav (reliable in pygame-ce).
# Avoid .mp3 (patchy support across builds).
