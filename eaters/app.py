
class CursesApp(object):

    def __init__(self, screen):
        self.screen = screen
        self.world = dict()
        self.peaters = list()
        self.populate_world()

    def _start_screen(self):
        # don't echo keypresses
        curses.noecho()
        # handle keypresses immediately
        curses.cbreak()
        # enable color rendering
        curses.start_color()
        # hide the cursor
        self.orig_curs_mode = curses.curs_set(0)
        # handle special characters
        self.screen.keypad(1)

    def _stop_screen(self):
        curses.curs_set(self.orig_curs_mode)
        self.screen.keypad(0)
        curses.nocbreak()
        curses.echo()
        curses.endwin()

    def populate_world(self):
        height, width = self.screen.getmaxyx()
        for y in range(height - 1):
            for x in range(width):
                tile = None
                if x == 0 or x == width - 1:
                    tile = Wall()
                elif y == 0 or y == height - 2:
                    tile = Wall()
                elif random.randint(0, 20) == 0:
                    tile = Plant()
                elif random.randint(0, 10) == 0:
                    tile = Peater(y, x)
                    self.peaters.append(tile)
                if tile:
                    self.world[(y, x)] = tile


    def _render_world(self):
        height, width = self.screen.getmaxyx()
        for y in range(height - 1):
            for x in range(width):
                tile = self.world.get((y, x), Space())
                self.screen.move(y, x)
                self.screen.addch(ord(tile.char))

    def handle_keys(self):
        pass

    def run(self):
        self._start_screen()
        iterations = 0
        running = True
        try:
            while running:
                for p in self.peaters:
                    p.update(self.world)
                self.screen.clear()
                self.handle_keys()
                self._render_world()
                self.screen.refresh()
                iterations += 1
                time.sleep(.1)
        except KeyboardInterrupt, e:
            self._stop_screen()
            print "%s iterations" % iterations
