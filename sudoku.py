#!/usr/local/bin/python
import itertools
import cProfile
import copy
import random
import logging

global recursion_level

recursion_level = 0


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class Cell:
    def __init__(self, row, col, parent, value = None):
        if value:
            self.possible_values = [value,]
            self.value = value
        else:
            self.possible_values = set()
            self.possible_values.update([1,2,3,4,5,6,7,8,9])
            self.value = None

        self.row = row
        self.col = col
        self.parent = parent
    
    def __unicode__(self):
        if not self.get_value():
            return ' '
        return "".join( str(c) for c in self.possible_values )

    def __str__(self):
        return self.__unicode__()

    def get_value(self):
        return self.value
    
    def set_value(self, value):
        if not value:
            return False
    
        self.value = value
        self.possible_values = set([value,])
        return all( peer.eliminate_value(self.get_value() ) for peer in self.get_peers() )

    def get_peers(self):
        return self.parent.get_peers(self)


    def eliminate_value(self, value):
        '''
        Remove a value from the list of possible values.
        If this cell is set to this value or this value is not in the list of possible values, return False.
        Otherwise return True
        '''
        if not value or value not in self.possible_values:
            return True

        if self.get_value() == value:
            #print "Cell %d,%d already has value %d. Can't eliminate it" % (self.row, self.col, value)
            return False
        elif len(self.possible_values) == 1:
            #print "Can't remove last possible value from cell %d,%d" % (self.row, self.col)
            return False

        # remove the value from this cell
        self.possible_values.remove(value)
        # if this cell is down to only one possible value, assign it and attempt to remove it from the peers
        if len(self.possible_values) == 1:
            self.set_value(self.possible_values[0])
            # try removing it from the peers
            #print "Only one option remaining (%d) for cell %d,%d. Propagating elimination" % (self.get_value(), self.row, self.col)
            return all( peer.eliminate_value( self.get_value() ) for peer in self.get_peers() )

        return True


