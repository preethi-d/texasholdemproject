from players.learningplayer import LearningPlayer

player = LearningPlayer()
player.load_qtable_from_file("q-table-1200.txt")
print("\n".join(player.dump_table()))