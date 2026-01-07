from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from app.models.player import Player
from app.game.world import world
from app.game.transformations import get_transformation, get_available_transformations, calculate_effective_stats
from app.models.race import Race
from app.game.quest_manager import quest_manager
from app.game.combat import CombatSystem, Mob
from app.game.inventory_manager import inventory_manager
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
            else:
                await self.msg_system(player.id, "You are in combat! Valid commands: attack, flee, use")
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
            player.transformation = "Base"
            db.commit()
            await self.msg_system(player.id, "You revert to your base form.")
        elif verb in ["inventory", "i", "inv"]:
            await self.cmd_inventory(player)
        elif verb == "buy":
            await self.cmd_buy(player, " ".join(args), db)
        elif verb == "use":
            await self.cmd_use(player, " ".join(args), db)
        elif verb == "talk":
            await self.cmd_talk(player, " ".join(args), db)
        elif verb in ["quests", "q"]:
            await self.cmd_quests(player)
        elif verb == "wish":
            await self.cmd_wish(player, db)
        elif verb == "cheat_balls":
             # Dev Helper
             inv = list(player.inventory) if player.inventory else []
             for i in range(1, 8):
                 inv.append({"item_id": f"dragon_ball_{i}", "qty": 1})
             player.inventory = inv
             flag_modified(player, "inventory")
             db.commit()
             await self.msg_system(player.id, "Cheater! You have the balls.")
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
            await self.msg_system(player.id, "You are lost in the void.")
            return

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
            player.exp += outcome["exp"]
            req_exp = player.level * 100
            
            logs = [f"You gained {outcome['exp']} EXP."]
            
            if player.exp >= req_exp:
                player.level += 1
                player.exp -= req_exp
                logs.append(f"LEVEL UP! You are now level {player.level}!")
                
                race = db.query(Race).filter(Race.name == player.race).first()
                if race and race.scaling_stats:
                    for k, v in race.scaling_stats.items():
                        if k in player.stats:
                            player.stats[k] = int(player.stats[k] + v)
                    
                    player.stats["max_hp"] = player.stats["vit"] * 10
                    player.stats["hp"] = player.stats["max_hp"]
                    flag_modified(player, "stats")

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
            await self.msg_system(player.id, "You are defeated... Reviving at start.")
            
        elif outcome["status"] == "continue":
            player.combat_state["hp"] = outcome["mob_hp"]
            player.stats["hp"] = temp_player.stats["hp"] 
            flag_modified(player, "combat_state")
            flag_modified(player, "stats")
            db.commit()

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
                "exits": room.exits
            },
            "player": {
                "id": player.id, 
                "name": player.name,
                "level": player.level,
                "stats": eff_stats,
                "exp": player.exp,
                "race": player.race,
                "transformation": player.transformation
            }
        }, player.id)

    async def cmd_move(self, player: Player, direction: str, db: Session):
        short_dir = { "n": "north", "s": "south", "e": "east", "w": "west" }
        direction = short_dir.get(direction, direction)
        current_room = world.get_room(player.current_map)
        if not current_room: return
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
        
        msg = f"Zeni: {player.zeni}\n"
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
             msg = f"Welcome to {shop['name']}!\nGoods for sale:"
             for i_id in shop['inventory']:
                 item = inventory_manager.get_item(i_id)
                 if item:
                     msg += f"\n- {item.name}: {item.price} Zeni"
             await self.msg_system(player.id, msg)
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
        
        await self.msg_system(player.id, f"You bought {target_item.name} for {target_item.price} Zeni.")

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
                    rewards.append(f"{quest['reward']['zeni']} Zeni")
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
        # Check for Dragon Balls 1-7
        required = [f"dragon_ball_{i}" for i in range(1, 8)]
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
             await self.msg_system(player.id, "You do not have all 7 Dragon Balls.")
             return

        # Summon Logic
        await self.msg_system(player.id, "The sky turns dark... thunder rumbles...")
        await self.manager.broadcast({
             "type": "chat", "sender": "System", "content": "SHENRON has been summoned by a powerful warrior!", "channel": "channel-info"
        })
        await self.msg_system(player.id, "SHENRON: 'I SHALL GRANT YOU ONE WISH. I WILL MAKE YOU POWERFUL.'")
        
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
        await self.msg_system(player.id, "SHENRON: 'FAREWELL.' (The balls scatter to the winds... well, they vanish from your inventory).")
