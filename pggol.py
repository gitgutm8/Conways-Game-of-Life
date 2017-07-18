import sys
import json
import operator as oper
from functools import partial, wraps

import pygame as pg

import gol
from vectors import Vector


FPS = 30
TIMER_INIT = 200  # Zeit zum nächsten Update der Zellen in ms
TIMER_CHANGE = 10
TIMER_MIN, TIMER_MAX = 20, 300

_MAGIC_FACTOR = 4
LINES, COLS = 30 * _MAGIC_FACTOR, 50 * _MAGIC_FACTOR
BLOCK_SIZE = 20 // _MAGIC_FACTOR

_LEFT_MOUSE, _MIDDLE_MOUSE, _RIGHT_MOUSE = range(1, 4)

# Es gibt sonst Probleme aufgrund anderer Tastaturstandards
_PLUS = 93
_MINUS = 47

TEXT_COLOR       = (  0,   0,   0)  # Schwarz
CELL_COLOR       = (  0, 200,  50)  # Grün
GAME_OVER_COLOR  = (155, 155, 155)  # Grau
BACKGROUND_COLOR = (255, 255, 255)  # Weiß

FONT_SIZE = 20


def require_state(state, bool_=True):
    """
    Decorator 2. Ordnung, der die dekorierte Methode dann ausführt,
    wenn ein spezifiertes Attribut des Objektes, welche die Methode
    momentan bindet, den selben Wahrheitswert wie `bool_` hat.

    :param state: {str} Das zu überprüfende Attribut
    :param bool_: {bool} Bool'scher Wert, gegen den `state` gecheckt wird
    :return: {function} Decorator
    """
    def dec(method):
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            if getattr(self, state) == bool_:
                method(self, *args, **kwargs)
        return wrapper
    return dec


