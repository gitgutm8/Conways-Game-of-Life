import gol

init = gol.from_file('examples.json', 'period15')
gol.sim(init, 20, 20)
