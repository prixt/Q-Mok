from godot import exposed, export
from godot.bindings import Node
from Scripts.Quantum import real_name

@exposed
class Gameplay(Node):
    job = None
    turn = 0

    is_white = export(bool, True)
    is_quantum = export(bool, True)
    
    def tick(self):
        if self.board.is_cleared:
            return
        if self.turn != 0 and self.turn % 15 == 0:
            self.board.collapse()
            self.timer.start()
            self.timer_timeout()
        self.turn += 1
        self.is_quantum = (self.turn % 3 == 0)
        self.is_white = (self.turn % 2 == 1)
        self.update_status_text()
    
    def timer_timeout(self):
        self.board.check_job()
        if self.board.is_measuring:
            self.get_node('WaitIndicator').set_visible(True)
            print('Still waiting...')

    def update_status_text(self):
        if self.board.is_cleared:
            return
        if self.board.is_measuring:
            self.status_text.text = 'Collapsing Quantum States...'
        elif self.is_white:
            if self.is_quantum:
                self.status_text.text = 'White\'s Quantum Turn'
            else:
                self.status_text.text = 'White\'s Turn'
        else:
            if self.is_quantum:
                self.status_text.text = 'Black\'s Quantum Turn'
            else:
                self.status_text.text = 'Black\'s Turn'
    
    def game_over(self, winner):
        self.status_text.text = '%s Wins!' % winner
        self.get_node('Restart').visible = True
    
    def restart_pressed(self):
        self.get_tree().reload_current_scene()
    
    def show_circuit(self, text):
        self.circuit_text.set_text(text)
        self.circuit_text.set_visible(True)
    
    def job_cleanup(self):
        self.circuit_text.set_visible(False)
        self.get_node('WaitIndicator').set_visible(False)
        self.timer.stop()
        self.update_status_text()

    def quantum_toggle(self, button_pressed):
        if button_pressed:
            self.get_node('DeviceName').set_text( "Quantum Device:\n" + real_name )
        else:
            self.get_node('DeviceName').set_text( "Local Simulator" )

    def _ready(self):
        self.timer = self.get_node('Timer')
        self.board = self.get_node('Board')
        self.status_text = self.get_node('GameStatus')
        self.circuit_text = self.get_node('CircuitText')
        self.board.connect('game_finished', self, 'game_over')
        self.board.connect('circuit_finished', self, 'show_circuit')
        self.board.connect('job_finished', self, 'job_cleanup')

        self.tick()