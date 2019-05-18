from godot import exposed, export
from godot.bindings import *

@exposed
class About(Node):
    def return_pressed(self):
        self.get_tree().change_scene("res://Scenes/Title.tscn")

    def _ready(self):
        pass
