from godot import exposed, export
from godot.bindings import Node
import Scripts.Quantum

@exposed
class Title(Node):
    def play_pressed(self):
        self.get_tree().change_scene("res://Scenes/Gameplay.tscn")
    
    def tutorial_pressed(self):
        self.get_tree().change_scene("res://Scenes/Tutorial.tscn")
    
    def about_pressed(self):
        self.get_tree().change_scene("res://Scenes/About.tscn")
    
    def _ready(self):
        pass