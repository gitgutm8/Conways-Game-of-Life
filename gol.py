import time
import sys
import json
import os
from vectors import Vector


def step(cells, lines, columns):
    create = []
    die = []

    for x in range(columns):
        for y in range(lines):
            position = (x, y)
            neighbors = count_neighbors(position, cells)
            is_cell = position in cells
            if not is_cell and neighbors == 3:
                create.append(position)
            elif not 1 < neighbors < 4 and is_cell:
                die.append(position)

    """
    for position, state in grid.items():
        neighbors = count_neighbots(position, grid)
        is_cell = state == _ALIVE
        if not is_cell and neighbors == 3:
            create.append(position)
        elif not 1 < neighbors < 4 and is_cell:
            die.append(position)
            
    for new_cell in create:
        cells[new_cell] == _ALIVE
    for dying_cell in die:
        cells[dying_cell] == _DEAD
    """

    for new_cell in create:
        cells.add(new_cell)
    for dead_cell in die:
        cells.remove(dead_cell)


def display_grid(cells, lines, columns, default_symbol=' '):
    os.system('cls')
    for y in range(lines):
        for x in range(columns):
            symbol = default_symbol
            if (x, y) in cells:
                symbol = 'O'
            print(symbol, end='')
        print()


def shift_to_middle(template, lines, cols):
    mid_of_grid = Vector((cols // 2, lines // 2))
    longest_line = max(len(line) for line in template)
    mid_of_template = Vector((longest_line // 2, len(template) // 2))
    shift_per_point = mid_of_grid - mid_of_template
    return shift_per_point


def count_neighbors(position, cells):
    neighbors = [
        (-1, -1), (-1, 0), (-1, 1),
        ( 0, -1),          ( 0, 1),
        ( 1, -1), ( 1, 0), ( 1, 1)
    ]
    x, y = position
    return sum((x+dx, y+dy) in cells
               for dy, dx
               in neighbors
               # Innerhalb des Feldes
               if x+dx >= 0 and y+dy >= 0)


def parse_string(template, row_offset=0, col_offset=0, alive='#'):
    cells = set()
    for row_idx, row in enumerate(template):
        for col_idx, char in enumerate(row):
            if char is alive:
                cells.add((col_idx + col_offset,
                           row_idx + row_offset))
    return cells


def from_file(file, config_name, lines, cols, middle):
    with open(file, 'rt') as f:
        configs = json.load(f)
    config = configs[config_name]
    if middle:
        config['col_offset'],\
         config['row_offset'] = shift_to_middle(config['template'], lines, cols)
    return parse_string(**config)


def sim(cells, lines, columns, steps=None):
    if steps is None:
        while cells:
            sim(cells, lines, columns, 10)
    else:
        for _ in range(steps):
            step(cells, lines, columns)
            display_grid(cells, lines, columns)
            time.sleep(0.3)


if __name__ == '__main__':
    _init = set()
    if len(sys.argv) >= 3:
        _init = from_file(*sys.argv[1:3])
    _lines, _cols = 30, 150
    sim(_init, _lines, _cols)
