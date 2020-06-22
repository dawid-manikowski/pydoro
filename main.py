import gi
from gi.repository import Gtk, Notify, GdkPixbuf
import threading
from time import sleep

gi.require_version("Gtk", "3.0")


WORK_TIME = 1 * 30
PAUSE_TIME = 1 * 15
BREAK_TIME = 1 * 30
ICON_PATH = "./788502_1.jpg"


class Pydoro(Gtk.Window):

    state = "idle"
    timer_thread = None
    pauses_taken = 0

    def __init__(self):
        Gtk.Window.__init__(self, title="Pydoro")

        Notify.init("Pydoro")
        self.notifs = Notify.Notification.new("")
        image = GdkPixbuf.Pixbuf.new_from_file(ICON_PATH)
        self.notifs.set_image_from_pixbuf(image)
        self.set_icon(image)

        self.timer = WORK_TIME
        self.stop_timer = False

        self.set_border_width(10)

        main_grid = Gtk.Grid()
        self.add(main_grid)

        self.start_btn = Gtk.Button(label="Start")
        self.stop_btn = Gtk.Button(label="Stop")
        self.rst_btn = Gtk.Button(label="Reset")

        self.start_btn.connect("clicked", self.start)
        self.stop_btn.connect("clicked", self.stop)
        self.rst_btn.connect("clicked", self.reset)

        self.timer_lbl = Gtk.Label("{:02d}:{:02d}".format(*divmod(self.timer, 60)))
        self.state_lbl = Gtk.Label(self.state)

        main_grid.attach(self.timer_lbl, 0, 0, 3, 2)
        main_grid.attach(self.state_lbl, 0, 4, 3, 1)
        main_grid.attach(self.start_btn, 0, 3, 1, 1)
        main_grid.attach(self.stop_btn, 1, 3, 1, 1)
        main_grid.attach(self.rst_btn, 2, 3, 1, 1)

    def start(self, widget):
        if self.state not in ("idle", "paused"):
            print('Timer already running!')
            return
        self.notifs.update("Pydoro", "Timer started! Keep focus!")
        self.notifs.show()
        print("Timer started")
        self.state = "working"
        self.state_lbl.set_label(self.state)
        self.timer_thread = threading.Thread(target=self.countdown)
        self.timer_thread.daemon = True
        self.timer_thread.start()

    def stop(self, widget):
        print("Timer stopped")
        self.state = "paused"
        self.state_lbl.set_label(self.state)
        if self.timer_thread:
            self.notifs.update("Pydoro", "Timer stopped")
            self.notifs.show()
            self.stop_timer = True
            self.timer_thread.join()
            self.timer_thread = None
        self.timer_lbl.set_label("{:02d}:{:02d}".format(*divmod(self.timer, 60)))

    def reset(self, widget):
        print("Reset timer")
        self.timer = 25 * 60
        self.timer_lbl.set_label("{:02d}:{:02d}".format(*divmod(self.timer, 60)))

    def countdown(self):
        while self.timer:
            if self.stop_timer:
                self.stop_timer = False
                return
            self.timer -= 1
            mins, secs = divmod(self.timer, 60)
            self.timer_lbl.set_label("{:02d}:{:02d}".format(mins, secs))
            sleep(1)
        if self.pauses_taken == 4:
            self.pauses_taken = 0
            self.timer = BREAK_TIME
            self.state = "breaking"
            self.state_lbl.set_label(self.state)
        else:
            self.pauses_taken += 1
            self.timer = PAUSE_TIME
            self.state = "pausing"
            self.state_lbl.set_label(self.state)
        self.timer_thread = threading.Thread(target=self.countdown)
        self.timer_thread.daemon = True
        self.timer_thread.start()


win = Pydoro()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
Notify.uninit()
