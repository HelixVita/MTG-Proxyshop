"""
CONSOLE MODULES
"""
import ctypes
import os
import sys
import threading
import time
from traceback import print_tb
from typing import Union
import asynckivy as ak
from datetime import datetime as dt
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

from src.constants import con
from src.gui.updater import UpdatePopup
from src.settings import cfg, Singleton


class Console(BoxLayout):
    """
    Main console class
    """
    __metaclass__ = Singleton
    Builder.load_file(os.path.join(con.cwd, "src/kv/console.kv"))
    lines = 1

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not cfg.dev_mode:
            self.size_hint = (1, .58)

    def update(self, msg="", e=None, end="\n"):
        """
        Add text to console
        """
        output = self.ids.console_output

        # Enforce maximum number of lines
        if self.lines == 300:
            text = output.text.split("\n", 1)[1]
        else:
            text = output.text
            self.lines += 1

        # Add message to the output label
        output.text = f"{text}{msg}{end}"
        self.ids.viewport.scroll_y = 0
        if e:
            self.log_exception(e)

    def log_error(self, msg, card, template=None, e=None):
        """
        Log failed card in a log file.
        Then prompt error request
        """
        cur_time = dt.now().strftime("%m/%d/%Y %H:%M")
        log_text = f"{card} ({template}) [{cur_time}]\n" if template else f"{card} [{cur_time}]\n"
        with open(os.path.join(con.path_logs, "failed.txt"), "a", encoding="utf-8") as log:
            log.write(log_text)
        return self.error(msg, e)

    def error(self, msg, e=None, continue_msg="Continue to next card?"):
        """
        Display error, wait for user to cancel or continue.
        """
        # End waiting to cancel
        self.end_await()

        # Log exception if given
        if e:
            self.log_exception(e)

        # Are we in dev mode?
        if cfg.dev_mode:
            return False

        # Automatically skip to next card?
        if cfg.skip_failed:
            continue_msg = "Skipping this card!"

        # Notify user
        self.update(f"{msg}{continue_msg}")

        # Enable buttons
        self.ids.continue_btn.disabled = False
        self.ids.cancel_btn.disabled = False

        # Prompt user response
        result = True if cfg.skip_failed else self.ids.console_controls.wait()

        # Cancel or don't
        if not result:
            self.update("Understood! Canceling render operation.")

        # Disable buttons
        self.ids.continue_btn.disabled = True
        self.ids.cancel_btn.disabled = True
        return result

    def wait(self, msg):
        """
        Wait for user to continue.
        """
        self.end_await()
        self.update(msg)
        self.ids.continue_btn.disabled = False
        self.ids.console_controls.wait()
        self.ids.continue_btn.disabled = True
        return True

    def await_cancel(self, thr):
        """
        Await for user to cancel the operation.
        Auto-returns if the render finishes.
        """
        self.ids.console_controls.success = False
        self.ids.cancel_btn.disabled = False
        self.ids.console_controls.await_cancel()
        if not self.ids.console_controls.success:
            self.ids.cancel_btn.disabled = True
            App.get_running_app().enable_buttons()
            self.kill_thread(thr)
            self.update("Canceling render process!")
            sys.exit()
        return True

    def end_await(self):
        """
        Stops awaiting cancellation
        """
        self.ids.console_controls.success = True
        self.ids.console_controls.running = False
        self.ids.cancel_btn.disabled = True

    @staticmethod
    def log_exception(error: Union[Exception, str], log_file: str = "error.txt"):
        """
        Log python exception.
        """
        # Is this an Exception object?
        if not hasattr(error, '__traceback__'):
            return

        # Print the error for dev testing
        print_tb(error.__traceback__)
        print(f"  Reason: {str(error)}")

        # Add to log file
        cur_time = dt.now().strftime("%m/%d/%Y %H:%M")
        with open(os.path.join(con.path_logs, log_file), "a", encoding="utf-8") as log:
            log.write("============================================================================\n")
            log.write(f"> {cur_time}\n")
            log.write("============================================================================\n")
            print_tb(error.__traceback__, file=log)
            log.write(f"  Reason: {str(error)}\n")

    @staticmethod
    def kill_thread(thr: threading.Thread):
        """
        Kill current render thread.
        @param thr: Thread object to kill
        """
        thread_id = thr.ident
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)


class ConsoleOutput(Label):
    """
    Label displaying console output
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text = "Test mode enabled!\n" if cfg.dev_mode else "Let's make a proxy!\n"


class ConsoleControls(BoxLayout):
    """
    Console control buttons
    """
    running = True
    waiting = False
    success = True
    choice = False

    def wait(self):
        """
        Force wait until user makes a choice
        """
        self.waiting = True
        while self.waiting:
            time.sleep(.5)
        return self.choice

    def choose(self, confirm=True):
        """
        Define the response, end wait
        """
        if confirm:
            self.choice = True
        else:
            self.choice = False
            self.running = False
            self.success = False
        self.waiting = False

    def await_cancel(self):
        """
        Await for user cancelling during render process
        """
        self.running = True
        while self.running:
            time.sleep(1)
        return None

    @staticmethod
    async def check_for_updates():
        """
        Open updater Popup.
        """
        # We are Authenticated
        Updater = UpdatePopup()
        Updater.open()
        await ak.run_in_thread(Updater.check_for_updates, daemon=True)
        ak.start(Updater.populate_updates())
