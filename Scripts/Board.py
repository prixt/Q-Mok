import random
from math import pi

from godot import exposed, export, signal
from godot.bindings import Vector2, Color, TileMap
from godot.globals import Globals

from Scripts.Rock import WHITE, BLACK, UNKNOWN, EMPTY
from Scripts.Quantum import assemble, transpile, CircuitBuilder, JobStatus, QiskitError, sim_backend, real_backend

RockScene = Globals.RockScene
GateScene = Globals.GateScene

TILE_COUNT = 16
TILE_SIZE = 32

@exposed
class Board(TileMap):
    is_measuring = export(bool, False)
    is_cleared = export(bool, False)

    game_finished = signal()
    circuit_finished = signal()
    job_finished = signal()
    
    gate_start_rock = None
    current_gate = None

    job = None
    backend = sim_backend
    
    def get_rock(self, x, y):
        return self.rocks_array[TILE_COUNT * y + x]

    def _unhandled_input(self, event):
        if not self.is_measuring and not self.is_cleared:
            if event.is_action_pressed('mouse_left_button'):
                v = self.get_local_mouse_position()
                x = int(v.x // TILE_SIZE)
                y = int(v.y // TILE_SIZE)
                cell = self.get_cell( x, y )
                if cell != -1:
                    rock = self.get_rock(x,y)
                    if rock.value == EMPTY:
                        if self.gameplay.is_quantum:
                            rock.value = UNKNOWN
                            
                            num = len( self.quantum_rocks )
                            self.quantum_rocks[rock.get_name()] = num
                            self.quantum_rocks_inv.append(rock)
                            if not self.gameplay.is_white:
                                self.quantum_operations.append( ('x', num) )
                            self.quantum_operations.append( ('h', num) )
                        elif self.gameplay.is_white:
                            rock.value = WHITE
                            self.check_cleared([(x,y)])
                        else:
                            rock.value = BLACK
                            self.check_cleared([(x,y)])
                        self.gameplay.tick()
                
            elif event.is_action_pressed('mouse_right_button') and self.gameplay.is_quantum:
                v = self.get_local_mouse_position()
                x = int(v.x // TILE_SIZE)
                y = int(v.y // TILE_SIZE)
                cell = self.get_cell( x, y )
                if cell != -1:
                    rock = self.get_rock( x, y )
                    if rock.value == UNKNOWN:
                        self.gate_start_rock = rock
                        gate = GateScene.instance()
                        gate.position = self.gate_start_rock.position
                        self.gates_node.add_child(gate)
                        self.current_gate = gate
                
            elif event.is_action_released('mouse_right_button') and self.current_gate != None:
                diff = self.get_local_mouse_position() - self.gate_start_rock.get_position()

                cx, cy = self.gate_start_rock.cell_x, self.gate_start_rock.cell_y
                nx, ny = cx, cy

                if diff.x >= 0:
                    if diff.y >= 0:
                        if diff.x >= diff.y:
                            nx += 1
                        else:
                            ny += 1
                    else:
                        if diff.x >= -diff.y:
                            nx += 1
                        else:
                            ny -= 1
                else:
                    if diff.y >= 0:
                        if -diff.x >= diff.y:
                            nx -= 1
                        else:
                            ny += 1
                    else:
                        if -diff.x >= -diff.y:
                            nx -= 1
                        else:
                            ny -= 1
                
                if nx >= 0 and nx < TILE_COUNT and ny >= 0 and ny < TILE_COUNT:
                    next_rock = self.get_rock(nx, ny)
                    if next_rock.value != EMPTY:
                        a_num = self.quantum_rocks[self.gate_start_rock.get_name()]
                        b_num = 0
                        if next_rock.value != UNKNOWN:
                            b_num = len( self.quantum_rocks )
                            self.quantum_rocks[next_rock.get_name()] = b_num
                            self.quantum_rocks_inv.append(next_rock)
                            if next_rock.value == BLACK:
                                self.quantum_operations.append( ('x', b_num) )
                            next_rock.value = UNKNOWN
                        else:
                            b_num = self.quantum_rocks[next_rock.get_name()]

                        self.quantum_operations.append(('gate', a_num, b_num))
                        self.quantum_gates.append(self.current_gate)
                        self.gameplay.tick()
                    else:
                        self.current_gate.queue_free()
                else:
                    self.current_gate.queue_free()
                
                self.gate_start_rock = None
                self.current_gate = None

    def collapse(self):
        register_size = len(self.quantum_rocks)
        circuit_builder = CircuitBuilder(register_size)
        for op in self.quantum_operations:
            circuit_builder.add_operation(op, self.backend)
        qr, cr, circuit = circuit_builder.build()
        circuit_text = circuit.draw(output='text',line_length=75)
        self.emit_signal('circuit_finished', circuit_text.single_string())
        qobj = assemble( transpile(circuit, self.backend, optimization_level=2) , self.backend, memory=True, shots=32)
        self.job = self.backend.run(qobj)
        self.is_measuring = True

    def check_job(self):
        if self.job != None:
            status = self.job.status()
            if status == JobStatus.DONE:
                self.cleanup()
                self.emit_signal('job_finished')
            elif status == JobStatus.ERROR or status == JobStatus.CANCELLED:
                raise QiskitError

    def cleanup(self):
        result = self.job.result()

        memory_list = result.get_memory()
        # counts = result.get_counts()
        # memory_list = []
        # for k,v in counts.items():
        #     for _ in range(v):
        #         memory_list.append(k)
        pick = memory_list[0]
        pick = pick[::-1]

        arr = []
        for i, v in enumerate(pick):
            rock = self.quantum_rocks_inv[i]
            if v == '0':
                rock.value = WHITE
            else:
                rock.value = BLACK
            arr.append( (rock.cell_x, rock.cell_y) )
        
        self.quantum_rocks.clear()
        self.quantum_rocks_inv.clear()
        self.quantum_operations.clear()
        for gate in self.quantum_gates:
            gate.queue_free()
        self.quantum_gates.clear()

        self.job = None
        self.is_measuring = False

        self.check_cleared(arr)

    def check_cleared(self, arr):
        for v in arr:
            x, y = v[0], v[1]
            value = self.get_rock(x,y).value

            count = 0
            for i in range(-4,5):
                cx = x + i
                if cx >= 0 and cx < TILE_COUNT and self.get_rock(cx,y).value == value:
                    count += 1
                    if count == 5:
                        return self.cleared(value)
                else:
                    count = 0

            count = 0
            for i in range(-4,5):
                cy = y + i
                if cy >= 0 and cy < TILE_COUNT and self.get_rock(x,cy).value == value:
                    count += 1
                    if count == 5:
                        return self.cleared(value)
                else:
                    count = 0

            count = 0
            for i in range(-4,5):
                cx, cy = x + i, y + i
                if cx >= 0 and cx < TILE_COUNT and cy >= 0 and cy < TILE_COUNT and self.get_rock(cx,cy).value == value:
                    count += 1
                    if count == 5:
                        return self.cleared(value)
                else:
                    count = 0
                
            count = 0
            for i in range(-4,5):
                cx, cy = x + i, y - i
                if cx >= 0 and cx < TILE_COUNT and cy >= 0 and cy < TILE_COUNT and self.get_rock(cx,cy).value == value:
                    count += 1
                    if count == 5:
                        return self.cleared(value)
                else:
                    count = 0
    
    def cleared(self, value):
        self.is_cleared = True
        winner = ''
        if value == WHITE:
            winner = 'White'
        else:
            winner = 'Black'
        self.emit_signal('game_finished', winner)

    def quantum_toggle(self, button_pressed):
        if button_pressed:
            self.backend = real_backend
        else:
            self.backend = sim_backend
    
    def _process(self, dt):
        if self.current_gate != None:
            dv = self.current_gate.position - self.get_local_mouse_position()
            if dv.x >= 0:
                if dv.y >= 0:
                    if dv.x >= dv.y:
                        self.current_gate.rotation_degrees = 180.0
                    else:
                        self.current_gate.rotation_degrees = 270.0
                else:
                    if dv.x >= -dv.y:
                        self.current_gate.rotation_degrees = 180.0
                    else:
                        self.current_gate.rotation_degrees = 90.0
            else:
                if dv.y >= 0:
                    if -dv.x >= dv.y:
                        self.current_gate.rotation_degrees = 0.0
                    else:
                        self.current_gate.rotation_degrees = 270.0
                else:
                    if -dv.x >= -dv.y:
                        self.current_gate.rotation_degrees = 0.0
                    else:
                        self.current_gate.rotation_degrees = 90.0

    def _ready(self):
        self.gameplay = self.get_parent()
        self.rocks_node = self.get_node('Rocks')
        self.gates_node = self.get_node('Gates')

        self.rocks_array = []
        for iy in range(TILE_COUNT):
            for ix in range(TILE_COUNT):
                y = (iy + 0.5) * TILE_SIZE
                x = (ix + 0.5) * TILE_SIZE
                rock = RockScene.instance()
                self.rocks_array.append(rock)
                self.rocks_node.add_child(rock)
                rock.position = Vector2(x , y)
                rock.cell_x, rock.cell_y = ix, iy
        self.quantum_rocks = {}
        self.quantum_rocks_inv = []
        self.quantum_gates = []
        self.quantum_operations = []

        self.set_process(True)