class Grid:
    def __init__(self, grid = None):
        print "Initializing grid..."
        self.cells=[ Cell(row, col, self) for row in range(9) for col in range(9) ]

        #self.rows = [[ self.cells[row][i] for i in range(9)] for row in range(9) ]
        #self.cols = [[ self.cells[i][col] for i in range(9)] for col in range(9) ]

        #self.subgrids = []
        #for start_row in (0,3,6):
        #    for start_col in (0,3,6):
        #        #print "adding subgrid %d,%d" % (start_row, start_col)
        #        self.subgrids.append(
        #                [ self.cells[row][col] for row in range(start_row, start_row + 3) for col in range(start_col, start_col + 3) ]
        #                )

        #print "%d subgrids" % len(self.subgrids)
        #for sg in self.subgrids:
        #    print sg

        #self.all_units = self.rows + self.cols + self.subgrids

        #self.all_cells = []
        #for row in range(9):
        #    self.all_cells += self.cells[row] 

        #for cell in self.get_all_cells():
        #    cell.peers = set(self.get_row(cell.row) + self.get_col(cell.col) + self.get_subgrid_for_cell(cell))#.remove(cell)
        #    cell.peers.remove(cell)
            #print "cell %d,%d has %d peers:" % (cell.row, cell.col, len(cell.peers))
            #for c in cell.peers:
            #    print " > %d,%d" % (c.row, c.col)


        if grid:
            self.parse_grid(grid)

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        cells_in_conflict = self.find_conflicts()
        width = 0
        for i in range(9):
            for j in range(9):
                w = len(str(self.cells[i * 9 + j])) + 1
                if cells_in_conflict and self.cells[i][j] in cells_in_conflict:
                    w += 2
                width = max(width, w)

        out=''
        for i in range(9):
            row = ''
            for j in range(9):
                cell = str(self.cells[i*9 + j])
                if cells_in_conflict and self.cells[i][j] in cells_in_conflict:
                    cell = '-' + cell + '-'
                out += cell.center(width)
                if j in (2,5): out += "| "
            out += '\r\n'
            if i in (2, 5): out += ''.join(['-' * (width * 3 + 1)] * 3) + "\n"
    
        return out

    def get_row(self, row):
        #return self.rows[row]
        return [ self.cells[row * 9 + i] for i in range(9) ]

    def get_col(self, col):
        #return self.cols[col]
        return [ self.cells[ i * 9 + col ] for i in range(9) ]

    def get_subgrid(self, subgrid):
        # subgrid = 1, we want [0-2][0-2]
        # subgrid = 2, we want [0-2][3-5]
        start_row = int(subgrid/3) * 3
        start_col = (subgrid % 3) * 3
        return [ self.cells[i * 9 + j] for i in range(start_row, start_row + 3) for j in range(start_col, start_col + 3) ]

    def get_subgrid_for_cell(self, cell):
        return self.get_subgrid( int(cell.row / 3) * 3 + int(cell.col / 3) )

    def get_all_cells(self):
        #all_cells = []
        #for row in range(9):
        #    all_cells += self.cells[row] 
        return self.cells

    def get_all_units(self):
        return [ self.get_row(i) + self.get_col(i) + self.get_subgrid(i) for i in range(9) ]

    def set_cell(self, cell, value):
        '''
        Set the value for a cell. If it can't be done because it conflicts with
        other cells in the row/col/subgrid of this cell or the value is not in 
        the possible values for the cell, return False. Otherwise, return True
        '''
        for unit in self.get_units_for_cell(cell):
            for c in unit:
                if c.get_value() == value:
                    return False
        
        if value not in cell.possible_values:
            return False
        
        return cell.set_value(value)

    def get_units_for_cell(self, cell):
        units = []
        units += self.get_row(cell.row) 
        units += self.get_col(cell.col)
        units += self.get_subgrid_for_cell(cell)
        return units
        #return [ self.get_row(cell.row) + self.get_col(cell.col) + self.get_subgrid_for_cell(cell) ]

    def get_peers(self, cell):
        peers = set(self.get_units_for_cell(cell))
        if cell in peers:
            peers.remove(cell)
        return peers

    def reduce_unit(self, unit):
        for cell in unit:
            val = cell.get_value()
            if not val:
                continue

            for peer in unit:
                if cell == peer:
                    continue
                if val in peer.possible_values:
                    if not peer.eliminate_value(val):
                        return False

        return True


    def solve(self):
        self.reduce()

        if self.search():
            print self
            return True
        else:
            print "No solution!"
            return False

    def reduce_from_cell(self, cell):
        val = cell.get_value()
        if not val:
            return True

        #print "Reducing from cell %d,%d (%s)" % (cell.row, cell.col, cell)

        for peer in self.get_peers(cell):
            if val in peer.possible_values:
                #print "Eliminating value %d from cell %d,%d (%s)" % (val, peer.row, peer.col, peer)
                if not peer.eliminate_value(val):
                    #print "Couldn't eliminate %d from cell %d,%d" % (val, peer.row, peer.col)
                    return False

        return True

    def reduce(self):
        return all (self.reduce_from_cell(cell) for cell in self.get_all_cells())


    def get_unsolved_cells(self):
        unsolved_cells = []

        for cell in self.get_all_cells():
            if not cell.get_value():
                #print "adding %d,%d to unsolved cells" %(cell.row, cell.col)
                unsolved_cells.append(cell)
        # sort by increasing number of options
        unsolved_cells.sort(key=lambda x: len(x.possible_values))

        return unsolved_cells

    def search(self, unsolved_cells = None):
        global recursion_level 

        # if no list of unsolved cells was provided, create one
        if not unsolved_cells or len(unsolved_cells) == 0:
            unsolved_cells = self.get_unsolved_cells()

        if len(unsolved_cells) == 0:
            return True

        cell = unsolved_cells[0]

        #print "Working on cell %d,%d (%s)" % (cell.row, cell.col, cell)

        # save the original possible values
        original_possible_values = cell.possible_values[:]
        unsolved_cells.remove(cell)

        # try the possible values at random and continue to recurse
        while len(cell.possible_values) > 0:
            #print "recursion level = %d" % recursion_level
            #val = random.choice(list(cell.possible_values))
            val = cell.possible_values[0]

            #print "Attempting %d in cell %d,%d (%s)" % (val, cell.row, cell.col, cell)

            # make a copy to work on
            g = copy.deepcopy(self)

            # set the cell value
            g_cell = g.cells[cell.row * 9 + cell.col]
            g_cell.set_value(val)

            # if we run into a conflict, try another value
            if not g.reduce_from_cell(g_cell):
                #print "Couldn't assign value %d to %d,%d due to conflict" % (val, cell.row, cell.col)
                cell.possible_values.remove(val)
                continue


            #print g
            #print "recursion level = %d" % recursion_level
            #raw_input("Press enter...")


            recursion_level += 1

            # if we're solved, return True
            if g.is_solved() or g.search(unsolved_cells):
                self.cells = g.cells
                return True
            else:
                #print "Conflict resulting from %d in cell %d,%d. Removing value %d from cell %d,%d" % (val, cell.row, cell.col, val, cell.row, cell.col)
                cell.possible_values.remove(val)

            recursion_level -= 1

        # when we move to the next cell, restore the possible values here
        #print "No more values for cell %d,%d. Restoring originals" % (cell.row, cell.col)
        cell.possible_values = original_possible_values
        #unsolved_cells.append(cell)

        # we're out of things to try and no solution
        #print "Out of options and no solution! Returning False"
        return False

    def is_unit_solved(self, unit):
        for cell in unit:
            val = cell.get_value()

            # if this cell doesn't have a final value yet, we're not solved
            if not val:
                return False 

            # if we find a conflict, return False
            for peer in unit:
                if cell != peer:
                    if peer.get_value() == val:
                        # conflict
                        return False

        return True


    def is_solved(self):
        return all(self.is_unit_solved(unit) for unit in self.get_all_units())
        

    def find_conflicts(self):
        cells_in_conflict = set()
        for cell in self.get_all_cells():
            #print len(self.get_all_cells())
            if cell.get_value() != None: # and cell not in cells_in_conflict:
                for peer in self.get_peers(cell):
                    if cell.get_value() == peer.get_value():
                        cells_in_conflict.add(cell)
                        cells_in_conflict.add(peer)


    def parse_grid(self, grid):
        if len(grid) != 81:
            print "Invalid grid (length %d)" % len(grid)
            return False
        
        for i in range(len(grid)):
            self.cells[ i ].possible_values = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        
        for i in range(len(grid)):
            c = grid[i];
            
            if c in '123456789':
                self.cells[i].set_value(int(c))
            elif c in '.0':
                pass
            else:
                print "Invalid grid character: %c" % c
                return False

        print "Grid parsed"
        return True

