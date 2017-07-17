import sys
import operator
import pygame as pg
import gol


class Vector(tuple):

    def __add__(self, other): return Vector(v + w for v, w in zip(self, other))
    def __sub__(self, other): return Vector(v - w for v, w in zip(self, other))
    def __mul__(self, scalar): return Vector(scalar * v for v in self)
    def __rmul__(self, scalar):	return Vector(scalar * v for v in self)
    def __neg__(self): return -1 * self


FPS = 30
TIMER_INIT = 200  # Zeit zum nächsten Update der Zellen in ms
TIMER_CHANGE = 10
TIMER_MIN, TIMER_MAX = 100, 300

ROWS, COLS = 30, 50
BLOCK_SIZE = 20

# Es gibt sonst Probleme aufgrund anderer Tastaturstandards
_PLUS = 93
_MINUS = 47

TEXT_COLOR       = (  0,   0,   0)  # Schwarz
CELL_COLOR       = (  0, 200,  50)  # Grün
BACKGROUND_COLOR = (255, 255, 255)  # Weiß

FONT_SIZE = 20


class PgGol:

    key_to_action = {
        pg.K_p: lambda self: setattr(self, 'initialising', False),
        pg.K_q: lambda _: sys.exit(),
        pg.K_ESCAPE: lambda self: self.toggle_pause(),
        _PLUS: lambda self: self.change_timer(operator.lt, TIMER_MAX, operator.add),
        _MINUS: lambda self: self.change_timer(operator.gt, TIMER_MIN, operator.sub)
    }

    def __init__(self, lines, cols):
        pg.display.set_caption('Game of Life')
        self.clock = pg.time.Clock()
        self.block_size = BLOCK_SIZE
        self.world = pg.display.set_mode(Vector((cols, lines)) * self.block_size)
        self.screen = pg.display.get_surface()
        self.font = pg.font.Font('freesansbold.ttf', FONT_SIZE)
        self._size = (lines, cols)
        self.reset()

    def reset(self):
        self.cells = set()
        self.texts = []
        self.time_passed = 0
        self.initialising = True
        self.paused = False
        self.timer = TIMER_INIT

    def run(self):
        while True:
            dt = self.clock.tick(FPS)
            for e in pg.event.get():
                if e.type == pg.MOUSEBUTTONDOWN:
                    self.handle_mouse_input()
                elif e.type == pg.KEYDOWN:
                    self.handle_key_input(e.key)
                elif e.type == pg.QUIT:
                    sys.exit()
            self.update(dt)
            self.draw()

    def update(self, dt):
        if self.paused:
            self.alert_paused()
        elif not self.initialising and self.cells_should_move(dt):
            gol.step(self.cells, *self._size)
            if not self.cells:
                # TODO: Was passiert, wenn alle Zellen Tod sind
                #  zum Beispiel:
                #   - Irgendein Screen?
                #   - Einfach neustart?
                #   - Start config nocheinmal anzeigen?
                pass

    def cells_should_move(self, dt):
        self.time_passed += dt
        if self.time_passed >= self.timer:
            self.time_passed -= self.timer
            return True
        return False

    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)
        for cell in self.cells:
            rect = pg.Rect(Vector(cell) * BLOCK_SIZE, (BLOCK_SIZE, BLOCK_SIZE))
            pg.draw.rect(self.screen, CELL_COLOR, rect)
        while self.texts:
            text = self.texts.pop()
            if isinstance(text, (tuple, list)):
                self.draw_text(*text)
            elif isinstance(text, dict):
                self.draw_text(**text)
        pg.display.update()

    def draw_text(self, text, pos, color=TEXT_COLOR):
        """Schreibe Text an beliebiger Position im Fenster."""
        self.screen.blit(self.font.render(text, 1, color), pos)

    def handle_mouse_input(self):
        if not self.initialising:
            return
        pos = pg.mouse.get_pos()
        lclick = pg.mouse.get_pressed()[0]
        if lclick:
            scaled_pos = Vector(v // BLOCK_SIZE for v in pos)
            try:
                self.cells.remove(scaled_pos)
            except KeyError:
                self.cells.add(scaled_pos)

    def handle_key_input(self, key):
        act = self.key_to_action.get(key, lambda _: 0)
        act(self)

    def change_timer(self, cmp, cmp_with, op):
        if cmp(self.timer, cmp_with):
            self.timer = op(self.timer, TIMER_CHANGE)

    def toggle_pause(self):
        self.paused = not self.paused

    def alert_paused(self):
        self.texts.append(('Pausiert', (20, 0)))
        self.texts.append((f'Derzeitige ms pro Zyklus: {self.timer}', (20, 30)))


if __name__ == '__main__':
    pg.init()
    PgGol(ROWS, COLS).run()
