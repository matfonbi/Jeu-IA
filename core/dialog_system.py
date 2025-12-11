import arcade
from core.utils_text import wrap_dialog_history, count_wrapped_lines
from managers.npc_agent import NPC_Agent

class DialogSystem:
    def __init__(self, game):
        self.game = game

    def detect_npc(self):
        g = self.game
        npc_zones = g.map_manager.npc_interactions
        g.npc_to_talk = None

        if npc_zones:
            detected = arcade.check_for_collision_with_list(g.player, npc_zones)
            if detected:
                g.npc_to_talk = detected[0].npc_ref

    def update(self):
        self.detect_npc()
        g = self.game

        # Position bulle
        if g.npc_to_talk and not g.in_dialogue:
            cam_x, cam_y = g.camera.position
            win_w, win_h = g.get_size()

            g.bubble_sprite.center_x = g.player.center_x - cam_x + win_w / 2
            g.bubble_sprite.center_y = g.player.center_y - cam_y + win_h / 2 + 50

    def start_dialog(self, npc):
        g = self.game

        g.in_dialogue = True
        g.current_npc = npc
        g.dialog_scroll = 0

        folder = f"npc/{npc.npc_name}"

        quest_prompt = ""
        if g.quest_manager:
            _, quest_prompt = g.quest_manager.handle_npc_interaction(
                npc_name=npc.npc_name,
                inventory=g.inventory,
            )

        g.npc_agent = NPC_Agent(folder, quest_prompt)
        inv_list = list(g.inventory.keys())
        first_message = g.npc_agent.start_dialog(inv_list)

        # --- APPLIQUER LES EFFETS DE QUÊTES APRÈS LA RÉPONSE IA ---
        if g.quest_manager:
            g.quest_manager.finalize_quests_after_dialog(
                npc_name=npc.npc_name,
                inventory=g.inventory,
            )

        g.dialog_history = [(npc.npc_name.capitalize(), first_message)]
        g.dialog_input = ""


    def send_player_message(self):
        g = self.game
        msg = g.dialog_input.strip()

        if not msg:
            return

        g.dialog_history.append(("Vous", msg))

        # Met à jour le contexte de quêtes AVANT la réponse
        if g.quest_manager and g.current_npc:
            _, quest_prompt = g.quest_manager.handle_npc_interaction(
                npc_name=g.current_npc.npc_name,
                inventory=g.inventory,
            )
            if quest_prompt:
                g.npc_agent.quest_context = quest_prompt

        # Réponse IA
        npc_response = g.npc_agent.ask(
            player_message=msg,
            inventory_list=list(g.inventory.keys())
        )

        # APRES la réponse, on applique réellement la validation des quêtes
        if g.quest_manager and g.current_npc:
            completed_now = g.quest_manager.finalize_quests_after_dialog(
                npc_name=g.current_npc.npc_name,
                inventory=g.inventory,
            )
            # Si tu veux, tu peux ici afficher un message "Quête terminée !" selon completed_now

        g.dialog_history.append((g.current_npc.npc_name.capitalize(), npc_response))
        g.dialog_input = ""
        g.dialog_scroll = 0


    def scroll(self, dy):
        g = self.game

        win_w, win_h = g.get_size()
        box_width = win_w - 100
        total_lines = count_wrapped_lines(g.dialog_history, box_width - 40, font_size=18)

        history_height = int(win_h * 0.40) - 80
        line_height = 24
        max_visible = max(1, history_height // line_height)
        max_scroll = max(0, total_lines - max_visible)

        if dy > 0:
            g.dialog_scroll = min(g.dialog_scroll + 1, max_scroll)
        else:
            g.dialog_scroll = max(g.dialog_scroll - 1, 0)
