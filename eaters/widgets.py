import pudb
import heapq, time, random
import curses, _curses, urwid

from urwid.display_common import UNPRINTABLE_TRANS_TABLE, AttrSpec
from urwid.main_loop import MainLoop
from urwid.curses_display import Screen
from urwid.compat import bytes, chr2, B, bytes3, PYTHON3

class BufferScreen(Screen):
    def __init__(self):
        super(BufferScreen, self).__init__()
        self.ch_bufs = dict() # character buffers
        self.co_bufs = dict() # color buffers
        self.dirty = False

    def refresh(self):
        self.s.refresh()

    def clear_ch_bufs(self):
        for buffer in self.ch_bufs.values():
            buffer.clear()

    def clear_co_bufs(self):
        for buffer in self.co_bufs.values():
            buffer.clear()

    def clear_all_bufs(self):
        self.clear_ch_bufs()
        self.clear_co_bufs()

    def render_ch_buffer(self):
        buffer = dict()
        for buf in self.ch_bufs.values():
            if buf.keys():
                buffer.update(buf)
        return buffer

    def render_co_buffer(self):
        buffer = dict()
        for buf in self.co_bufs.values():
            if buf.keys():
                buffer.update(buf)
        return buffer

    def chbuf(self, name):
        if name in self.ch_bufs:
            return self.ch_bufs[name]
        else:
            newbuf = dict()
            self.ch_bufs[name] = newbuf
            return newbuf

    def cobuf(self, name):
        if name in self.co_bufs:
            return self.co_bufs[name]
        else:
            newbuf = dict()
            self.co_bufs[name] = newbuf
            return newbuf


    def start(self):
        super(BufferScreen, self).start()
        curses.init_pair(1, curses.COLOR_WHITE, -1)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_GREEN)
        curses.init_pair(3, curses.COLOR_GREEN, -1)

    def draw_buffer(self):
        for coord, tile in self.render_ch_buffer().items():
            y, x = coord
            self.s.addch(y, x, ord(tile.char), curses.color_pair(1))
        self.clear_ch_bufs()

    def draw_colors(self):
        for coord, color in self.render_co_buffer().items():
            y, x = coord
            self.s.chgat(y, x, 1, curses.color_pair(color))
        self.clear_co_bufs()

    def draw_screen(self, (cols, rows), r ):
        """Paint screen with rendered canvas."""
        if not self.dirty:
            return
        assert self._started
        
        assert r.rows() == rows, "canvas size and passed size don't match"
    
        y = -1
        for row in r.content():
            y += 1
            try:
                self.s.move( y, 0 )
            except _curses.error:
                # terminal shrunk? 
                # move failed so stop rendering.
                return
            
            first = True
            lasta = None
            nr = 0
            for a, cs, seg in row:
                bail = True
                for char in seg:
                    if char != chr(0):
                        bail = False
                if bail:
                    break
                if cs != 'U':
                    seg = seg.translate(UNPRINTABLE_TRANS_TABLE)
                    assert isinstance(seg, bytes)

                if first or lasta != a:
                    self._setattr(a)
                    lasta = a
                try:
                    if cs in ("0", "U"):
                        for i in range(len(seg)):
                            self.s.addch( 0x400000 +
                                ord(seg[i]) )
                    else:
                        assert cs is None
                        if PYTHON3:
                            assert isinstance(seg, bytes)
                            self.s.addstr(seg.decode('utf-8'))
                        else:
                            self.s.addstr(seg)
                except _curses.error:
                    # it's ok to get out of the
                    # screen on the lower right
                    if (y == rows-1 and nr == len(row)-1):
                        pass
                    else:
                        # perhaps screen size changed
                        # quietly abort.
                        return
                nr += 1
        if r.cursor is not None:
            x,y = r.cursor
            self._curs_set(1)
            try:
                self.s.move(y,x)
            except _curses.error:
                pass
        else:
            self._curs_set(0)
            self.s.move(0,0)
        
        self.keep_cache_alive_link = r
        self.dirty = False

    def _setattrat(self, a, y, x):
        if a is None:
            self.s.attrset(0)
            return
        elif not isinstance(a, AttrSpec):
            p = self._palette.get(a, (AttrSpec('default', 'default'),))
            a = p[0]

        if self.has_color:
            if a.foreground_basic:
                if a.foreground_number >= 8:
                    fg = a.foreground_number - 8
                else:
                    fg = a.foreground_number
            else:
                fg = 7

            if a.background_basic:
                bg = a.background_number
            else:
                bg = 0

            attr = curses.color_pair(bg * 8 + 7 - fg)
        else:
            attr = 0

        if a.bold:
            attr |= curses.A_BOLD
        if a.standout:
            attr |= curses.A_STANDOUT
        if a.underline:
            attr |= curses.A_UNDERLINE
        if a.blink:
            attr |= curses.A_BLINK

        self.s.chgat(y, x, attr)

