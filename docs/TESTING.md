# Pygame Template — Manual Testing Checklist

Run after a non-trivial change.

```powershell
cd pygame-template-files
python main.py
```

## Smoke

1. Boot: window opens at the resolution defined by `ScreenSettings.RESOLUTION`, no console errors.
2. The title bar shows `ScreenSettings.WINDOW_TITLE`.
3. The background is `ColorSettings.BG_COLOR`.
4. The CRT overlay is visible (scanlines + slight flicker).

## Globals

5. `F11` toggles fullscreen. CRT overlay disappears in fullscreen, reappears in windowed.
6. `Esc` exits cleanly.
7. With a controller connected: `BACK` toggles fullscreen.
8. With a controller connected: holding `START + SELECT + L1 + R1` exits cleanly.
9. Closing the OS window via the title-bar `X` exits cleanly.

## Audio

10. Boot logs no `Could not load sound` lines as long as `AudioSettings.SOUND_EFFECTS` and `MUSIC_TRACKS` either are empty or all referenced files exist.
11. With a sound registered in `SOUND_EFFECTS` and triggered from `_update_world` or a handler, calling `self.audio.play("name")` plays it; missing keys are silently ignored.
12. With a music track in `MUSIC_TRACKS`, looping playback starts on boot. `pause_music`, `resume_music`, and `stop_music` behave as advertised. `toggle_mute()` cuts everything (SFX and music) and restoring the mute restarts a random track.

## Layer 0 — engine spike

13. Title screen shows the game title and a menu of `NEW GAME`, `CONTINUE`, `LOAD GAME`, `QUIT`. All text is ALL-CAPS regardless of the source string casing.
14. With no save on disk, `CONTINUE` and `LOAD GAME` are dimmed and not selectable. The cursor skips them on Up/Down.
15. Picking `NEW GAME` enters the test room. The party roster appears in the upper-right corner.
16. Picking `TALK` opens a bordered text box at the bottom that types its line out at the configured chars-per-second; pressing confirm again advances or fast-forwards.
17. Picking `FIGHT` enters the battle scene. Party HP and enemy HP are visible. Pressing confirm steps through narration; the battle resolves to victory, defeat, or — on cancel — flee, then returns to the test room.
18. Picking `SAVE` writes `saves/slot_1.json` and the `Saved.` line appears in the box.
19. Picking `QUIT TO TITLE` returns to the title screen, and `CONTINUE` is now enabled.
20. Picking `CONTINUE` restores the previously-saved party (same names appear in the roster).
21. No `print()` output appears on the console at any point during gameplay.

## Sign-off

- [ ] Smoke + globals all passed.
- [ ] [docs/CHANGELOG.md](CHANGELOG.md) updated.
- [ ] [docs/ARCHITECTURE.md](ARCHITECTURE.md) updated if structure changed.
- [ ] [docs/TODO.md](TODO.md) updated if a roadmap item was completed.
