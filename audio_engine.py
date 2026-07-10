"""
AudioEngine — the core playback model for Futurecast.

Design (from the project spec):
  - A background *ambience* bed loops forever.
  - Pressing a channel button plays that channel's track ONCE, layered on top.
  - When the track finishes, we're back to just ambience (idle state).
  - Two volume buttons nudge a master level up/down, but never fully mute.

Implementation notes:
  - Ambience uses pygame.mixer.music (its own streaming channel).
  - Channel tracks are pygame.mixer.Sound objects played on ONE reserved
    channel, so a new press cleanly interrupts the previous one-shot.
  - Ducking (lowering ambience while a track plays) is an instant volume
    change, not a fade — kept deliberately simple.

Nothing here knows about buttons or GPIO; feed it channel IDs from anywhere
(keyboard test harness now, GPIO later).
"""

import pygame

import config


class AudioEngine:
    def __init__(self, ambience_path, channel_paths,
                 master_volume=config.MASTER_VOLUME, duck=config.DUCK):
        # Low latency-ish mixer setup; init BEFORE loading any sound.
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mixer.init()

        # Reserve channel 0 exclusively for one-shot channel tracks.
        pygame.mixer.set_num_channels(8)
        pygame.mixer.set_reserved(1)
        self._oneshot = pygame.mixer.Channel(0)

        self.master_volume = float(master_volume)
        self.duck = float(duck)

        self._ambience_path = str(ambience_path)
        self._sounds = {cid: pygame.mixer.Sound(str(p))
                        for cid, p in channel_paths.items()}

        self._ducking = False  # True while a track is playing and ambience is lowered

    # --- lifecycle ---------------------------------------------------------
    def start_ambience(self):
        """Load and loop the ambience bed forever."""
        pygame.mixer.music.load(self._ambience_path)
        pygame.mixer.music.set_volume(self._ambience_level())
        pygame.mixer.music.play(loops=-1)

    def update(self):
        """Call once per frame. Restores ambience level when a track ends."""
        if self._ducking and not self._oneshot.get_busy():
            self._ducking = False
            pygame.mixer.music.set_volume(self._ambience_level())

    # --- interaction -------------------------------------------------------
    def trigger(self, channel_id):
        """Play a channel's track once. Interrupts any track already playing."""
        snd = self._sounds.get(channel_id)
        if snd is None:
            return False
        snd.set_volume(self.master_volume)
        self._oneshot.play(snd)  # replaces whatever was on the reserved channel
        if self.duck < 1.0:
            self._ducking = True
            pygame.mixer.music.set_volume(self._ambience_level(ducked=True))
        return True

    def volume_up(self):
        self._set_master(self.master_volume + config.VOLUME_STEP)

    def volume_down(self):
        self._set_master(self.master_volume - config.VOLUME_STEP)

    # --- state (handy for a status display / debugging) --------------------
    @property
    def track_playing(self):
        return self._oneshot.get_busy()

    # --- internals ---------------------------------------------------------
    def _set_master(self, value):
        self.master_volume = max(config.VOLUME_FLOOR, min(config.VOLUME_CEIL, value))
        pygame.mixer.music.set_volume(self._ambience_level(ducked=self._ducking))
        # currently-playing one-shot follows the new master level too
        self._oneshot.set_volume(self.master_volume)

    def _ambience_level(self, ducked=False):
        lvl = self.master_volume
        if ducked and self.duck < 1.0:
            lvl *= self.duck
        return lvl
