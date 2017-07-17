import time
import sys
import json
from os import system


def step(cells, rows, columns):
    create = []
    die = []

    for x in range(columns):
        for y in range(rows):
            position = (x, y)
            neighbors = count_neighbors(position, cells)
            is_cell = position in cells
            if not is_cell and neighbors == 3:
                create.append(position)
            elif not 1 < neighbors < 4 and is_cell:
                die.append(position)

    for new_cell in create:
        cells.add(new_cell)
    for dead_cell in die:
        cells.remove(dead_cell)


def display_grid(cells, rows, columns, default_symbol=' '):
    system('cls')
    for y in range(rows):
        for x in range(columns):
            symbol = default_symbol
            if (x, y) in cells:
                symbol = 'O'
            print(symbol, end='')
        print()


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
                cells.add((col_idx + col_offset, row_idx + row_offset))
    return cells


def from_file(file, config_name):
    with open(file, 'rt') as f:
        configs = json.load(f)
    return parse_string(**configs[config_name])


def sim(cells, rows, columns, steps=None):
    if steps is None:
        while cells:
            sim(cells, rows, columns, 10)
    else:
        for _ in range(steps):
            step(cells, rows, columns)
            display_grid(cells, rows, columns)
            time.sleep(0.3)


if __name__ == '__main__':
    _init = set()
    if len(sys.argv) >= 3:
        _init = from_file(*sys.argv[1:3])
    _rows, _cols = 30, 150
    sim(_init, _rows, _cols)
