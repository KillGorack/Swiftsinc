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

        logging.basicConfig(level=logging.INFO, filename='swiftsync.log', filemode='a',
                            format='[%(asctime)s][%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

        self.queue = Queue()
        self.processes = {}

        self.root = tk.Tk()
        self.root.geometry("800x400")
        self.root.resizable(False, False)
        self.root.title("Swiftsync")
        self.root.iconbitmap(r'favicon.ico')
        self.root.protocol("WM_DELETE_WINDOW", self.stopServices)
        self.root.configure(background='black')
        self.texta = ("Courier", 10)
        self.textb = ("Courier", 16, "bold")

        title_frame = tk.Frame(self.root)
        title_frame.pack(side='top', pady=10)
        title_label = tk.Label(title_frame, text="Current Modules Loaded",
                               font=self.textb, bg='black', fg='#cccccc')
        title_label.pack()

        title_frame = tk.Frame(self.root)
        title_frame.pack(side='bottom', pady=10)
        title_label = tk.Label(title_frame, text="Contact: dmonroe@killgorack.com",
                               font=self.texta, bg='black', fg='#cccccc')
        title_label.pack()

        img = Image.open("swift.png")
        self.tk_img = ImageTk.PhotoImage(img)
        label = tk.Label(self.root, image=self.tk_img,
                         borderwidth=0, highlightthickness=0)
        label.place(x=0, y=0)

        self.status_dot = {}
        self.labels = {}

    def addService(self, process_name, row):
        try:
            process_module = import_module(
                f"processes.{process_name}.{process_name}")
            process_func = getattr(process_module, 'main')
            self.processes[process_name] = Process(
                target=process_func, args=(self.queue,))
            service_frame = tk.Frame(self.root, bg='#cccccc')
            service_frame.pack(fill='x')
            self.status_dot[process_name] = tk.Canvas(
                service_frame, width=20, height=20)
            self.status_dot[process_name].grid(row=row, column=0)
            self.status_dot[process_name].create_oval(
                6, 7, 16, 17, fill='yellow')
            self.labels[process_name] = tk.Label(
                service_frame, text="", anchor='w', justify='left', font=self.texta, bg='#cccccc')
            self.labels[process_name].grid(row=row, column=1, sticky='w')
        except ModuleNotFoundError:
            logging.error(
                f"No module named 'processes.{process_name}.{process_name}'")

    def startServices(self):
        for process in self.processes.values():
            try:
                process.start()
            except Exception as e:
                print(f"Error starting process: {e}")
        self.root.after(1000, self.update_labels)
        self.root.mainloop()

    def stopServices(self):
        for process in self.processes.values():
            process.terminate()
            process.join()
            logging.info(f"Terminated process {process}")
        self.root.destroy()

    def update_labels(self):
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


if __name__ == "__main__":
    freeze_support()
    obj = Parent()
    obj.addService("weather", 0)
    obj.addService("speed", 1)
    obj.addService("screens", 2)
    obj.addService("photos", 3)
    obj.addService("music", 4)
    obj.addService("backups", 5)
    obj.startServices()
