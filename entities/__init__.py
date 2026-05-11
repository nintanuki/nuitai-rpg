"""Entities — sprites and actors that move through the game's scenes.

Currently houses the overworld leader sprite. As the game grows this
package will hold NPC sprites, ship sprites, party-follower sprites,
and any other on-screen actor that has a position, a facing, and an
update loop of its own. Battle-side combatants stay under
[systems/battle.py](../systems/battle.py); this package is for
pixel-space actors.
"""