grids = [
            "003020600900305001001806400008102900700000008006708200002609500800203009005010300",
            "4.....8.5.3..........7......2.....6.....8.4......1.......6.3.7.5..2.....1.4......",
            "52...6.........7.13...........4..8..6......5...........418.........3..2...87.....",
            "6.....8.3.4.7.................5.4.7.3..2.....1.6.......2.....5.....8.6......1....",
            "48.3............71.2.......7.5....6....2..8.............1.76...3.....4......5....",
            "....14....3....2...7..........9...3.6.1.............8.2.....1.4....5.6.....7.8...",
            "......52..8.4......3...9...5.1...6..2..7........3.....6...1..........7.4.......3.",
            "6.2.5.........3.4..........43...8....1....2........7..5..27...........81...6.....",
            ".524.........7.1..............8.2...3.....6...9.5.....1.6.3...........897........",
            "6.2.5.........4.3..........43...8....1....2........7..5..27...........81...6.....",
            ".923.........8.1...........1.7.4...........658.........6.5.2...4.....7.....9.....",
            "6..3.2....5.....1..........7.26............543.........8.15........4.2........7..",
            ".6.5.1.9.1...9..539....7....4.8...7.......5.8.817.5.3.....5.2............76..8...",
            "..5...987.4..5...1..7......2...48....9.1.....6..2.....3..6..2.......9.7.......5..",
            "3.6.7...........518.........1.4.5...7.....6.....2......2.....4.....8.3.....5.....",
            "1.....3.8.7.4..............2.3.1...........958.........5.6...7.....8.2...4.......",
            "6..3.2....4.....1..........7.26............543.........8.15........4.2........7..",
            "....3..9....2....1.5.9..............1.2.8.4.6.8.5...2..75......4.1..6..3.....4.6.",
            "45.....3....8.1....9...........5..9.2..7.....8.........1..4..........7.2...6..8..",
            ".237....68...6.59.9.....7......4.97.3.7.96..2.........5..47.........2....8.......",
            "..84...3....3.....9....157479...8........7..514.....2...9.6...2.5....4......9..56",
            ".98.1....2......6.............3.2.5..84.........6.........4.8.93..5...........1..",
            "..247..58..............1.4.....2...9528.9.4....9...1.........3.3....75..685..2...",
            "4.....8.5.3..........7......2.....6.....5.4......1.......6.3.7.5..2.....1.9......",
            ".2.3......63.....58.......15....9.3....7........1....8.879..26......6.7...6..7..4",
            "1.....7.9.4...72..8.........7..1..6.3.......5.6..4..2.........8..53...7.7.2....46",
            "4.....3.....8.2......7........1...8734.......6........5...6........1.4...82......",
            ".......71.2.8........4.3...7...6..5....2..3..9........6...7.....8....4......5....",
            "6..3.2....4.....8..........7.26............543.........8.15........8.2........7..",
            ".47.8...1............6..7..6....357......5....1..6....28..4.....9.1...4.....2.69.",
            "......8.17..2........5.6......7...5..1....3...8.......5......2..4..8....6...3....",
            "38.6.......9.......2..3.51......5....3..1..6....4......17.5..8.......9.......7.32",
            "...5...........5.697.....2...48.2...25.1...3..8..3.........4.7..13.5..9..2...31..",
            ".2.......3.5.62..9.68...3...5..........64.8.2..47..9....3.....1.....6...17.43....",
            ".8..4....3......1........2...5...4.69..1..8..2...........3.9....6....5.....2.....",
            "..8.9.1...6.5...2......6....3.1.7.5.........9..4...3...5....2...7...3.8.2..7....4",
            "4.....5.8.3..........7......2.....6.....5.8......1.......6.3.7.5..2.....1.8......",
            "1.....3.8.6.4..............2.3.1...........958.........5.6...7.....8.2...4.......",
            "1....6.8..64..........4...7....9.6...7.4..5..5...7.1...5....32.3....8...4........",
            "249.6...3.3....2..8.......5.....6......2......1..4.82..9.5..7....4.....1.7...3...",
            "...8....9.873...4.6..7.......85..97...........43..75.......3....3...145.4....2..1",
            "...5.1....9....8...6.......4.1..........7..9........3.8.....1.5...2..4.....36....",
            "......8.16..2........7.5......6...2..1....3...8.......2......7..3..8....5...4....",
            ".476...5.8.3.....2.....9......8.5..6...1.....6.24......78...51...6....4..9...4..7",
            ".....7.95.....1...86..2.....2..73..85......6...3..49..3.5...41724................",
            ".4.5.....8...9..3..76.2.....146..........9..7.....36....1..4.5..6......3..71..2..",
            ".834.........7..5...........4.1.8..........27...3.....2.6.5....5.....8........1..",
            "..9.....3.....9...7.....5.6..65..4.....3......28......3..75.6..6...........12.3.8",
            ".26.39......6....19.....7.......4..9.5....2....85.....3..2..9..4....762.........4",
            "2.3.8....8..7...........1...6.5.7...4......3....1............82.5....6...1.......",
            "6..3.2....1.....5..........7.26............843.........8.15........8.2........7..",
            "1.....9...64..1.7..7..4.......3.....3.89..5....7....2.....6.7.9.....4.1....129.3.",
            ".........9......84.623...5....6...453...1...6...9...7....1.....4.5..2....3.8....9",
            ".2....5938..5..46.94..6...8..2.3.....6..8.73.7..2.........4.38..7....6..........5",
            "9.4..5...25.6..1..31......8.7...9...4..26......147....7.......2...3..8.6.4.....9.",
            "...52.....9...3..4......7...1.....4..8..453..6...1...87.2........8....32.4..8..1.",
            "53..2.9...24.3..5...9..........1.827...7.........981.............64....91.2.5.43.",
            "1....786...7..8.1.8..2....9........24...1......9..5...6.8..........5.9.......93.4",
            "....5...11......7..6.....8......4.....9.1.3.....596.2..8..62..7..7......3.5.7.2..",
            ".47.2....8....1....3....9.2.....5...6..81..5.....4.....7....3.4...9...1.4..27.8..",
            "......94.....9...53....5.7..8.4..1..463...........7.8.8..7.....7......28.5.26....",
            ".2......6....41.....78....1......7....37.....6..412....1..74..5..8.5..7......39..",
            "1.....3.8.6.4..............2.3.1...........758.........7.5...6.....8.2...4.......",
            "2....1.9..1..3.7..9..8...2.......85..6.4.........7...3.2.3...6....5.....1.9...2.5",
            "..7..8.....6.2.3...3......9.1..5..6.....1.....7.9....2........4.83..4...26....51.",
            "...36....85.......9.4..8........68.........17..9..45...1.5...6.4....9..2.....3...",
            "34.6.......7.......2..8.57......5....7..1..2....4......36.2..1.......9.......7.82",
            "......4.18..2........6.7......8...6..4....3...1.......6......2..5..1....7...3....",
            ".4..5..67...1...4....2.....1..8..3........2...6...........4..5.3.....8..2........",
            ".......4...2..4..1.7..5..9...3..7....4..6....6..1..8...2....1..85.9...6.....8...3",
            "8..7....4.5....6............3.97...8....43..5....2.9....6......2...6...7.71..83.2",
            ".8...4.5....7..3............1..85...6.....2......4....3.26............417........",
            "....7..8...6...5...2...3.61.1...7..2..8..534.2..9.......2......58...6.3.4...1....",
            "......8.16..2........7.5......6...2..1....3...8.......2......7..4..8....5...3....",
            ".2..........6....3.74.8.........3..2.8..4..1.6..5.........1.78.5....9..........4.",
            ".52..68.......7.2.......6....48..9..2..41......1.....8..61..38.....9...63..6..1.9",
            "....1.78.5....9..........4..2..........6....3.74.8.........3..2.8..4..1.6..5.....",
            "1.......3.6.3..7...7...5..121.7...9...7........8.1..2....8.64....9.2..6....4.....",
            "4...7.1....19.46.5.....1......7....2..2.3....847..6....14...8.6.2....3..6...9....",
            "......8.17..2........5.6......7...5..1....3...8.......5......2..3..8....6...4....",
            "963......1....8......2.5....4.8......1....7......3..257......3...9.2.4.7......9..",
            "15.3......7..4.2....4.72.....8.........9..1.8.1..8.79......38...........6....7423",
            "..........5724...98....947...9..3...5..9..12...3.1.9...6....25....56.....7......6",
            "....75....1..2.....4...3...5.....3.2...8...1.......6.....1..48.2........7........",
            "6.....7.3.4.8.................5.4.8.7..2.....1.3.......2.....5.....7.9......1....",
            "....6...4..6.3....1..4..5.77.....8.5...8.....6.8....9...2.9....4....32....97..1..",
            ".32.....58..3.....9.428...1...4...39...6...5.....1.....2...67.8.....4....95....6.",
            "...5.3.......6.7..5.8....1636..2.......4.1.......3...567....2.8..4.7.......2..5..",
            ".5.3.7.4.1.........3.......5.8.3.61....8..5.9.6..1........4...6...6927....2...9..",
            "..5..8..18......9.......78....4.....64....9......53..2.6.........138..5....9.714.",
            "..........72.6.1....51...82.8...13..4.........37.9..1.....238..5.4..9.........79.",
            "...658.....4......12............96.7...3..5....2.8...3..19..8..3.6.....4....473..",
            ".2.3.......6..8.9.83.5........2...8.7.9..5........6..4.......1...1...4.22..7..8.9",
            ".5..9....1.....6.....3.8.....8.4...9514.......3....2..........4.8...6..77..15..6.",
            ".....2.......7...17..3...9.8..7......2.89.6...13..6....9..5.824.....891..........",
            "3...8.......7....51..............36...2..4....7...........6.13..452...........8..",
        ]


import time

def solve_all():
    results = [ ]
    solved = True
    for grid in grids:
        g = Grid(grid)
        print g
        t_start = time.clock()
        prof = cProfile.Profile()
        #solved = prof.runcall('g.solve()', globals(), locals() )
        cProfile.runctx('solved = g.solve()', globals(), locals() )
        #solved = g.solve()
        t_end = time.clock()
        delta = t_end - t_start
        print "%.4f seconds" % (delta)
        results.append({'solved': solved, 'time':delta })
        print '---------------------'

    for i in range(len(results)):
        if results[i]['solved']:
            stat = 'SOLVED'
        else:
            stat = 'NOT SOLVED'
        print "Puzzle %4d %s in %.4f seconds" % (i, stat, results[i]['time'])

    total = sum ( result['time'] for result in results if result['solved'] )
    print total

    print "AVG: %.4f" % (float(sum ( result['time'] for result in results if result['solved'] )) / len([ result for result in results if result['solved'] ]))
    print "MIN: %.4f" % (min ( result['time'] for result in results ))
    print "MAX: %.4f" % (max ( result['time'] for result in results ))



if __name__ == '__main__':
    solve_all()

