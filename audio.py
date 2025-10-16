"""Audio helpers for Rat Race.

Thin wrapper(s) around pygame mixer for sound effects and music.
"""

import pygame

class SoundManager:
    def __init__(self):
        self.sounds = {}
        self.enabled = False
        self.volume = 0.6
        try:
            # Ensure mixer is initialized with sensible defaults (mono to match our buffers)
            self._ensure_mixer()
            pygame.mixer.set_num_channels(8)
            self.create_sound_effects()
            self.enabled = True
        except Exception as e:
            print(f"Sound system disabled: {e}")
            self.enabled = False

    def create_sound_effects(self):
        try:
            self.sounds['coin'] = self.create_simple_sound(880, 0.1)
            self.sounds['bark'] = self.create_bark_sound()
            self.sounds['enemy_kill'] = self.sounds['bark']
            self.sounds['jump'] = self.create_simple_sound(700, 0.09)
            self.sounds['hit'] = self.create_simple_sound(180, 0.18)
            for sound in self.sounds.values():
                sound.set_volume(self.volume)
        except Exception as e:
            print(f"Could not create sound effects: {e}")
            self.enabled = False

    def _ensure_mixer(self):
        """Initialize pygame mixer if not already initialized, with fallbacks."""
        if pygame.mixer.get_init():
            return
        attempts = [
            {"frequency": 22050, "channels": 1, "buffer": 512},
            {"frequency": 44100, "channels": 1, "buffer": 512},
            {"frequency": 22050, "channels": 2, "buffer": 512},
        ]
        last_error = None
        for cfg in attempts:
            try:
                pygame.mixer.init(frequency=cfg["frequency"], size=-16, channels=cfg["channels"], buffer=cfg["buffer"])
                return
            except Exception as e:
                last_error = e
        # Re-raise the last error if all attempts failed
        raise last_error if last_error else RuntimeError("Unknown mixer init error")

    def create_simple_sound(self, frequency, duration):
        try:
            sample_rate = 22050
            frames = int(duration * sample_rate)
            import math
            wave_data = []
            for i in range(frames):
                t = float(i) / sample_rate
                wave = math.sin(2 * math.pi * frequency * t)
                envelope = max(0, 1 - (i / frames))
                sample = int(wave * envelope * 12000)
                wave_data.extend([sample & 0xFF, (sample >> 8) & 0xFF])
            buffer = bytes(wave_data)
            return pygame.mixer.Sound(buffer=buffer)
        except Exception as e:
            print(f"Could not create simple sound: {e}")
            return pygame.mixer.Sound(buffer=b'\x00\x00' * 1000)

    def create_bark_sound(self):
        try:
            sample_rate = 22050
            import math
            data = []
            for base_freq, dur in [(550, 0.06), (450, 0.08)]:
                frames = int(dur * sample_rate)
                for i in range(frames):
                    t = float(i) / sample_rate
                    freq = base_freq * (1 - 0.6 * (i / frames))
                    wave = math.sin(2 * math.pi * freq * t)
                    square = 1.0 if wave >= 0 else -1.0
                    mixed = 0.6 * wave + 0.4 * square
                    env = 1.0
                    if i < frames * 0.1:
                        env = i / (frames * 0.1)
                    elif i > frames * 0.85:
                        env = max(0, 1 - (i - frames * 0.85) / (frames * 0.15))
                    sample = int(max(-1, min(1, mixed * env)) * 12000)
                    data.extend([sample & 0xFF, (sample >> 8) & 0xFF])
                data.extend([0, 0] * int(0.02 * sample_rate))
            return pygame.mixer.Sound(buffer=bytes(data))
        except Exception as e:
            print(f"Could not create bark sound: {e}")
            return self.create_simple_sound(500, 0.1)

    def set_volume(self, volume):
        self.volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.volume)

    def play(self, sound_name):
        if self.enabled and sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except Exception as e:
                print(f"Could not play sound {sound_name}: {e}")


