import threading
from collections import Counter
from time import sleep

import gi

from consts import (BREAK_TIME, ICON_PATH, NOTIFICATIONS, PAUSE_AMOUNT,
                    PAUSE_TIME, WORK_TIME)

gi.require_version("Gtk", "3.0")
gi.require_version("Wnck", "3.0")
gi.require_version("Notify", "0.7")
gi.require_version('GdkPixbuf', '2.0')

from gi.repository import GdkPixbuf, Gtk, Notify, Wnck  # noqa: E402


class Pydoro(Gtk.Window):

    # TODO: Rethink app data structure
    state = "idle"
    timer_thread = None
    pauses_taken = 0
    notifs_enabled = True
    screen = Wnck.Screen.get_default()
    active_windows = Counter()
    current_window = None

    def __init__(self):
        # TODO: Move init stuff to dedicated functions
        Gtk.Window.__init__(self, title="Pydoro")

        Notify.init("Pydoro")
        self.notifs = Notify.Notification.new("")
        image = GdkPixbuf.Pixbuf.new_from_file(ICON_PATH)
        self.notifs.set_image_from_pixbuf(image)
        self.set_icon(image)
        self.set_resizable(False)

        self.timer = WORK_TIME
        self.stop_timer = False

        self.set_border_width(10)

        main_grid = Gtk.Grid()
        main_grid.set_column_homogeneous(True)
        main_grid.set_row_homogeneous(True)
        self.add(main_grid)

        self.start_btn = Gtk.Button(label="Start")
        self.stop_btn = Gtk.Button(label="Stop")
        self.rst_btn = Gtk.Button(label="Reset")

        self.start_btn.connect("clicked", self.start)
        self.stop_btn.connect("clicked", self.stop)
        self.rst_btn.connect("clicked", self.reset)

        self.timer_lbl = Gtk.Label(label="{:02d}:{:02d}".format(
            *divmod(self.timer, 60)))
        self.state_lbl = Gtk.Label(label="Status:")
        self.state_val_lbl = Gtk.Label(label=self.state)
        self.pauses_lbl = Gtk.Label(label="Pauses:")
        self.pauses_val_lbl = Gtk.Label(label=self.pauses_taken)

        # TODO: Make design dynamic
        main_grid.attach(self.timer_lbl, 1, 0, 1, 1)
        main_grid.attach(self.start_btn, 0, 2, 1, 1)
        main_grid.attach(self.stop_btn, 1, 2, 1, 1)
        main_grid.attach(self.rst_btn, 2, 2, 1, 1)
        main_grid.attach(self.state_lbl, 0, 3, 1, 1)
        main_grid.attach(self.state_val_lbl, 2, 3, 1, 1)
        main_grid.attach(self.pauses_lbl, 0, 4, 1, 1)
        main_grid.attach(self.pauses_val_lbl, 2, 4, 1, 1)

    def start(self, widget):
        if self.state not in ("idle", "paused"):
            print('Timer already running!')
            return

        self.notify("work")
        print("Timer started")
        self.state = "working"
        self.state_val_lbl.set_label(self.state)
        self.timer_thread = threading.Thread(target=self.countdown)
        self.timer_thread.daemon = True
        self.timer_thread.start()

    def stop(self, widget):
        print("Timer stopped")
        self.state = "paused"
        self.state_lbl.set_label(self.state)
        if self.timer_thread:
            self.stop_timer = True
            self.timer_thread.join()
            self.timer_thread = None
        self.timer_lbl.set_label(
            "{:02d}:{:02d}".format(*divmod(self.timer, 60)))

    def reset(self, widget):
        print("Reset timer")
        self.timer = WORK_TIME
        self.timer_lbl.set_label(
            "{:02d}:{:02d}".format(*divmod(self.timer, 60)))

    def resolve_state(self):
        if self.state == "working":
            if self.pauses_taken == PAUSE_AMOUNT:
                self.notify("break")
                self.timer = BREAK_TIME
                self.state = "breaking"
                self.pauses_taken = 0
            else:
                self.notify("pause")
                self.timer = PAUSE_TIME
                self.state = "pausing"
                self.pauses_taken += 1
        elif self.state in ("breaking", "pausing"):
            self.notify("work")
            self.timer = WORK_TIME
            self.state = "working"
        self.state_val_lbl.set_label(self.state)
        self.pauses_val_lbl.set_label(str(self.pauses_taken))

    # TODO: Defninitely refactor this monster
    def countdown(self):
        while self.timer:
            if self.stop_timer:
                self.stop_timer = False
                return
            self.timer -= 1
            mins, secs = divmod(self.timer, 60)
            self.timer_lbl.set_label("{:02d}:{:02d}".format(mins, secs))
            self.handle_window_stats()
            sleep(1)
        self.resolve_state()
        self.timer_thread = threading.Thread(target=self.countdown)
        self.timer_thread.daemon = True
        self.timer_thread.start()

    def notify(self, notify_event):
        self.notifs.update("Pydoro", NOTIFICATIONS.get(notify_event))
        self.notifs.show()

    def handle_window_stats(self):
        self.current_window = self.screen.get_active_window().get_name()
        self.active_windows[self.current_window] += 1
        print(self.active_windows)


if __name__ == "__main__":
    win = Pydoro()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
    Notify.uninit()
