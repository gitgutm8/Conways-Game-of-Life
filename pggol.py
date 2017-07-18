import sys
import operator

import pygame as pg

import gol
from vectors import Vector


FPS = 30
TIMER_INIT = 200  # Zeit zum nächsten Update der Zellen in ms
TIMER_CHANGE = 10
TIMER_MIN, TIMER_MAX = 100, 300

LINES, COLS = 30, 50
BLOCK_SIZE = 20

# Es gibt sonst Probleme aufgrund anderer Tastaturstandards
_PLUS = 93
_MINUS = 47

TEXT_COLOR       = (  0,   0,   0)  # Schwarz
CELL_COLOR       = (  0, 200,  50)  # Grün
GAME_OVER_COLOR  = (155, 155, 155)  # Grau
BACKGROUND_COLOR = (255, 255, 255)  # Weiß

FONT_SIZE = 20


class PgGol:

    key_to_action = {
        pg.K_p: lambda self: self.start_game(),
        pg.K_q: lambda self: setattr(self, 'playing', False),
        pg.K_h: lambda self: self.toggle_help(),
        pg.K_r: lambda self: self.reset(),
        pg.K_s: lambda self: self.soft_reset(),
        pg.K_ESCAPE: lambda self: self.toggle_pause(),
        _MINUS: lambda self: self.change_timer(operator.lt, TIMER_MAX, operator.add),
        _PLUS: lambda self: self.change_timer(operator.gt, TIMER_MIN, operator.sub)
    }

    def __init__(self, lines, cols):
        pg.display.set_caption('Game of Life')
        self.clock = pg.time.Clock()
        self.block_size = BLOCK_SIZE
        self.world = pg.display.set_mode(Vector((cols, lines)) * self.block_size)
        self.screen = pg.display.get_surface()
        self.font = pg.font.Font('freesansbold.ttf', FONT_SIZE)
        self._size = (lines, cols)
        self.playing = False
        self.reset()

    @classmethod
    def from_file(cls, file, config_name, lines, cols):
        obj = cls(lines, cols)
        obj.cells = gol.from_file(file, config_name)
        return obj

    def reset(self):
        """
        Setzt ein vorübergegangenes Spiel auf den Ursprungszustand zurück.

        :return: None
        """
        if self.playing:
            return
        self.cells = set()
        self.texts = []
        self.time_passed = 0
        self.initialising = True
        self.playing = True
        self.paused = False
        self.in_help = False
        self.timer = TIMER_INIT

    def soft_reset(self):
        """
        Wie `self.reset`, benutzt aber vorherige Startkonfiguration als Ausgangspunkt.

        :return: None
        """
        if self.playing:
            return
        self.reset()
        self.cells = self.old_config

    def start_game(self):
        """
        Beginnt Simulation und speichert Startkonfiguration.

        :return: None
        """
        if self.initialising:
            self.initialising = False
            self.old_config = self.cells.copy()

    def run(self):
        """
        Die Game-Loop

        :return: None
        """
        while True:
            # Wir wollen Millisekunden
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
        """
        Kümmert sich um Zellen und aktuellen Status.

        :param dt: {int} Millisekunden seit letztem Tick
        :return: None
        """
        if not self.playing:
            return
        if self.in_help:
            self.alert_help()
        if self.paused:
            self.alert_paused()
        elif not self.initialising and self.cells_should_move(dt):
            gol.step(self.cells, *self._size)
            if not self.cells:
                self.playing = False

    def cells_should_move(self, dt):
        """
        Berechnet, ob es Zeit für einen Zellenzyklus ist.

        :param dt: {int} Millisekunden seit letztem Tick
        :return: bool
        """
        self.time_passed += dt
        if self.time_passed >= self.timer:
            self.time_passed -= self.timer
            return True
        return False

    def draw(self):
        """
        Zeichnet Zellen und Text, der zu sehen ist.

        :return: None
        """
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

        if not self.playing:
            self.draw_game_over()
        pg.display.update()

    def draw_text(self, text, pos, color=TEXT_COLOR):
        """
        Schreibe Text an beliebiger Position im Fenster.

        :return: None
        """
        self.screen.blit(self.font.render(text, 1, color), pos)

    def handle_mouse_input(self):
        """
        In der Initialisierungssphase werden bei einem Linksklick
        Zellen hinzugefügt/entfernt.

        :return: None
        """
        if not self.initialising:
            return
        pos = pg.mouse.get_pos()
        lclick = pg.mouse.get_pressed()[0]
        if lclick:
            scaled_pos = Vector(pos) // self.block_size
            try:
                self.cells.remove(scaled_pos)
            except KeyError:
                self.cells.add(scaled_pos)

    def handle_key_input(self, key):
        """
        Macht je nach gedrückter Taste etwas anderes.

        :param key: {int} Gedrückte Taste
        :return: None
        """
        act = self.key_to_action.get(key, lambda _: 0)
        act(self)

    def change_timer(self, cmp, cmp_with, op):
        """
        Erhöht oder senkt den Timer, der zwischen Zyklen läuft.

        :param cmp: {function} Vergleichsfunktion
        :param cmp_with: {int} Damit wird verglichen
        :param op: {function} Veränderung von `self.timer`
        :return: None
        """
        if cmp(self.timer, cmp_with):
            self.timer = op(self.timer, TIMER_CHANGE)

    def toggle_help(self):
        """
        De-/Aktiviert die Hilfe-Einblendungen.

        :return: None
        """
        self.in_help = not self.in_help

    def toggle_pause(self):
        """
        Un-/Pausiert die Simulation.

        :return: None
        """
        self.paused = not self.paused

    def alert_paused(self):
        """
        Fügt die Texte hinzu, die während dem pausierten Zustand
        angezeigt werden sollen.

        :return:None
        """
        self.texts.append(('Pausiert', (20, 5)))
        self.texts.append((f'Derzeitige ms pro Zyklus: {self.timer}', (20, 30)))

    def alert_help(self):
        """
        Fügt die Hilfe-Einblendungen gegebenenfalls hinzu.

        :return: None
        """
        self.texts.append(('+: Beschleunige Zyklen', (20, 80)))
        self.texts.append(('-: Verlangsame Zyklen', (20, 110)))
        self.texts.append(('esc: Pause', (20, 140)))
        self.texts.append(('p: Spiel Starten', (20, 170)))
        self.texts.append(('q: Spiel beenden', (20, 200)))

    def draw_game_over(self):
        """
        Zeichnet, was nach beenden der Simulation zu sehen ist.

        :return: None
        """
        self.screen.fill(GAME_OVER_COLOR)
        self.draw_text('Das Spiel ist vorbei!', (20, 10))
        self.draw_text('Drücke r, um nochmal zu spielen', (20, 40))
        self.draw_text('Drücke s, um die gleiche Konfiguration wie eben zu benutzen', (20, 70))


if __name__ == '__main__':
    pg.init()
    PgGol.from_file('examples.json', '54turns', LINES, COLS).run()