class PgGol:

    def __init__(self, lines, cols):
        pg.display.set_caption('Game of Life')
        self.clock = pg.time.Clock()
        self.block_size = BLOCK_SIZE
        self.world = pg.display.set_mode(Vector((cols, lines)) * self.block_size)
        self.screen = pg.display.get_surface()
        self.font = pg.font.Font('freesansbold.ttf', FONT_SIZE)
        self.timer = TIMER_INIT
        self._size = (lines, cols)
        self.playing = False
        self.reset()

    @classmethod
    def from_file(cls, file, config_name, lines, cols, middle=False):
        obj = cls(lines, cols)
        obj.cells = gol.from_file(file, config_name, lines, cols, middle)
        return obj

    @require_state('playing', False)
    def reset(self):
        """
        Setzt ein vorübergegangenes Spiel auf den Ursprungszustand zurück.

        :return: {None}
        """
        self.cells = set()
        self.texts = []
        self.time_passed = 0
        self.initialising = True
        self.playing = True
        self.paused = False
        self.in_help = False

    @require_state('playing', False)
    def soft_reset(self):
        """
        Wie `self.reset`, benutzt aber vorherige Startkonfiguration als Ausgangspunkt.

        :return: {None}
        """
        self.reset()
        self.cells = self.old_config

    @require_state('initialising')
    def start_game(self):
        """
        Beginnt Simulation und speichert Startkonfiguration.

        :return: {None}
        """
        self.initialising = False
        self.old_config = self.cells.copy()

    def run(self):
        """
        Die Game-Loop

        :return: {None}
        """
        callbacks = {
            pg.MOUSEBUTTONDOWN: self.handle_mouse_input,
            pg.KEYDOWN: self.handle_key_input,
            pg.QUIT: sys.exit
        }
        while True:
            # Wir wollen Millisekunden
            dt = self.clock.tick(FPS)
            for e in pg.event.get():
                # Schneller als dict.get
                if e.type in callbacks:
                    callbacks[e.type](e)
            self.update(dt)
            self.draw()

    @require_state('playing')
    def update(self, dt):
        """
        Kümmert sich um Zellen und aktuellen Status.

        :param dt: {int} Millisekunden seit letztem Tick
        :return: {None}
        """
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
        Zeichnet je nach Spielstatus verschiedene Sachen.

        :return: {None}
        """
        if not self.playing:
            # Leere übrige Texte, die sich eventuell angesammelt haben
            self.texts = []
            self.draw_game_over()
        else:
            self.screen.fill(BACKGROUND_COLOR)
            for cell in self.cells:
                rect = pg.Rect(Vector(cell) * BLOCK_SIZE, (BLOCK_SIZE, BLOCK_SIZE))
                pg.draw.rect(self.screen, CELL_COLOR, rect)

        self.draw_all_texts()
        pg.display.update()

    def draw_all_texts(self):
        while self.texts:
            text = self.texts.pop()
            if isinstance(text, (tuple, list)):
                self.draw_text(*text)
            elif isinstance(text, dict):
                self.draw_text(**text)

    def draw_text(self, text, pos, color=TEXT_COLOR):
        """
        Schreibe Text an beliebiger Position im Fenster.

        :return: {None}
        """
        self.screen.blit(self.font.render(text, 1, color), pos)

    @require_state('initialising')
    def handle_mouse_input(self, event):
        """
        In der Initialisierungssphase werden bei einem Linksklick
        Zellen hinzugefügt/entfernt.

        :param: {pygame.Event} Das Klickevent
        :return: {None}
        """
        pos = event.pos
        lclick = event.button == _LEFT_MOUSE
        if lclick:
            scaled_pos = Vector(pos) // self.block_size
            try:
                self.cells.remove(scaled_pos)
            except KeyError:
                self.cells.add(scaled_pos)

    def handle_key_input(self, event):
        """
        Macht je nach gedrückter Taste etwas anderes.

        :param event: {pygame.Event} Das Drückevent
        :return: {None}
        """
        key_to_action = {
            pg.K_p: self.start_game,
            pg.K_q: partial(setattr, self, 'playing', False),
            pg.K_h: self.toggle_help,
            pg.K_r: self.reset,
            pg.K_s: self.soft_reset,
            pg.K_o: self.save_to_file,
            pg.K_ESCAPE: self.toggle_pause,
            _MINUS: partial(self.change_timer, oper.lt, TIMER_MAX, oper.add),
            _PLUS: partial(self.change_timer, oper.gt, TIMER_MIN, oper.sub)
        }
        key = event.key
        action = key_to_action.get(key, lambda: 0)
        action()

    def change_timer(self, cmp, cmp_with, op):
        """
        Erhöht oder senkt den Timer, der zwischen Zyklen läuft.

        :param cmp: {function} Vergleichsfunktion
        :param cmp_with: {int} Damit wird verglichen
        :param op: {function} Veränderung von `self.timer`
        :return: {None}
        """
        if cmp(self.timer, cmp_with):
            self.timer = op(self.timer, TIMER_CHANGE)

    def toggle_help(self):
        """
        De-/Aktiviert die Hilfe-Einblendungen.

        :return: {None}
        """
        self.in_help = not self.in_help

    def toggle_pause(self):
        """
        Un-/Pausiert die Simulation.

        :return: {None}
        """
        self.paused = not self.paused

    @require_state('playing', False)
    def save_to_file(self, file='your_templates.json'):
        """
        Speichert aktuelle Startkonfiguration in eine .json Datei.
        
        :param file: {str} Dateiname/-pfad 
        :return: {None}
        """
        template = self.create_template()

        with open(file, 'rt') as f:
            configs = json.load(f)
        name = f'config{len(configs)}'
        configs[name] = {'template': template}
        with open(file, 'wt') as f:
            json.dump(configs, f)

        self.alert_save_success()

    def create_template(self):
        """
        Erstellt ein Template aus aktueller Ausgangskonfiguration.

        :return: {list<str>} Das Template
        """
        lines, cols = self._size
        template = []

        for y in range(lines):
            line = []
            for x in range(cols):
                symbol = ' '
                if (x, y) in self.old_config:
                    symbol = '#'
                line.append(symbol)
            template.append(''.join(line))
        return template

    def alert_paused(self):
        """
        Fügt die Texte hinzu, die während dem pausierten Zustand
        angezeigt werden sollen.

        :return: {None}
        """
        self.texts.append(('Pausiert', (20, 5)))
        self.texts.append((f'Derzeitige ms pro Zyklus: {self.timer}', (20, 30)))

    def alert_help(self):
        """
        Fügt die Hilfe-Einblendungen gegebenenfalls hinzu.

        :return: {None}
        """
        self.texts.append(('+: Beschleunige Zyklen', (20, 80)))
        self.texts.append(('-: Verlangsame Zyklen', (20, 110)))
        self.texts.append(('esc: Pause', (20, 140)))
        self.texts.append(('p: Spiel Starten', (20, 170)))
        self.texts.append(('q: Spiel beenden', (20, 200)))

    def alert_save_success(self):
        # TODO: Show a message upon saving

        # this doesn't work
        self.texts.append(('Speichern erfolgreich', (20, 130)))

    def draw_game_over(self):
        """
        Zeichnet, was nach beenden der Simulation zu sehen ist.

        :return: {None}
        """
        self.screen.fill(GAME_OVER_COLOR)
        self.texts.append(('Das Spiel ist vorbei!', (20, 10)))
        self.texts.append(('Drücke r, um nochmal zu spielen', (20, 40)))
        self.texts.append(('Drücke s, um die gleiche Konfiguration wie eben zu benutzen', (20, 70)))
        self.texts.append(('Drücke o, um deine Startkonfiguration in'
                           ' "your_templates.json" abzuspeichern', (20, 100)))


if __name__ == '__main__':
    pg.init()
    #PgGol(LINES, COLS).run()
    PgGol.from_file('examples.json', 'glidergun', LINES, COLS).run()
