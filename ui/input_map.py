"""Shared input helpers for scenes.

Centralises the mapping from raw pygame events to logical UI actions
(``confirm``, ``cancel``, ``up``, ``down``, ``left``, ``right``) so each
scene doesn't reimplement the keyboard + controller routing.
"""

from __future__ import annotations

import pygame

from settings import InputSettings


CONFIRM_KEYS = (pygame.K_RETURN, pygame.K_z, pygame.K_SPACE)
CANCEL_KEYS = (pygame.K_BACKSPACE, pygame.K_x)
UP_KEYS = (pygame.K_UP, pygame.K_w)
DOWN_KEYS = (pygame.K_DOWN, pygame.K_s)
LEFT_KEYS = (pygame.K_LEFT, pygame.K_a)
RIGHT_KEYS = (pygame.K_RIGHT, pygame.K_d)


def is_confirm(event: pygame.event.Event) -> bool:
    """Return True if ``event`` is a confirm press (Enter / Z / Space / A button)."""
    if event.type == pygame.KEYDOWN and event.key in CONFIRM_KEYS:
        return True
    if event.type == pygame.JOYBUTTONDOWN and event.button in (
        InputSettings.JOY_BUTTON_A,
        InputSettings.JOY_BUTTON_START,
    ):
        return True
    return False


def is_cancel(event: pygame.event.Event) -> bool:
    """Return True if ``event`` is a cancel press (Backspace / X / B button)."""
    if event.type == pygame.KEYDOWN and event.key in CANCEL_KEYS:
        return True
    if event.type == pygame.JOYBUTTONDOWN and event.button == InputSettings.JOY_BUTTON_B:
        return True
    return False


def is_up(event: pygame.event.Event) -> bool:
    """Return True for an up press (arrow / WASD / D-pad up / left-stick up)."""
    if event.type == pygame.KEYDOWN and event.key in UP_KEYS:
        return True
    if event.type == pygame.JOYHATMOTION and event.value[1] > 0:
        return True
    if event.type == pygame.JOYAXISMOTION and event.axis == InputSettings.JOY_AXIS_LEFT_Y:
        if event.value < -InputSettings.JOY_TRIGGER_THRESHOLD:
            return True
    return False


def is_down(event: pygame.event.Event) -> bool:
    """Return True for a down press."""
    if event.type == pygame.KEYDOWN and event.key in DOWN_KEYS:
        return True
    if event.type == pygame.JOYHATMOTION and event.value[1] < 0:
        return True
    if event.type == pygame.JOYAXISMOTION and event.axis == InputSettings.JOY_AXIS_LEFT_Y:
        if event.value > InputSettings.JOY_TRIGGER_THRESHOLD:
            return True
    return False
