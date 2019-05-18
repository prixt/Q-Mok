from godot import exposed, export
from godot.bindings import Sprite, Color

WHITE = 0
BLACK = 1
UNKNOWN = 2
EMPTY = -1

@exposed
class Rock(Sprite):
    cell_x = export(int)
    cell_y = export(int)

    @export(int)
    @property
    def value(self):
        return self._value
    
    @value.setter
    def value(self, val):
        self._value = val

        if val == WHITE:
            self.set_modulate( Color(1.0, 1.0, 1.0, 1) )
            self.visible = True
        elif val == BLACK:
            self.set_modulate( Color(0.3, 0.3, 0.3, 1) )
            self.visible = True
        elif val == UNKNOWN:
            self.set_modulate( Color(0.1, 0.8, 0.8, 1) )
            self.visible = True
        elif val == EMPTY:
            self.visible = False

    def _ready(self):
        self.value = -1