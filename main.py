"""
Futurecast audio — keyboard test harness.

Runs the AudioEngine with a small on-screen status window so you can bench-test
the whole audio model before the GPIO buttons are wired:

  keys 1-9, 0, then q w e r  -> channels 1..14
  + / =                      -> volume up
  - / _                      -> volume down
  ESC                        -> quit

Later, the GPIO button service will call engine.trigger(channel_id),
engine.volume_up(), engine.volume_down() instead of these key events —
the engine itself doesn't change.
"""

import pygame

import config
from audio_engine import AudioEngine

# Map test-harness keys -> channel_id (1..14)
KEY_TO_CHANNEL = {
    pygame.K_1: 1, pygame.K_2: 2, pygame.K_3: 3, pygame.K_4: 4, pygame.K_5: 5,
    pygame.K_6: 6, pygame.K_7: 7, pygame.K_8: 8, pygame.K_9: 9, pygame.K_0: 10,
    pygame.K_q: 11, pygame.K_w: 12, pygame.K_e: 13, pygame.K_r: 14,
}
VOL_UP_KEYS = {pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS}
VOL_DOWN_KEYS = {pygame.K_MINUS, pygame.K_UNDERSCORE, pygame.K_KP_MINUS}


def main():
    pygame.init()
    screen = pygame.display.set_mode((520, 300))
    pygame.display.set_caption("Futurecast audio — test harness")
    font = pygame.font.SysFont("monospace", 16)
    big = pygame.font.SysFont("monospace", 22, bold=True)
    clock = pygame.time.Clock()

    engine = AudioEngine(config.AMBIENCE, config.CHANNELS)
    engine.start_ambience()

    last_channel = None
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in KEY_TO_CHANNEL:
                    cid = KEY_TO_CHANNEL[event.key]
                    if engine.trigger(cid):
                        last_channel = cid
                elif event.key in VOL_UP_KEYS:
                    engine.volume_up()
                elif event.key in VOL_DOWN_KEYS:
                    engine.volume_down()

        engine.update()

        # --- draw status ---
        screen.fill((18, 18, 24))
        lines = [
            (big, f"Futurecast audio", (235, 235, 245)),
            (font, "", None),
            (font, f"ambience: looping", (150, 200, 150)),
            (font, f"track playing: {'YES ch %02d' % last_channel if engine.track_playing else 'no (idle)'}",
             (230, 200, 120) if engine.track_playing else (120, 140, 160)),
            (font, f"master volume: {int(engine.master_volume * 100):3d}%", (180, 180, 220)),
            (font, "", None),
            (font, "keys 1-9 0 q w e r = channels 1..14", (150, 150, 165)),
            (font, "+ / - = volume    ESC = quit", (150, 150, 165)),
        ]
        y = 20
        for f, text, color in lines:
            if text:
                screen.blit(f.render(text, True, color), (24, y))
            y += 30
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
