import gol
import pggol as pgol


def demo_cmd():
    lines, cols = 20, 20
    init = gol.from_file('examples.json', 'period15', lines, cols, middle=True)
    gol.sim(init, 20, 20, 30)
    init = gol.from_file('examples.json', 'pulsar', lines, cols, middle=True)
    gol.sim(init, 20, 20, 30)


def demo_pygame():
    pgol.pg.init()
    lines, cols = 100, 100
    demo = pgol.PgGol.from_file('examples.json', '54turns', lines, cols, middle=True)
    demo.initialising = False
    demo.run()

if __name__ == '__main__':
    inp = input('What do you want to see?\n1> demo in commandline\n2> demo in PyGame\n')
    {'1': demo_cmd, '2': demo_pygame}[inp]()
