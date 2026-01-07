from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from app.models.player import Player
from app.game.world import world
from app.game.transformations import get_transformation, get_available_transformations, calculate_effective_stats
from app.models.race import Race
from app.game.quest_manager import quest_manager
from app.game.combat import CombatSystem, Mob
from app.game.inventory_manager import inventory_manager
from app.game.skills_manager import skills_manager
import random
import copy

class GameEngine:
    def __init__(self, connection_manager):
        self.manager = connection_manager
        self.combat_system = CombatSystem(self.manager)
        self.active_mobs = {} 

    async def process_command(self, player_id: int, command: str, db: Session):
        player = db.query(Player).filter(Player.id == player_id).first()
        if not player:
            return

        cmd = command.strip().split()
        if not cmd:
            return
        
        verb = cmd[0].lower()
        args = cmd[1:]

        # COMBAT HANDLING
        if player.combat_state:
            if verb in ["attack", "a"]:
                await self.cmd_attack_round(player, db)
            elif verb in ["flee", "run"]:
                await self.cmd_flee(player, db)
            elif verb in ["use", "item"]: 
                await self.cmd_use(player, " ".join(args), db)
            elif verb in ["skill", "sk"]:
                await self.cmd_use_skill(player, " ".join(args), db)
            else:
                await self.msg_system(player.id, "You are in combat! Valid commands: attack, flee, use, skill")
            return

        # NORMAL HANDLING
        if verb in ["look", "l"]:
            await self.cmd_look(player, args)
        if verb in ["north", "south", "east", "west", "up", "down", "n", "s", "e", "w", "u", "d", "enter", "exit"]:
            await self.cmd_move(player, verb, db)
        elif verb == "move":
            if args:
                await self.cmd_move(player, args[0], db)
        elif verb == "say":
            await self.cmd_say(player, " ".join(args))
        elif verb == "hunt":
            await self.cmd_hunt(player, db)
        elif verb == "transform":
            await self.cmd_transform(player, " ".join(args), db)
        elif verb == "revert":
            await self.cmd_revert(player, db)
        elif verb in ["inventory", "i", "inv"]:
            await self.cmd_inventory(player)
        elif verb in ["buy", "shop"]:
            await self.cmd_buy(player, " ".join(args), db)
        elif verb == "use":
            await self.cmd_use(player, " ".join(args), db)
        elif verb == "talk":
            await self.cmd_talk(player, " ".join(args), db)
        elif verb in ["quests", "q"]:
            await self.cmd_quests(player)
        elif verb == "wish":
            await self.cmd_wish(player, db)
        elif verb in ["skills", "sk"]:
            await self.cmd_skills(player, db)
        elif verb in ["skillinfo", "si"]:
            await self.cmd_skill_info(player, " ".join(args), db)
        elif verb == "passive":
            await self.cmd_passive(player)
        elif verb == "cheat_shards":
             # Dev Helper
             inv = list(player.inventory) if player.inventory else []
             for i in range(1, 8):
                 inv.append({"item_id": f"cosmic_shard_{i}", "qty": 1})
             player.inventory = inv
             flag_modified(player, "inventory")
             db.commit()
             await self.msg_system(player.id, "Cheater! You have the Shards.")
        elif verb == "cheat_exp":
             try:
                 amount = int(args[0])
                 await self.grant_exp(player, amount, db)
                 await self.msg_system(player.id, f"Cheater! Gained {amount} EXP.")
             except:
                 await self.msg_system(player.id, "Usage: cheat_exp <amount>")
        elif verb == "cheat_item":
             try:
                 i_id = args[0]
                 item = inventory_manager.get_item(i_id)
                 if item:
                     inv = list(player.inventory) if player.inventory else []
                     found = False
                     for slot in inv:
                         if slot["item_id"] == i_id:
                             slot["qty"] += 1
                             found = True
                             break
                     if not found:
                         inv.append({"item_id": i_id, "qty": 1})
                     player.inventory = inv
                     flag_modified(player, "inventory")
                     db.commit()
                     await self.msg_system(player.id, f"Cheater! Obtained {item.name}.")
                 else:
                     await self.msg_system(player.id, "Invalid Item ID.")
             except:
                 await self.msg_system(player.id, "Usage: cheat_item <item_id>")
        else:
            await self.msg_system(player.id, "Unknown command.")

    async def cmd_transform(self, player: Player, form_name: str, db: Session):
        avail = get_available_transformations(player.race, player.level)
        if not form_name:
             await self.msg_system(player.id, f"Available forms: {', '.join(avail)}")
             return

        target_form = None
        for f in avail:
            if f.lower() == form_name.lower():
                target_form = f
                break
        
        if target_form:
            player.transformation = target_form
            db.commit()
            await self.msg_system(player.id, f"You scream in power and transform into {target_form}!")
            await self.manager.send_personal_message({
                 "type": "chat", "sender": "System", "content": "Your power has multiplied!", "channel": "channel-info"
            }, player.id)
        else:
            await self.msg_system(player.id, "You cannot transform into that.")

    async def cmd_hunt(self, player: Player, db: Session):
        room = world.get_room(player.current_map)
        if not room: 
             # Auto-fix
            start_room = world.get_start_room()
            player.current_map = start_room.id
            db.commit()
            room = start_room
            await self.msg_system(player.id, "You were lost in the void and returned to reality.")

        if not room.mobs:
            await self.msg_system(player.id, "There is nothing to hunt here.")
            return

        mob_id = random.choice(room.mobs)
        mob = self.combat_system.spawn_mob(mob_id)
        
        if mob:
            player.combat_state = {"mob_id": mob.id, "hp": mob.stats["hp"], "max_hp": mob.stats["max_hp"]}
            flag_modified(player, "combat_state")
            
            if "hp" not in player.stats:
                 player.stats["hp"] = player.stats["vit"] * 10
                 player.stats["max_hp"] = player.stats["vit"] * 10
                 flag_modified(player, "stats")
            
            db.commit()
            self.active_mobs[player.id] = mob
            
            await self.msg_system(player.id, f"You found a {mob.name}! Combat started!")
            await self.manager.send_personal_message({
                 "type": "chat", "sender": "Combat", "content": f"{mob.name} engages you!", "channel": "channel-combat"
            }, player.id)
        else:
            await self.msg_system(player.id, "You found nothing (Error spawning mob).")

    async def cmd_attack_round(self, player: Player, db: Session):
        mob = self.active_mobs.get(player.id)
        if not mob and player.combat_state:
             mob = self.combat_system.spawn_mob(player.combat_state["mob_id"])
             mob.stats["hp"] = player.combat_state["hp"]
             self.active_mobs[player.id] = mob

        if not mob:
            player.combat_state = None
            db.commit()
            return

        eff_stats = calculate_effective_stats(player.stats, player.transformation)
        
        class TempPlayer:
            def __init__(self, stats): self.stats = stats
        
        temp_player = TempPlayer(eff_stats)

        outcome = await self.combat_system.combat_round(temp_player, mob, "attack")
        
        for line in outcome["log"]:
             await self.manager.send_personal_message({
                 "type": "chat", "sender": "Combat", "content": line, "channel": "channel-combat"
            }, player.id)

        if outcome["status"] == "win":
            await self.grant_exp(player, outcome["exp"], db)
            
            logs = [f"You gained {outcome['exp']} EXP."]
            
            # Zenkai: Battle Hardened - +5% STR per win (max 50%)
            if player.race == "Zenkai":
                battle_bonus = player.stats.get("battle_hardened_bonus", 0)
                if battle_bonus < 50:
                    battle_bonus = min(50, battle_bonus + 5)
                    player.stats["battle_hardened_bonus"] = battle_bonus
                    flag_modified(player, "stats")
                    logs.append(f"[Battle Hardened] STR bonus: +{battle_bonus}%!")
            
            # LOOT HANDLING
            if "loot" in outcome and outcome["loot"]:
                inv = list(player.inventory) if player.inventory else []
                new_items = []
                for item_id in outcome["loot"]:
                    item = inventory_manager.get_item(item_id)
                    if item:
                        found = False
                        for slot in inv:
                            if slot["item_id"] == item_id:
                                slot["qty"] += 1
                                found = True
                                break
                        if not found:
                            inv.append({"item_id": item_id, "qty": 1})
                        new_items.append(item.name)
                
                if new_items:
                    player.inventory = inv
                    flag_modified(player, "inventory")
                    logs.append(f"Loot dropped: {', '.join(new_items)}")

            # QUEST HOOK: KILL UPDATE
            mob_id = player.combat_state["mob_id"]
            updated_quests = False

            if player.active_quests:
                active = copy.deepcopy(player.active_quests)
                
                for q_id, progress in active.items():
                    quest = quest_manager.get_quest(q_id)
                    if not quest: continue
                    
                    if quest["type"] == "kill" and quest["target"] == mob_id:
                        if progress["progress"] < quest["count"]:
                            progress["progress"] += 1
                            updated_quests = True
                            logs.append(f"Quest Update: {quest['title']} ({progress['progress']}/{quest['count']})")
                
                if updated_quests:
                     player.active_quests = active
                     flag_modified(player, "active_quests")

            await self.msg_system(player.id, " ".join(logs))
            
            # Restore flux to max when combat ends
            player.stats["flux"] = player.stats.get("max_flux", 100)
            
            player.combat_state = None
            if player.id in self.active_mobs: del self.active_mobs[player.id]
            db.commit()
            
        elif outcome["status"] == "loss":
            player.combat_state = None
            if player.id in self.active_mobs: del self.active_mobs[player.id]
            player.stats["hp"] = int(player.stats["max_hp"] * 0.5)
            player.stats["flux"] = player.stats.get("max_flux", 100)  # Restore flux on revival
            
            # Zenkai: Reset Battle Hardened bonus on death
            if player.race == "Zenkai" and "battle_hardened_bonus" in player.stats:
                player.stats["battle_hardened_bonus"] = 0
                
            flag_modified(player, "stats")
            player.current_map = "start_area"
            player.transformation = "Base"
            db.commit()
            await self.msg_system(player.id, f"You took fatal damage! Reviving at start with {player.stats['hp']} HP.")
            
            
        elif outcome["status"] == "continue":
            player.combat_state["hp"] = outcome["mob_hp"]
            player.stats["hp"] = temp_player.stats["hp"]
            
            # Regenerate Flux: 10% of max per round
            max_flux = player.stats.get("max_flux", 100)
            current_flux = player.stats.get("flux", 0)
            flux_regen = int(max_flux * 0.10)
            new_flux = min(max_flux, current_flux + flux_regen)
            player.stats["flux"] = new_flux
            
            # Send Flux regen notification
            if flux_regen > 0 and new_flux < max_flux:
                await self.manager.send_personal_message({
                    "type": "chat", "sender": "System", "content": f"⚡ Regenerated {flux_regen} Flux ({new_flux}/{max_flux})", "channel": "channel-combat"
                }, player.id)
            
            # Reduce cooldowns
            if "skill_cooldowns" in player.stats:
                cooldowns = player.stats["skill_cooldowns"]
                for skill_id in list(cooldowns.keys()):
                    if cooldowns[skill_id] > 0:
                        cooldowns[skill_id] -= 1
                        if cooldowns[skill_id] <= 0:
                            del cooldowns[skill_id]
                            # Notify skill is ready
                            skill = skills_manager.get_skill(skill_id)
                            if skill:
                                await self.manager.send_personal_message({
                                    "type": "chat", "sender": "System", "content": f"✓ {skill.name} is ready!", "channel": "channel-info"
                                }, player.id)
                player.stats["skill_cooldowns"] = cooldowns
            
            flag_modified(player, "combat_state")
            flag_modified(player, "stats")
            db.commit()
            
        # Update UI
        await self.cmd_look(player, [])

    async def cmd_flee(self, player: Player, db: Session):
        if random.random() > 0.5:
            player.combat_state = None
            if player.id in self.active_mobs: del self.active_mobs[player.id]
            db.commit()
            await self.msg_system(player.id, "You fled successfully!")
        else:
            await self.msg_system(player.id, "Failed to flee!")

    async def cmd_look(self, player: Player, args):
        room = world.get_room(player.current_map)
        if not room: room = world.get_start_room()
        
        eff_stats = calculate_effective_stats(player.stats, player.transformation)

        await self.manager.send_personal_message({
            "type": "gamestate",
            "room": {
                "id": room.id,
                "name": room.name,
                "description": room.description,
                "exits": room.exits,
                "mobs": room.mobs
            },
            "player": {
                "id": player.id, 
                "name": player.name,
                "level": player.level,
                "stats": eff_stats,
                "exp": player.exp,
                "race": player.race,
                "transformation": player.transformation,
                "zeni": player.zeni,
                "inventory": player.inventory
            }
        }, player.id)

    async def cmd_move(self, player: Player, direction: str, db: Session):
        short_dir = { "n": "north", "s": "south", "e": "east", "w": "west" }
        direction = short_dir.get(direction, direction)
        current_room = world.get_room(player.current_map)
        
        # Auto-fix if room doesn't exist (e.g. after map update)
        if not current_room:
            start_room = world.get_start_room()
            player.current_map = start_room.id
            db.commit()
            current_room = start_room
            await self.msg_system(player.id, "You were lost in the void and returned to reality.")

        if direction in current_room.exits:
            player.current_map = current_room.exits[direction]
            db.commit()
            await self.msg_system(player.id, f"You move {direction}...")
            await self.cmd_look(player, [])
        else:
            await self.msg_system(player.id, "You cannot go that way.")

    async def cmd_say(self, player: Player, message: str):
        await self.manager.broadcast({
            "type": "chat", "sender": player.name, "content": message, "channel": "channel-say"
        })

    async def msg_system(self, player_id: int, text: str):
        await self.manager.send_personal_message({
            "type": "chat", "sender": "System", "content": text, "channel": "channel-system"
        }, player_id)

    async def cmd_inventory(self, player: Player):
        inv_list = []
        if player.inventory:
            for item_data in player.inventory:
                item = inventory_manager.get_item(item_data["item_id"])
                if item:
                    inv_list.append(f"{item.name} x{item_data['qty']}")
        
        msg = f"Credits: {player.zeni}\n"
        if inv_list:
            msg += "Inventory:\n- " + "\n- ".join(inv_list)
        else:
            msg += "Inventory is empty."
            
        await self.msg_system(player.id, msg)

    async def cmd_buy(self, player: Player, item_name: str, db: Session):
        room_id = player.current_map
        shop = inventory_manager.get_shop(room_id)
        
        if not shop:
            await self.msg_system(player.id, "There is no shop here.")
            return
            
        if not item_name:
             # HTML Shop Interface
             html = f"""
             <div class="mt-2 mb-4 max-w-3xl border border-gray-800 bg-gray-900/50 rounded p-4 font-mono whitespace-normal">
                 <div class="flex justify-between items-center border-b border-cyan-900/50 pb-2 mb-3">
                     <h3 class="text-cyan-500 font-header text-lg uppercase tracking-wider">
                         {shop['name']}
                     </h3>
                     <span class="text-xs text-yellow-500 font-bold border border-yellow-900/50 px-2 py-1 rounded bg-yellow-900/10">
                         Credits: {player.zeni}
                     </span>
                 </div>
                 
                 <table class="w-full text-sm border-collapse">
                     <thead>
                         <tr class="text-gray-500 text-xs uppercase tracking-wider border-b border-gray-800">
                             <th class="py-2 text-left w-1/3">Item</th>
                             <th class="py-2 text-center w-20">Price</th>
                             <th class="py-2 text-left">Description</th>
                         </tr>
                     </thead>
                     <tbody class="divide-y divide-gray-800/50">
             """
             
             if not shop['inventory']:
                 html += '<tr><td colspan="3" class="py-4 text-center text-gray-500 italic">This shop is empty.</td></tr>'
             else:
                 for i_id in shop['inventory']:
                     item = inventory_manager.get_item(i_id)
                     if item:
                         can_afford = player.zeni >= item.price
                         price_class = "text-yellow-500" if can_afford else "text-red-500"
                         row_class = "hover:bg-gray-800/50 transition-colors cursor-pointer group"
                         
                         html += f"""
                         <tr class="{row_class}">
                             <td class="py-2 text-white font-bold group-hover:text-cyan-400 transition-colors">{item.name}</td>
                             <td class="py-2 text-center {price_class} font-bold">{item.price}</td>
                             <td class="py-2 text-gray-400 italic">{item.description}</td>
                         </tr>
                         """

             html += """
                     </tbody>
                 </table>
                 <div class="mt-3 text-xs text-gray-600 text-center border-t border-gray-800 pt-2">
                     Type <span class="text-cyan-700">buy &lt;item name&gt;</span> to purchase.
                 </div>
             </div>
             """
             await self.msg_system(player.id, html)
             return

        target_item = None
        for i_id in shop['inventory']:
             item = inventory_manager.get_item(i_id)
             if item and item.name.lower() == item_name.lower():
                 target_item = item
                 break
        
        if not target_item:
            await self.msg_system(player.id, "That item is not sold here.")
            return

        if player.zeni < target_item.price:
            await self.msg_system(player.id, "You cannot afford that.")
            return

        player.zeni -= target_item.price
        
        inv = list(player.inventory) if player.inventory else []
        found = False
        for slot in inv:
            if slot["item_id"] == target_item.id:
                slot["qty"] += 1
                found = True
                break
        if not found:
            inv.append({"item_id": target_item.id, "qty": 1})
            
        player.inventory = inv
        flag_modified(player, "inventory")
        db.commit()
        
        await self.msg_system(player.id, f"You bought {target_item.name} for {target_item.price} Credits.")

    async def cmd_use(self, player: Player, item_name: str, db: Session):
        if not player.inventory:
             await self.msg_system(player.id, "You have nothing to use.")
             return

        target_slot = None
        target_item = None
        
        for slot in player.inventory:
            item = inventory_manager.get_item(slot["item_id"])
            if item and item.name.lower() == item_name.lower():
                target_slot = slot
                target_item = item
                break
        
        if not target_slot:
            await self.msg_system(player.id, "You don't have that item.")
            return

        if target_item.type == "consumable":
            if "hp" in target_item.effect:
                max_hp = player.stats.get("max_hp", 100)
                current = player.stats.get("hp", max_hp)
                heal = target_item.effect["hp"]
                
                new_hp = min(max_hp, current + heal)
                player.stats["hp"] = new_hp
                flag_modified(player, "stats")
                
                await self.msg_system(player.id, f"You used {target_item.name} and recovered {heal} HP.")
                
            inv = list(player.inventory)
            target_slot["qty"] -= 1
            if target_slot["qty"] <= 0:
                inv.remove(target_slot)
            player.inventory = inv
            flag_modified(player, "inventory")
            db.commit()
            
        elif target_item.type in ["weapon", "armor", "accessory"]:
             await self.msg_system(player.id, "You cannot equip items yet (Coming Soon).")
        else:
             await self.msg_system(player.id, "You cannot use that.")

    async def cmd_talk(self, player: Player, args: str, db: Session):
        room_id = player.current_map
        npc = quest_manager.get_npc_by_room(room_id)
        
        if not npc:
            await self.msg_system(player.id, "There is no one here to talk to.")
            return

        q_id = npc.get("quest_id")
        
        if q_id in player.completed_quests:
            await self.msg_system(player.id, f"{npc['name']}: {npc['dialogue']['default']}")
            return

        if player.active_quests and q_id in player.active_quests:
            progress = player.active_quests[q_id]
            quest = quest_manager.get_quest(q_id)
            
            if progress["progress"] >= quest["count"]:
                await self.msg_system(player.id, f"{npc['name']}: {npc['dialogue']['quest_complete']}")
                
                rewards = []
                if "zeni" in quest["reward"]:
                    player.zeni += quest["reward"]["zeni"]
                    rewards.append(f"{quest['reward']['zeni']} Credits")
                if "exp" in quest["reward"]:
                    player.exp += quest["reward"]["exp"]
                    rewards.append(f"{quest['reward']['exp']} EXP")
                if "item" in quest["reward"]:
                    item_id = quest["reward"]["item"]
                    inv = list(player.inventory) if player.inventory else []
                    inv.append({"item_id": item_id, "qty": 1})
                    player.inventory = inv
                    flag_modified(player, "inventory")
                    rewards.append(f"Item: {item_id}")

                active = copy.deepcopy(player.active_quests)
                del active[q_id]
                player.active_quests = active
                flag_modified(player, "active_quests")
                
                completed = list(player.completed_quests) if player.completed_quests else []
                completed.append(q_id)
                player.completed_quests = completed
                flag_modified(player, "completed_quests")
                
                db.commit()
                await self.msg_system(player.id, f"Quest Completed! Received: {', '.join(rewards)}")
            else:
                await self.msg_system(player.id, f"{npc['name']}: {npc['dialogue']['quest_pending']}")
        
        else:
            if q_id:
                 await self.msg_system(player.id, f"{npc['name']}: {npc['dialogue']['quest_start']}")
                 
                 active = copy.deepcopy(player.active_quests) if player.active_quests else {}
                 active[q_id] = {"progress": 0}
                 player.active_quests = active
                 flag_modified(player, "active_quests")
                 db.commit()
                 
                 await self.msg_system(player.id, "Quest Started! Check 'quests' for details.")
            else:
                 await self.msg_system(player.id, f"{npc['name']}: {npc['dialogue']['default']}")

    async def cmd_quests(self, player: Player):
        if not player.active_quests:
            await self.msg_system(player.id, "No active quests.")
            return
            
        msg = "Active Quests:"
        for q_id, data in player.active_quests.items():
            quest = quest_manager.get_quest(q_id)
            if quest:
                msg += f"\n- {quest['title']}: {data['progress']}/{quest['count']} ({quest['description']})"
        await self.msg_system(player.id, msg)

    async def cmd_wish(self, player: Player, db: Session):
        # Check for Cosmic Shards 1-7
        required = [f"cosmic_shard_{i}" for i in range(1, 8)]
        has_all = True
        
        # Build inventory lookup
        inv_counts = {}
        if player.inventory:
            for slot in player.inventory:
                inv_counts[slot["item_id"]] = slot["qty"]
        
        for r in required:
            if inv_counts.get(r, 0) < 1:
                has_all = False
                break
        
        if not has_all:
             await self.msg_system(player.id, "You do not have all 7 Cosmic Shards.")
             return

        # Summon Logic
        await self.msg_system(player.id, "The shards resonate... a rift opens in reality...")
        await self.manager.broadcast({
             "type": "chat", "sender": "System", "content": "THE ARCHON has been summoned by a powerful traveler!", "channel": "channel-info"
        })
        await self.msg_system(player.id, "ARCHON: 'YOU HAVE AWAKENED ME. STATE YOUR DESIRE.'")
        
        # Reward: +5 Levels and full heal
        old_level = player.level
        player.level += 5
        player.exp = 0 
        
        # Scaling stats
        race = db.query(Race).filter(Race.name == player.race).first()
        if race and race.scaling_stats:
            for _ in range(5): # Apply growth 5 times
                for k, v in race.scaling_stats.items():
                    if k in player.stats:
                        player.stats[k] = int(player.stats[k] + v)
        
        player.stats["max_hp"] = player.stats["vit"] * 10
        player.stats["hp"] = player.stats["max_hp"]
        flag_modified(player, "stats") # Important!

        # Remove Balls
        inv = list(player.inventory)
        for r in required:
            for slot in inv:
                if slot["item_id"] == r:
                    slot["qty"] -= 1
                    if slot["qty"] <= 0:
                        inv.remove(slot)
                    break
        player.inventory = inv
        flag_modified(player, "inventory")
        db.commit()

        await self.msg_system(player.id, f"You have gained 5 levels! (Level {old_level} -> {player.level})")
        await self.msg_system(player.id, "ARCHON: 'IT IS DONE.' (The shards dissipate into the void).")

    async def grant_exp(self, player: Player, amount: int, db: Session):
        player.exp += amount
        
        while True:
            req_exp = player.level * 100
            if player.exp >= req_exp:
                player.level += 1
                player.exp -= req_exp
                
                await self.msg_system(player.id, f"LEVEL UP! You are now level {player.level}!")
                await self.manager.broadcast({
                    "type": "chat", "sender": "System", "content": f"{player.name} has reached Level {player.level}!", "channel": "channel-info"
                })
                
                race = db.query(Race).filter(Race.name == player.race).first()
                if race and race.scaling_stats:
                    for k, v in race.scaling_stats.items():
                        if k in player.stats:
                            player.stats[k] = int(player.stats[k] + v)
                    
                    player.stats["max_hp"] = int(player.stats["vit"] * 10)
                    if player.stats["hp"] > player.stats["max_hp"]:
                        player.stats["hp"] = player.stats["max_hp"]
                    
                    # Recalculate Flux: base_flux + (INT * 5)
                    base_flux = race.base_flux if race.base_flux else 100
                    player.stats["max_flux"] = base_flux + (player.stats.get("int", 0) * 5)
                    player.stats["flux"] = player.stats["max_flux"]  # Restore to full on level up
                    
                # Auto-learn skills
                available = skills_manager.get_available_skills(player.race, player.level)
                current_skills = list(player.learned_skills) if player.learned_skills else []
                new_skills_names = []
                
                for skill in available:
                    if skill.id not in current_skills:
                        current_skills.append(skill.id)
                        new_skills_names.append(skill.name)
                
                if new_skills_names:
                    player.learned_skills = current_skills
                    flag_modified(player, "learned_skills")
                    await self.msg_system(player.id, f"Learned new skills: {', '.join(new_skills_names)}")
                    await self.manager.broadcast({
                        "type": "chat", "sender": "System", "content": f"{player.name} learned {', '.join(new_skills_names)}!", "channel": "channel-info"
                    })
                flag_modified(player, "stats")
                flag_modified(player, "exp")
            else:
                break
        
        db.commit()

    async def cmd_skills(self, player: Player, db: Session):
        """List available and learned skills."""
        
        all_skills = skills_manager.get_all_race_skills(player.race)
        skill_cooldowns = player.stats.get("skill_cooldowns", {})
        
        # Build HTML Table
        html = f"""
        <div class="mt-2 mb-4 max-w-3xl border border-gray-800 bg-gray-900/50 rounded p-4 font-mono whitespace-normal">
            <h3 class="text-cyan-500 font-header text-lg border-b border-cyan-900/50 pb-2 mb-3 uppercase tracking-wider">
                Skill Progression <span class="text-gray-500 text-sm">[{player.race}]</span>
            </h3>
            
            <table class="w-full text-sm border-collapse">
                <thead>
                    <tr class="text-gray-500 text-xs uppercase tracking-wider border-b border-gray-800">
                        <th class="py-2 text-left w-1/4">Skill</th>
                        <th class="py-2 text-center w-16">Lvl</th>
                        <th class="py-2 text-center w-16">Flux</th>
                        <th class="py-2 text-left">Description</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-800/50">
        """
        
        if not all_skills:
             html += '<tr><td colspan="4" class="py-4 text-center text-gray-500 italic">No skills found.</td></tr>'
        
        for s in all_skills:
            is_learned = s.id in player.learned_skills
            is_available = player.level >= s.level_required
            
            # Row Styling
            row_class = "hover:bg-gray-800/50 transition-colors"
            name_class = "font-bold"
            desc_class = "text-gray-400"
            flux_val = f"{s.flux_cost}" if s.flux_cost > 0 else "-"
            
            # Status Icon/Logic
            if is_learned:
                status_display = '<span class="text-green-500">✔</span>'
                name_class = "text-white"
                
                # Check cooldown
                cd = skill_cooldowns.get(s.id, 0)
                if cd > 0:
                    status_display = f'<span class="text-red-500 font-bold">{cd}s</span>'
                    
            elif is_available:
                status_display = '<span class="text-yellow-500 animate-pulse">🔓</span>'
                name_class = "text-yellow-100"
            else:
                status_display = f'<span class="text-gray-600">Lv{s.level_required}</span>'
                name_class = "text-gray-600"
                desc_class = "text-gray-600 italic"
                row_class = ""

            html += f"""
                <tr class="{row_class}">
                    <td class="py-2 {name_class}">{s.name}</td>
                    <td class="py-2 text-center">{status_display}</td>
                    <td class="py-2 text-center text-cyan-600">{flux_val}</td>
                    <td class="py-2 {desc_class}">{s.description}</td>
                </tr>
            """

        html += """
                </tbody>
            </table>
            <div class="mt-3 text-xs text-gray-600 text-center border-t border-gray-800 pt-2">
                Type <span class="text-cyan-700">skillinfo &lt;name&gt;</span> for details.
            </div>
        </div>
        """
        
        await self.msg_system(player.id, html)
    
    async def cmd_skill_info(self, player: Player, skill_name: str, db: Session):
        """Show detailed information about a specific skill."""
        if not skill_name:
            await self.msg_system(player.id, "Usage: skillinfo <skill_name>")
            return
        
        # Use simple name matching first
        found_skill = None
        s_name_lower = skill_name.lower()
        
        all_skills = skills_manager.get_all_race_skills(player.race)
        
        # Prioritize race skills first
        for s in all_skills:
             if s.name.lower() == s_name_lower:
                 found_skill = s
                 break
        
        # Fallback to global search if not found in race skills (e.g. checking other class skills for fun)
        if not found_skill:
             found_skill = skills_manager.get_skill_by_name(skill_name)

        if not found_skill:
            await self.msg_system(player.id, f"Skill '{skill_name}' not found.")
            return

        s = found_skill
        skill_cooldowns = player.stats.get("skill_cooldowns", {})
        
        is_learned = s.id in player.learned_skills
        status_color = "text-green-500" if is_learned else "text-gray-500"
        status_text = "LEARNED" if is_learned else "NOT LEARNED"
        if not is_learned and player.level < s.level_required:
            status_color = "text-red-500"
            status_text = "LOCKED"

        # Construct Requirements HTML
        req_html = ""
        req_html += f'<div class="flex justify-between"><span class="text-gray-500">Level:</span> <span class="text-white">{s.level_required}</span></div>'
        if s.race_required:
             req_html += f'<div class="flex justify-between"><span class="text-gray-500">Race:</span> <span class="text-white">{s.race_required}</span></div>'
        if s.transformation_required:
             req_html += f'<div class="flex justify-between"><span class="text-gray-500">Form:</span> <span class="text-yellow-500">{s.transformation_required}</span></div>'
             
        # Construct Costs HTML
        cost_html = ""
        cost_html += f'<div class="flex justify-between"><span class="text-gray-500">Flux:</span> <span class="text-cyan-400">{s.flux_cost}</span></div>'
        if s.hp_cost_percent > 0:
            cost_html += f'<div class="flex justify-between"><span class="text-gray-500">HP Cost:</span> <span class="text-red-500">{s.hp_cost_percent}%</span></div>'
        
        # Cooldown Logic
        cd_html = ""
        if s.cooldown > 0:
            current_cd = skill_cooldowns.get(s.id, 0)
            cd_val = f"{s.cooldown} Rounds"
            if current_cd > 0:
                cd_val += f" <span class='text-red-400'>({current_cd} left)</span>"
            else:
                 cd_val += " <span class='text-green-500'>(Ready)</span>"
            cd_html = f'<div class="flex justify-between mt-1 pt-1 border-t border-gray-800"><span class="text-gray-500">Cooldown:</span> <span class="text-gray-300">{cd_val}</span></div>'
        
        # Effects HTML
        eff_html = ""
        if s.damage_multiplier > 0:
             eff_html += f'<li class="text-gray-300">Deals <span class="text-red-400 font-bold">{s.damage_multiplier}x</span> {s.stat_type.upper()} Dmg</li>'
        if s.heal_percent > 0:
             eff_html += f'<li class="text-gray-300">Heals <span class="text-green-400 font-bold">{s.heal_percent}%</span> HP</li>'
        if s.skip_enemy_turn:
             eff_html += f'<li class="text-yellow-400">Stuns Enemy (Skip Turn)</li>'
        if s.damage_reduction > 0:
             eff_html += f'<li class="text-blue-400">Reduces Damage by {int(s.damage_reduction * 100)}%</li>'
        if s.defense_pierce_percent > 0:
             eff_html += f'<li class="text-purple-400">Pierces {s.defense_pierce_percent}% Defense</li>'
        if s.buff_stat:
             eff_html += f'<li class="text-green-400">+{s.buff_percent}% {s.buff_stat.upper()} ({s.buff_duration} turns)</li>'
        if s.dodge_chance > 0:
             eff_html += f'<li class="text-blue-300">{int(s.dodge_chance*100)}% Dodge Chance</li>'

        if not eff_html:
            eff_html = '<li class="text-gray-500 italic">No direct special effects.</li>'

        html = f"""
        <div class="mt-2 mb-4 max-w-lg border border-gray-700 bg-gray-900 rounded overflow-hidden font-mono shadow-lg whitespace-normal">
            <!-- Header -->
            <div class="bg-gray-800 px-4 py-2 border-b border-gray-700 flex justify-between items-center">
                <h3 class="text-lg font-bold text-white uppercase tracking-wider">{s.name}</h3>
                <span class="text-xs font-bold border px-2 py-0.5 rounded {status_color} border-current">{status_text}</span>
            </div>
            
            <div class="p-4 space-y-4">
                
                <!-- Description -->
                <div class="italic text-gray-400 text-sm border-l-2 border-cyan-800 pl-3">
                    "{s.description}"
                </div>
                
                <!-- Grid Stats -->
                <div class="grid grid-cols-2 gap-4 text-sm">
                    <div class="bg-black/30 p-2 rounded border border-gray-800">
                        <h4 class="text-cyan-600 font-bold text-xs uppercase mb-1 border-b border-gray-800 pb-1">Requirements</h4>
                        {req_html}
                    </div>
                    <div class="bg-black/30 p-2 rounded border border-gray-800">
                        <h4 class="text-red-500 font-bold text-xs uppercase mb-1 border-b border-gray-800 pb-1">Cost</h4>
                        {cost_html}
                        {cd_html}
                    </div>
                </div>

                <!-- Effects Section -->
                <div>
                     <h4 class="text-gray-500 font-bold text-xs uppercase mb-1">Combat Effects</h4>
                     <ul class="list-disc list-inside space-y-0.5 text-sm">
                        {eff_html}
                     </ul>
                </div>

            </div>
        </div>
        """
        
        await self.msg_system(player.id, html)
    
    async def cmd_passive(self, player: Player):
        """Show race passive ability."""
        passive = skills_manager.get_race_passive(player.race)
        msg = f"**Race Passive: {passive['name']}**\n{passive['description']}"
        await self.msg_system(player.id, msg)

    async def cmd_use_skill(self, player: Player, skill_name: str, db: Session):
        """Use a skill in combat."""
        if not player.combat_state:
            await self.msg_system(player.id, "You can only use skills in combat!")
            return
        
        if not skill_name:
            await self.msg_system(player.id, "Usage: skill <skill_name>")
            return
        
        # Find skill by name
        target_skill = skills_manager.get_skill_by_name(skill_name)
        
        if not target_skill:
            await self.msg_system(player.id, f"Unknown skill '{skill_name}'.")
            return
            
        if target_skill.id not in player.learned_skills:
             await self.msg_system(player.id, f"You haven't learned {target_skill.name} yet.")
             return
        
        # Check if can use
        can_use, error = skills_manager.can_use_skill(target_skill.id, player.race, player.level, player.transformation)
        if not can_use:
            await self.msg_system(player.id, error)
            return
        
        # Check cooldown
        skill_cooldowns = player.stats.get("skill_cooldowns", {})
        if target_skill.id in skill_cooldowns and skill_cooldowns[target_skill.id] > 0:
            remaining = skill_cooldowns[target_skill.id]
            await self.msg_system(player.id, f"{target_skill.name} is on cooldown! {remaining} rounds remaining.")
            return
        
        # Check Flux cost
        current_flux = player.stats.get("flux", 0)
        flux_cost = target_skill.flux_cost
        if current_flux < flux_cost:
            await self.msg_system(player.id, f"Not enough Flux! Need {flux_cost}, have {current_flux}.")
            return
        
        # Deduct Flux and log it
        player.stats["flux"] = current_flux - flux_cost
        flag_modified(player, "stats")
        db.commit()
        
        # Send Flux change notification
        await self.manager.send_personal_message({
            "type": "chat", "sender": "System", "content": f"⚡ Used {flux_cost} Flux ({current_flux - flux_cost}/{player.stats.get('max_flux', 100)} remaining)", "channel": "channel-combat"
        }, player.id)
        
        # Set cooldown if skill has one
        if target_skill.cooldown > 0:
            if "skill_cooldowns" not in player.stats:
                player.stats["skill_cooldowns"] = {}
            player.stats["skill_cooldowns"][target_skill.id] = target_skill.cooldown
            flag_modified(player, "stats")
            db.commit()
        
        # Execute skill in combat
        mob = self.active_mobs.get(player.id)
        if not mob and player.combat_state:
             mob = self.combat_system.spawn_mob(player.combat_state["mob_id"])
             mob.stats["hp"] = player.combat_state["hp"]
             self.active_mobs[player.id] = mob

        if not mob:
            player.combat_state = None
            db.commit()
            return

        eff_stats = calculate_effective_stats(player.stats, player.transformation)
        
        class TempPlayer:
            def __init__(self, stats): self.stats = stats
        
        temp_player = TempPlayer(eff_stats)

        outcome = await self.combat_system.combat_round(temp_player, mob, "skill", skill=target_skill)
        
        for line in outcome["log"]:
             await self.manager.send_personal_message({
                 "type": "chat", "sender": "Combat", "content": line, "channel": "channel-combat"
            }, player.id)

        # Handle combat end
        if outcome["status"] == "win":
            await self.grant_exp(player, outcome["exp"], db)
            
            logs = [f"You gained {outcome['exp']} EXP."]
            
            # LOOT HANDLING
            if "loot" in outcome and outcome["loot"]:
                inv = list(player.inventory) if player.inventory else []
                new_items = []
                for item_id in outcome["loot"]:
                    item = inventory_manager.get_item(item_id)
                    if item:
                        found = False
                        for slot in inv:
                            if slot["item_id"] == item_id:
                                slot["qty"] += 1
                                found = True
                                break
                        if not found:
                            inv.append({"item_id": item_id, "qty": 1})
                        new_items.append(item.name)
                
                if new_items:
                    player.inventory = inv
                    flag_modified(player, "inventory")
                    logs.append(f"Loot dropped: {', '.join(new_items)}")

            await self.msg_system(player.id, " ".join(logs))
            
            player.combat_state = None
            if player.id in self.active_mobs: del self.active_mobs[player.id]
            db.commit()
            
        elif outcome["status"] == "loss":
            player.combat_state = None
            if player.id in self.active_mobs: del self.active_mobs[player.id]
            player.stats["hp"] = int(player.stats["max_hp"] * 0.5)
            flag_modified(player, "stats")
            player.current_map = "start_area"
            player.transformation = "Base"
            db.commit()
            await self.msg_system(player.id, f"You took fatal damage! Reviving at start with {player.stats['hp']} HP.")
            
        elif outcome["status"] == "continue":
            player.combat_state["hp"] = outcome["mob_hp"]
            player.stats["hp"] = temp_player.stats["hp"] 
            flag_modified(player, "combat_state")
            flag_modified(player, "stats")
            db.commit()
            
        # Update UI
        await self.cmd_look(player, [])