class CursesBufferLoop(MainLoop):
    def __init__(self, *args, **kwargs):
        super(CursesBufferLoop, self).__init__(*args, **kwargs)

    def draw_screen(self):
        """
        Renter the widgets and paint the screen.  This function is
        called automatically from run() but may be called additional
        times if repainting is required without also processing input.
        """
        if not self.screen_size:
            self.screen_size = self.screen.get_cols_rows()

        canvas = self._topmost_widget.render(self.screen_size, focus=True)
        
        self.screen.draw_screen(self.screen_size, canvas)
        cy, cx = self.screen.s.getyx()
        self.screen.draw_buffer()
        self.screen.draw_colors()
        self.screen.s.move(cy, cx)
        self.screen.refresh()

    def _run_screen_event_loop(self):
        """
        This method is used when the screen does not support using
        external event loops.

        The alarms stored in the SelectEventLoop in self.event_loop 
        are modified by this method.
        """
        next_alarm = None

        while True:
            self.draw_screen()

            if not next_alarm and self.event_loop._alarms:
                next_alarm = heapq.heappop(self.event_loop._alarms)

            keys = None
            while not keys:
                if next_alarm:
                    sec = max(0, next_alarm[0] - time.time())
                    self.screen.set_input_timeouts(sec)
                else:
                    self.screen.set_input_timeouts(None)
                keys, raw = self.screen.get_input(True)
                if not keys and next_alarm: 
                    sec = next_alarm[0] - time.time()
                    if sec <= 0:
                        break

            keys = self.input_filter(keys, raw)
            
            if keys:
                self.process_input(keys)
            
            while next_alarm:
                sec = next_alarm[0] - time.time()
                if sec > 0:
                    break
                tm, callback = next_alarm
                callback()
                
                if self.event_loop._alarms:
                    next_alarm = heapq.heappop(self.event_loop._alarms)
                else:
                    next_alarm = None
            
            if 'window resize' in keys:
                self.screen_size = None

class BufferFill(urwid.SolidFill):
    def render(self, size, focus=False):
        self.size = size
        maxcol, maxrow = size
        return urwid.SolidCanvas(self.fill_char, maxcol, maxrow)

class EaterScreenWidget(urwid.WidgetWrap):
    def __init__(self, app):
        fourths = app.screen.s.getmaxyx()[1] / 4
        self.options = []
        self.buffer = BufferFill(chr(0))
        self.panel = ('fixed', 8, urwid.LineBox(
                urwid.Columns([
                        urwid.Pile([
                                urwid.SolidFill(random.choice(('1','2','3','4','5'))),
                                urwid.SolidFill(random.choice(('1','2','3','4','5'))),
                                urwid.SolidFill(random.choice(('1','2','3','4','5'))),]),
                        urwid.Pile([
                                urwid.SolidFill(random.choice(('1','2','3','4','5'))),
                                urwid.SolidFill(random.choice(('1','2','3','4','5'))),
                                urwid.SolidFill(random.choice(('1','2','3','4','5'))),]),
                        urwid.Pile([
                                urwid.SolidFill(random.choice(('1','2','3','4','5'))),
                                urwid.SolidFill(random.choice(('1','2','3','4','5'))),
                                urwid.SolidFill(random.choice(('1','2','3','4','5'))),]),])))
        display_widget = urwid.Pile([self.buffer, self.panel])
        urwid.WidgetWrap.__init__(self, display_widget)

class EaterScreenWidget(urwid.WidgetWrap):
    def __init__(self, app):
        fourths = app.screen.s.getmaxyx()[1] / 4
        self.options = []
        self.buffer = BufferFill(chr(0))
        self._text = urwid.Text("Starting...\n")
        self._edit = urwid.Edit(">")
        self.panel = ('fixed', 8, urwid.ListBox(urwid.SimpleListWalker([self._text, self._edit])))

        display_widget = urwid.Pile([self.buffer, self.panel])
        urwid.WidgetWrap.__init__(self, display_widget)

    def _get_text(self):
        return self._text.get_text()[0]

    def _set_text(self, val):
        self._text.set_text(val)
    text = property(_get_text, _set_text)

    def log(self, line):
        self.text = self.text + line + "\n"

    def get_command(self):
        txt = self._edit.get_edit_text()
        self._edit.set_edit_text('')
        return txt
