from godot import exposed, export
from godot.bindings import Node

@exposed
class Tutorial(Node):
    def return_pressed(self):
        self.get_tree().change_scene("res://Scenes/Title.tscn")

    def _ready(self):
        pass
