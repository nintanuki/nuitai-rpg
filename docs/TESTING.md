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

## Layer 3 — Overworld (Pass 1 scaffolding)

> Pass 1 only covers walking around the two placeholder cells. NPCs, encounters, dialogue triggers, sign tiles, warp tiles, real sprite art, footstep audio, and per-cell content are Pass 2.

22. From the title screen, `NEW GAME` drops the player into the overworld instead of the test room. The screen shows a centered 640×384 cell area filled with green floor tiles, a few darker rock-wall tiles, blue water tiles in the middle, and small sand patches; a yellow square sits at the center of the cell.
23. Arrow keys, WASD, the controller D-pad, and the controller left analog stick all move the yellow square one tile per direction, animating smoothly between tiles over about 150 ms.
24. Walking into a wall tile (the dark brown border or the water in the middle) does not move the square; the move attempt still counts as "facing" so the sprite turns toward the wall without translating.
25. Walking off the east edge at the middle row crosses into the second cell (`beach_east`); the water and sand patches are mirrored from the first cell and the square reappears at the west edge of the new cell. Walking off the west edge of the second cell returns to the first cell.
26. Walking against any other edge (north, south, or east of the second cell) does nothing — there is no neighbor cell at that coordinate.
27. The bottom of the screen reserves space for the message box; for Pass 1 it stays empty (renders nothing).
28. `Tab` on the keyboard or `START` on the controller opens the translucent system menu over the overworld. The overworld remains visible beneath the dimming overlay. `Resume` (or cancel) pops the menu and returns to the overworld with the square in the same tile it was in.
29. From the menu, `Save` writes `saves/slot_1.json`. Quit to title, then `Continue`: the title returns to the overworld with the party intact. (Restoring the player's exact tile within the cell is a Layer-0.5 follow-up — the live save schema still writes only the party.)
30. No `print()` output appears on the console while walking, transitioning, or opening the menu.

## Layer 3 — Overworld (Pass 2 first cut)

> Pass 2 adds random encounters, HP / potion persistence across battles and saves, and the PARTY / INVENTORY status screens. NPCs, dialogue triggers, sign tiles, warp tiles, real sprite art, and footstep audio are still outstanding.

31. Start a `NEW GAME`. Open the menu (`Tab` / `START`). PARTY and INVENTORY rows are now selectable (no longer gray). SETTINGS stays gray.
32. Pick PARTY. The screen shows three rows — Kailo, Hina, Tawiri — each line `<NAME>    HP <X> / <X>` (current matches max, since nothing has damaged anyone yet), then the element pair tinted in the element accent colors below. Cancel returns to the system menu.
33. Pick INVENTORY. The screen shows one row: `POTION    x5`. Cancel returns to the system menu.
34. Resume to the overworld. Walk around for a few steps. Roughly every 5–10 steps an encounter should fire — the screen swaps to `BattleScene` with one of the placeholder enemies. (The expected average is ~9 steps with the Pass-2 default `EncounterSettings.RATE_PER_STEP = 0.20`.)
35. Fight: attack the enemy. Watch some HP come off your party. Take some damage. Eventually you should either kill the enemy or flee.
36. When the battle ends and the text drains, the scene pops back to the overworld and your yellow square is exactly where it was when the encounter triggered.
37. Open the menu → PARTY. The damaged member's `<X> / <max>` row should show the damage (current < max). KO'd members render in red.
38. If you used a potion: open the menu → INVENTORY. The potion count should be 4 (or whatever you ended with), not 5.
39. Take more damage in another encounter to confirm HP keeps accumulating across fights.
40. Save the game (menu → SAVE). Quit to title. `CONTINUE`. Open the menu → PARTY: HP for each member matches what was on screen before save. → INVENTORY: potion count matches.
41. No `print()` output appears on the console at any point.

### Known rough edges (Pass 2)

- Save gives no on-screen feedback — the row plays the menu-select sound and writes `saves/slot_1.json` silently. A "GAME SAVED." message is queued for a follow-up.
- `Continue` does not restore the overworld scene's tile position — the party + inventory load correctly, but the player respawns at cell centre. The full scene-stack-in-save path is the existing Layer-0.5 deferral.
- A wipe (all party HP at 0) currently leaves everyone at 0 HP after the battle pops; the floor-at-1 protection in `combatant_from_party_member` lets the next encounter still happen but at minimum HP. Proper game-over / save-point retreat is Layer 1.
- Encounter rate `0.20` is tuned for testing — production will likely sit closer to `0.08`.

## Sign-off

- [ ] Smoke + globals all passed.
- [ ] [docs/CHANGELOG.md](CHANGELOG.md) updated.
- [ ] [docs/ARCHITECTURE.md](ARCHITECTURE.md) updated if structure changed.
- [ ] [docs/TODO.md](TODO.md) updated if a roadmap item was completed.
