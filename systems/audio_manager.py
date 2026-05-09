"""Portable AudioManager template.

DROP-IN GUIDE
=============
1. Copy this file to ``systems/audio_manager.py`` in your new game.
2. Add an ``AudioSettings`` class to your ``settings.py`` matching the
   contract below. The manager only depends on these names:

       class AudioSettings:
           MUTE = False              # global kill switch (SFX + music)
           MUTE_MUSIC = False        # silence music while keeping SFX
           MUSIC_VOLUME = 1.0        # 0.0 - 1.0
           SFX_VOLUME = 1.0          # 0.0 - 1.0

           # Logical name -> filesystem path. Keys are what gameplay code
           # passes to ``AudioManager.play(name)``.
           SOUND_EFFECTS = {
               "jump":  "assets/audio/sound/jump.ogg",
               "hurt":  "assets/audio/sound/hurt.ogg",
           }

           # Background tracks; one is chosen at random each time music
           # starts, avoiding back-to-back repeats.
           MUSIC_TRACKS = [
               "assets/audio/music/level1.ogg",
           ]

3. Initialise the pygame mixer once at startup (typically in your
   GameManager.__init__) **before** constructing AudioManager:

       pygame.mixer.init()
       self.audio = AudioManager()

4. Trigger sounds from anywhere with one entry point:

       self.audio.play("jump")

5. Manage music with: ``play_random_music``, ``pause_music``,
   ``resume_music``, ``stop_music``, ``toggle_mute``.

DESIGN NOTES
============
- **Data-driven.** Adding a new sound is one line in settings; this file
  never changes per-project.
- **No reserved channels.** Pygame's default 8-channel pool is sufficient
  for casual SFX. If a specific cue MUST never be cut off, fetch a
  dedicated channel for it explicitly:

      pygame.mixer.set_num_channels(N+1)
      self._boss_channel = pygame.mixer.Channel(N)
      ...
      self._boss_channel.play(self.sounds["boss_death"])

  Add that opt-in only for sounds that genuinely need it.
- **Failure is non-fatal.** Missing files or an uninitialised mixer log
  a warning and silently skip; the game keeps running.
- **Mute is honored at the call site**, not by mutating each Sound's
  volume, so toggling mute is instant and reversible.
"""

import pygame
import random

from settings import AudioSettings


class AudioManager:
    """Data-driven music and sound-effect playback.

    All sounds are declared in ``AudioSettings.SOUND_EFFECTS`` (logical name
    -> file path). Gameplay code triggers them through ``play(name)``.
    """

    # ------------------------------------------------------------------
    # INIT
    # ------------------------------------------------------------------

    def __init__(self):
        """Load every registered sound effect and start background music."""
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        for name, path in AudioSettings.SOUND_EFFECTS.items():
            sound = self._load_sound(path)
            if sound is not None:
                sound.set_volume(AudioSettings.SFX_VOLUME)
                self.sounds[name] = sound

        # Track last played track so the same song never repeats back-to-back.
        self._last_music_track: str | None = None
        self._music_is_paused = False

        self.play_random_music()

    def _load_sound(self, path: str) -> pygame.mixer.Sound | None:
        """Load one sound from disk; return None if the asset or mixer is missing."""
        try:
            return pygame.mixer.Sound(path)
        except (pygame.error, FileNotFoundError) as error:
            print(f"Could not load sound {path}: {error}")
            return None

    # ------------------------------------------------------------------
    # SOUND EFFECTS
    # ------------------------------------------------------------------

    def play(self, name: str) -> None:
        """Play one registered sound effect by logical name.

        Args:
            name: Key from ``AudioSettings.SOUND_EFFECTS``.
        """
        if AudioSettings.MUTE:
            return
        sound = self.sounds.get(name)
        if sound is None:
            return
        sound.play()

    # ------------------------------------------------------------------
    # MUSIC
    # ------------------------------------------------------------------

    def play_random_music(self) -> None:
        """Pick a random track (avoiding the last one) and loop it indefinitely."""
        if AudioSettings.MUTE or AudioSettings.MUTE_MUSIC:
            return
        if not AudioSettings.MUSIC_TRACKS:
            return

        available = [t for t in AudioSettings.MUSIC_TRACKS if t != self._last_music_track]
        if not available:
            available = AudioSettings.MUSIC_TRACKS
        track = random.choice(available)
        self._last_music_track = track

        try:
            pygame.mixer.music.load(track)
            pygame.mixer.music.set_volume(AudioSettings.MUSIC_VOLUME)
            pygame.mixer.music.play(loops=-1)
            self._music_is_paused = False
        except pygame.error as error:
            print(f"Could not load music track {track}: {error}")

    def stop_music(self) -> None:
        """Stop the current background track."""
        pygame.mixer.music.stop()
        self._music_is_paused = False

    def pause_music(self) -> None:
        """Pause background music if anything is playing."""
        if AudioSettings.MUTE or AudioSettings.MUTE_MUSIC:
            return
        pygame.mixer.music.pause()
        self._music_is_paused = True

    def resume_music(self) -> None:
        """Resume paused music, or start a new random track if nothing is queued."""
        if AudioSettings.MUTE or AudioSettings.MUTE_MUSIC:
            return
        if self._music_is_paused:
            pygame.mixer.music.unpause()
            self._music_is_paused = False
            return
        self.play_random_music()

    # ------------------------------------------------------------------
    # GLOBAL CONTROLS
    # ------------------------------------------------------------------

    def toggle_mute(self, resume_music: bool = True) -> bool:
        """Flip the global mute flag and apply the side effects.

        Args:
            resume_music: When unmuting, whether to restart background music.

        Returns:
            bool: The new mute state (True = muted).
        """
        AudioSettings.MUTE = not AudioSettings.MUTE

        if AudioSettings.MUTE:
            pygame.mixer.stop()
            pygame.mixer.music.stop()
            self._music_is_paused = False
            return True

        if resume_music and not AudioSettings.MUTE_MUSIC:
            self.play_random_music()
        return False
