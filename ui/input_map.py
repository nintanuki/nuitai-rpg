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
# Keys that open the system / pause menu from gameplay scenes. Enter is
# included alongside Tab so the keyboard mirrors the controller, where
# both START and Y open the menu — pressing Enter in the overworld
# either advances any active text first, then opens the menu the next
# time it is pressed.
MENU_KEYS = (pygame.K_TAB, pygame.K_RETURN)

# Controller buttons that confirm a menu choice. ``START`` is included
# so the title screen can be entered with the most natural "start"
# gesture on a gamepad; the same button also functions as a menu-open
# in gameplay scenes (see ``is_menu``), and the two callers are
# state-disjoint so the overlap is harmless.
_CONFIRM_BUTTONS = (
    InputSettings.JOY_BUTTON_A,
    InputSettings.JOY_BUTTON_START,
)

# Controller buttons that open the system / pause menu. Y was added
# alongside START so players can reach the menu without taking their
# thumb off the face buttons. Tab and Enter on the keyboard map to the
# same logical action.
_MENU_BUTTONS = (
    InputSettings.JOY_BUTTON_START,
    InputSettings.JOY_BUTTON_Y,
)


def is_confirm(event: pygame.event.Event) -> bool:
    """Return True if ``event`` is a confirm press (Enter / Z / Space / A / Start)."""
    if event.type == pygame.KEYDOWN and event.key in CONFIRM_KEYS:
        return True
    if event.type == pygame.JOYBUTTONDOWN and event.button in _CONFIRM_BUTTONS:
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


def is_left(event: pygame.event.Event) -> bool:
    """Return True for a left press (arrow / A / D-pad left / left-stick left)."""
    if event.type == pygame.KEYDOWN and event.key in LEFT_KEYS:
        return True
    if event.type == pygame.JOYHATMOTION and event.value[0] < 0:
        return True
    if event.type == pygame.JOYAXISMOTION and event.axis == InputSettings.JOY_AXIS_LEFT_X:
        if event.value < -InputSettings.JOY_TRIGGER_THRESHOLD:
            return True
    return False


def is_right(event: pygame.event.Event) -> bool:
    """Return True for a right press (arrow / D / D-pad right / left-stick right)."""
    if event.type == pygame.KEYDOWN and event.key in RIGHT_KEYS:
        return True
    if event.type == pygame.JOYHATMOTION and event.value[0] > 0:
        return True
    if event.type == pygame.JOYAXISMOTION and event.axis == InputSettings.JOY_AXIS_LEFT_X:
        if event.value > InputSettings.JOY_TRIGGER_THRESHOLD:
            return True
    return False


def is_menu(event: pygame.event.Event) -> bool:
    """Return True for the system-menu open press (Tab / Enter / START / Y)."""
    if event.type == pygame.KEYDOWN and event.key in MENU_KEYS:
        return True
    if event.type == pygame.JOYBUTTONDOWN and event.button in _MENU_BUTTONS:
        return True
    return False


def read_held_direction(joysticks) -> tuple[int, int]:
    """Return the currently-held cardinal direction as ``(dx, dy)``.

    Polls keyboard state and every connected joystick's D-pad and left
    analog stick. Each axis is clamped to one of ``-1``, ``0``, ``+1``;
    diagonals are returned as-is and the caller decides how to resolve
    them (the overworld player prefers horizontal when both are held).

    Args:
        joysticks: Iterable of connected ``pygame.joystick.Joystick``
            instances, normally ``GameManager.connected_joysticks``.

    Returns:
        A ``(dx, dy)`` tuple in ``{-1, 0, +1} x {-1, 0, +1}`` where
        ``dx`` is east-positive and ``dy`` is south-positive.
    """
    dx = 0
    dy = 0
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        dx -= 1
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        dx += 1
    if keys[pygame.K_UP] or keys[pygame.K_w]:
        dy -= 1
    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        dy += 1
    threshold = InputSettings.JOY_TRIGGER_THRESHOLD
    for joystick in joysticks:
        # D-pad: pygame hats use screen-inverted Y (up = +1).
        try:
            if joystick.get_numhats() > 0:
                hx, hy = joystick.get_hat(0)
                dx += hx
                dy -= hy
        except pygame.error:
            pass
        # Left analog stick.
        try:
            ax = joystick.get_axis(InputSettings.JOY_AXIS_LEFT_X)
            ay = joystick.get_axis(InputSettings.JOY_AXIS_LEFT_Y)
        except pygame.error:
            ax = 0.0
            ay = 0.0
        if ax < -threshold:
            dx -= 1
        elif ax > threshold:
            dx += 1
        if ay < -threshold:
            dy -= 1
        elif ay > threshold:
            dy += 1
    # Clamp so multiple sources holding the same direction don't stack.
    if dx > 1:
        dx = 1
    elif dx < -1:
        dx = -1
    if dy > 1:
        dy = 1
    elif dy < -1:
        dy = -1
    return dx, dy
