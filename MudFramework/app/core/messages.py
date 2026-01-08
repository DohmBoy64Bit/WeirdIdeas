"""
Standardized game messages and error messages.
Centralized location for all user-facing text.
"""

class GameMessages:
    """Standardized game messages."""
    
    # Command Errors
    UNKNOWN_COMMAND = "Unknown command."
    COMMAND_TOO_LONG = "Command too long. Maximum length is {max_length} characters."
    
    # Movement
    CANNOT_MOVE = "You cannot go that way."
    MOVED = "You move {direction}..."
    LOST_IN_VOID = "You were lost in the void and returned to reality."
    
    # Combat
    IN_COMBAT = "You are in combat! Valid commands: attack, flee, use, skill"
    NOTHING_TO_HUNT = "There is nothing to hunt here."
    FOUND_MOB = "You found a {mob_name}! Combat started!"
    FLEE_SUCCESS = "You fled successfully!"
    FLEE_FAILED = "Failed to flee!"
    FATAL_DAMAGE = "You took fatal damage! Reviving at start with {hp} HP."
    
    # Inventory
    INVENTORY_EMPTY = "Inventory is empty."
    ITEM_NOT_FOUND = "You don't have that item."
    ITEM_ALREADY_FULL_HP = "Your Health is already full!"
    ITEM_ALREADY_FULL_FLUX = "Your Flux is already full!"
    ITEM_USED = "You used {item_name} and recovered {amount} HP."
    CANNOT_USE_ITEM = "You cannot use that."
    EQUIPMENT_NOT_IMPLEMENTED = "You cannot equip items yet (Coming Soon)."
    
    # Shop
    NO_SHOP_HERE = "There is no shop here."
    SHOP_EMPTY = "This shop is empty."
    ITEM_NOT_SOLD = "That item is not sold here."
    CANNOT_AFFORD = "You cannot afford that."
    ITEM_PURCHASED = "You bought {item_name} for {price} Credits."
    
    # Skills
    SKILLS_ONLY_IN_COMBAT = "You can only use skills in combat!"
    SKILL_USAGE = "Usage: skill <skill_name>"
    SKILL_UNKNOWN = "Unknown skill '{skill_name}'."
    SKILL_NOT_LEARNED = "You haven't learned {skill_name} yet."
    SKILL_ON_COOLDOWN = "{skill_name} is on cooldown! {remaining} rounds remaining."
    SKILL_INSUFFICIENT_FLUX = "Not enough Flux! Need {required}, have {current}."
    SKILL_READY = "{skill_name} is ready!"
    
    # Transformations
    CANNOT_TRANSFORM = "You cannot transform into that."
    TRANSFORMED = "You scream in power and transform into {form}!"
    POWER_MULTIPLIED = "Your power has multiplied!"
    
    # Quests
    NO_ACTIVE_QUESTS = "No active quests."
    QUEST_STARTED = "Quest Started! Check 'quests' for details."
    QUEST_COMPLETED = "Quest Completed! Received: {rewards}"
    QUEST_UPDATE = "Quest Update: {title} ({progress}/{count})"
    NO_ONE_TO_TALK = "There is no one here to talk to."
    
    # Wish Command
    MISSING_SHARDS = "You do not have all 7 Cosmic Shards."
    SHARDS_RESONATE = "The shards resonate... a rift opens in reality..."
    ARCHON_SUMMONED = "THE ARCHON has been summoned by a powerful traveler!"
    ARCHON_AWAKENED = "ARCHON: 'YOU HAVE AWAKENED ME. STATE YOUR DESIRE.'"
    ARCHON_DONE = "ARCHON: 'IT IS DONE.' (The shards dissipate into the void)."
    LEVELS_GAINED = "You have gained {levels} levels! (Level {old} -> {new})"
    
    # Level Up
    LEVEL_UP = "LEVEL UP! You are now level {level}!"
    LEVEL_UP_BROADCAST = "{name} has reached Level {level}!"
    SKILLS_LEARNED = "Learned new skills: {skills}"
    SKILLS_LEARNED_BROADCAST = "{name} learned {skills}!"
    
    # Experience
    EXP_GAINED = "You gained {exp} EXP."
    
    # Loot
    LOOT_DROPPED = "Loot dropped: {items}"
    
    # Battle Hardened (Zenkai)
    BATTLE_HARDENED = "[Battle Hardened] STR bonus: +{bonus}%!"
    
    # Flux
    FLUX_REGEN = "⚡ Regenerated {regen} Flux ({current}/{max})"
    FLUX_USED = "⚡ Used {cost} Flux ({current}/{max} remaining)"
    
    # System
    NEURAL_LINK_ESTABLISHED = "Neural Link Established."
    CONNECTION_LOST = "Connection Lost. Retrying..."

