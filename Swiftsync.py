from processes.weather.weather import main as weather_main
from processes.speed.speed import main as speed_main
from processes.screens.screens import main as screens_main
from processes.photos.photos import main as photos_main
from processes.music.music import main as music_main
from processes.backups.backups import main as backups_main
from processes.scraper.scraper import main as scraper_main
import tkinter as tk
from multiprocessing import Process, Queue, freeze_support
from datetime import datetime
from importlib import import_module
import logging
import signal
import time
import os
import subprocess
import sqlite3





class Parent:





    def __init__(self):
        """
        Initialize the Swiftsync application.

        This method sets up the Swiftsync application, including configuring logging, creating
        necessary data structures, configuring the GUI, and displaying the main window.

        """
        logging.basicConfig(level=logging.ERROR, filename='swiftsync.log', filemode='a', format='[%(asctime)s][%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        

        self.queue = Queue()
        self.processes = {}
        self.status_dot = {}
        self.labels = {}
        self.buttons = {}
        self.response = {}
        self.supressMessages = False

        conn = sqlite3.connect('settings.db')
        cursor = conn.cursor()
        cursor.execute("SELECT param FROM stg WHERE name = 'reportBackTime'")
        record = cursor.fetchone()
        self.report_back_after_process_start = int(record[0])

        self.root = tk.Tk()
        self.root.geometry("800x400")
        self.root.resizable(False, False)
        self.root.title("Swiftsync 1.0")
        self.root.iconbitmap(r'favicon.ico')
        self.root.protocol("WM_DELETE_WINDOW", self.windowXCloser)
        self.root.configure(background='black')
        self.texta = ("Courier", 10)
        self.textb = ("Courier", 16, "bold")
        self.textc = ("Courier", 8, "bold")

        title_frame = tk.Frame(self.root)
        title_frame.pack(side='top', pady=10)
        title_label = tk.Label(title_frame, text="Current Modules Loaded", font=self.textb, bg='black', fg='#cccccc')
        title_label.pack()

        title_frame = tk.Frame(self.root)
        title_frame.pack(side='bottom', pady=10)
        title_label = tk.Label(title_frame, text="Contact: david.monroe@vw.com, please leave running.", font=self.texta, bg='black', fg='#cccccc')
        title_label.pack()

        log_button = tk.Button(self.root, text="Open Log", command=self.open_log)
        log_button.place(relx=1.0, rely=1.0, x=-5, y=-5, anchor='se')

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)





    def open_log(self):
        """
        Open the swiftsync.log file in Notepad.

        Args:
            none

        """
        subprocess.Popen(["notepad.exe", os.path.join(os.getcwd(), 'swiftsync.log')])





    def windowXCloser(self):
        """
        When closing the window, lets not log the termination of each process.

        Args:
            none

        """
        self.supressMessages = True
        self.stopServices()
        self.supressMessages = False


        


    def signal_handler(self, signum, frame):
        """
        This definition just cleans up zombies..

        Args:
            none

        """
        self.stopServices()





    def addService(self, process_name, row):
        """
        This function adds a service to the GUI and initializes its process.

        Args:
            process_name (str): The name of the process to add.
            row (int): The row in the GUI grid where the service should be placed.

        """
        try:
            process_module = import_module(f"processes.{process_name}.{process_name}")
            process_func = getattr(process_module, 'main')
            self.processes[process_name] = Process(target=process_func, args=(self.queue,))
            service_frame = tk.Frame(self.root, bg='#cccccc')
            service_frame.pack(fill='x')
            self.status_dot[process_name] = tk.Canvas(service_frame, width=20, height=20)
            self.status_dot[process_name].grid(row=row, column=0)
            self.status_dot[process_name].create_oval(6, 7, 16, 17, fill='yellow')
            self.buttons[process_name] = tk.Button(service_frame, text="Running", height=1, width=8, command=lambda: self.toggleProcess(process_name), font=self.textc)
            self.buttons[process_name].grid(row=row, column=1)
            self.labels[process_name] = tk.Label(service_frame, text="", anchor='w', justify='left', font=self.texta, bg='#cccccc')
            self.labels[process_name].grid(row=row, column=2, sticky='w')
        except ModuleNotFoundError:
            logging.error(f"Swiftsync: No module named '{process_name}'")





    def toggleProcess(self, process_name):
        """
        Toggle the specified process on or off.

        Args:
            process_name (str): The name of the process to toggle.

        """
        button = self.buttons[process_name]
        if process_name in self.processes and self.processes[process_name].is_alive():
            if process_name in self.response:
                del self.response[process_name]
            self.processes[process_name].terminate()
            self.processes[process_name].join()
            del self.processes[process_name]
            self.status_dot[process_name].itemconfig(1, fill='light gray')
            self.labels[process_name].config(text=f"[{process_name}] - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Process stopped.")
            logging.info(f"Swiftsync: process '{process_name}' stopped.")
            button.config(text="Stopped")
        else:
            self.queue.put({
                'name': process_name,
                'timeout': self.report_back_after_process_start
            })
            process_module = import_module(f"processes.{process_name}.{process_name}")
            process_func = getattr(process_module, 'main')
            self.processes[process_name] = Process(target=process_func, args=(self.queue,))
            self.processes[process_name].start()
            self.status_dot[process_name].itemconfig(1, fill='green')
            self.labels[process_name].config(text=f"[{process_name}] - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Process restarting.")
            logging.info(f"Swiftsync: process '{process_name}' restarted.")
            button.config(text="Running")





    def startServices(self):
        """
        Start all the processes in the 'processes' dictionary and begin updating labels.

        """
        for process in self.processes.values():
            try:
                process.start()
            except Exception as e:
                errMsg = f"Error starting process: {e}"
                logging.error(f"Swiftsync: {errMsg}")
        self.root.after(1000, self.update_labels)
        self.root.mainloop()





    def stopServices(self):
        """
        Terminate all running processes and close the application window.
        """
        for key, process in self.processes.items():
            if process.is_alive():
                process.terminate()
                process.join()
                logging.info(f"Swiftsync: Terminated process {key}")
        self.root.destroy()






    def signal_handler(self, signum, frame):
        """
        Handles signals triggered by the operating system. This method is used to perform cleanup activities 
        when the program receives signals indicating abandoned processes.

        Args:
            signum (int): The signal number that triggers the handler. Each signal (like SIGINT, SIGTERM, etc.) has a corresponding number.
            frame (frame): The current stack frame. It provides information about the code being executed when the signal occurred.

        Returns:
            None
        """
        self.stopServices()





    def update_labels(self):
        """
        Update labels and status dots based on messages received from the queue.

        This function retrieves messages from the queue and updates the GUI labels and status dots
        according to the message's content.

        """
        current_time = time.time()

        while not self.queue.empty():

            message = self.queue.get()

            if 'status' in message:
                self.labels[message['name']].config(text=f"[{message['name']}] - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {message['message']} ")
                if message['status'] == 'OK':
                    self.status_dot[message['name']].itemconfig(1, fill='green')
                    logging.info(f"{message['name']}: {message['message']}")
                elif message['status'] == 'NOK':
                    self.status_dot[message['name']].itemconfig(1, fill='red')
                    logging.error(f"{message['name']}: {message['message']}")
                elif message['status'] == 'COK':
                    self.status_dot[message['name']].itemconfig(1, fill='yellow')
                    logging.warning(f"{message['name']}: {message['message']}")

            elif 'timeout' in message:
                if message['name'] in self.response:
                    del self.response[message['name']]

                self.response[message['name']] = time.time() + message['timeout'] * 60

        for process, timeout in self.response.items():

            if current_time > timeout:

                self.queue.put({
                    'name': process,
                    'status': 'NOK',
                    'message': f"Process has become unresponsive, attempting restart."
                })

                self.queue.put({
                    'name': process,
                    'timeout': self.report_back_after_process_start
                })

                self.processes[process].terminate()
                self.processes[process].join()
                del self.processes[process]
                process_module = import_module(f"processes.{process}.{process}")
                process_func = getattr(process_module, 'main')
                self.processes[process] = Process(target=process_func, args=(self.queue,))
                self.processes[process].start()

        self.root.after(1000, self.update_labels)





    def checkProcesses(self):
        """
        Check the status of running processes and log if any have terminated unexpectedly.

        This function iterates through the running processes and checks if any of them have
        terminated unexpectedly. If a process has terminated, it logs an error message.

        """
        for process_name, process in self.processes.items():
            if not process.is_alive():
                logging.info(f"Swiftsync: Process {process_name} has terminated.")
        self.root.after(1000, self.checkProcesses)





if __name__ == "__main__":
    """
    Entry point for the Swiftsync application.

    This block is executed when the script is run as the main program. It sets up the Parent object,
    adds and, starts the services, and initiates the process-checking loop.

    """
    freeze_support()
    obj = Parent()
    obj.addService("weather", 0)
    obj.addService("speed", 1)
    obj.addService("screens", 2)
    obj.addService("photos", 3)
    obj.addService("music", 4)
    obj.addService("backups", 5)
    obj.addService("scraper", 6)
    obj.startServices()
    obj.checkProcesses()