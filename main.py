from processes.weather.weather import main as weather_main
from processes.speed.speed import main as speed_main
from processes.screens.screens import main as screens_main
from processes.photos.photos import main as photos_main
from processes.music.music import main as music_main
from processes.backups.backups import main as backups_main
import tkinter as tk
from PIL import Image, ImageTk
from multiprocessing import Process, Queue, freeze_support
from datetime import datetime
from importlib import import_module
import logging





class Parent:

    def __init__(self):
        """
        Initialize the Swiftsync application.

        This method sets up the Swiftsync application, including configuring logging, creating
        necessary data structures, configuring the GUI, and displaying the main window.

        """
        logging.basicConfig(level=logging.INFO, filename='swiftsync.log', filemode='a', format='[%(asctime)s][%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        
        self.queue = Queue()
        self.processes = {}
        self.status_dot = {}
        self.labels = {}
        self.buttons = {}

        self.root = tk.Tk()
        self.root.geometry("800x400")
        self.root.resizable(False, False)
        self.root.title("Swiftsync")
        self.root.iconbitmap(r'favicon.ico')
        self.root.protocol("WM_DELETE_WINDOW", self.stopServices)
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
        title_label = tk.Label(title_frame, text="Contact: dmonroe@killgorack.com", font=self.texta, bg='black', fg='#cccccc')
        title_label.pack()





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
            self.processes[process_name].terminate()
            self.processes[process_name].join()
            del self.processes[process_name]
            self.status_dot[process_name].itemconfig(1, fill='light gray')
            logging.info(f"Swiftsync: process '{process_name}' stopped.")
            button.config(text="Stopped")
        else:
            process_module = import_module(f"processes.{process_name}.{process_name}")
            process_func = getattr(process_module, 'main')
            self.processes[process_name] = Process(target=process_func, args=(self.queue,))
            self.processes[process_name].start()
            self.status_dot[process_name].itemconfig(1, fill='green')
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
        for process in self.processes.values():
            process.terminate()
            process.join()
            logging.info(f"Swiftsync: Terminated process {process}")
        self.root.destroy()





    def update_labels(self):
        """
        Update labels and status dots based on messages received from the queue.

        This function retrieves messages from the queue and updates the GUI labels and status dots
        according to the message's content.

        """
        while not self.queue.empty():
            message = self.queue.get()
            self.labels[message['name']].config(
                text=f"[{message['name']}] - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {message['message']} ")
            if message['status'] == 'OK':
                self.status_dot[message['name']].itemconfig(1, fill='green')
                logging.info(f"{message['name']}: {message['message']}")
            elif message['status'] == 'NOK':
                self.status_dot[message['name']].itemconfig(1, fill='red')
                logging.error(f"{message['name']}: {message['message']}")
            elif message['status'] == 'COK':
                self.status_dot[message['name']].itemconfig(1, fill='yellow')
                logging.warn(f"{message['name']}: {message['message']}")
        self.root.after(1000, self.update_labels)





    def checkProcesses(self):
        """
        Check the status of running processes and log if any have terminated unexpectedly.

        This function iterates through the running processes and checks if any of them have
        terminated unexpectedly. If a process has terminated, it logs an error message.

        """
        for process_name, process in self.processes.items():
            if not process.is_alive():
                logging.error(f"Swiftsync: Process {process_name} has terminated unexpectedly")
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
    obj.startServices()
    obj.checkProcesses()