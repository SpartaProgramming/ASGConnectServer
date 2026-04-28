class GameMode: #Szablon rozgrywek, jakie metody ma implementować, jak integruje się z resztą systemu
    def __init__(self, name):
        self.name = name

    def on_hit(self, victim, session):
        pass

    def check_victory(self, session):
        pass

    def get_game_update_data(self, player, session):
        return {"allies": 0, "enemies": 0}

class TeamDeathmatch(GameMode):
    def on_hit(self, victim, session):
        victim.status = "DEAD"
        token = victim.tag.generate_new_token()
        session.mqtt.send_command(victim.tag.dev_eui, token, "DIE")

    """
     Dla każdego gracza zwraca customową informację o rozgrywce w danym trybie. 
    """
    def get_game_update_data(self, player, session):
        all_players = session.registry.get_all_players()
        red_alive = sum(1 for p in all_players if p.team == 0 and p.status == "ALIVE")
        blue_alive = sum(1 for p in all_players if p.team == 1 and p.status == "ALIVE")
        return {"allies": red_alive, "enemies": blue_alive}