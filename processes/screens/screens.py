import os
import sqlite3
import requests
import sched
import shutil
import time
from datetime import datetime
from sqlite3 import Error
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from multiprocessing import Queue

class ScreenPoster:

    def __init__(self, queue):
        super(ScreenPoster, self).__init__()
        self.paths = {}
        self.settings = {}
        self.con = self.db()
        self.get_settings()
        self.get_paths()
        self.check_directories()
        self.queue = queue

    def db(self):
        db_file = os.path.join(os.getcwd(), "settings.db")
        con = None
        try:
            con = sqlite3.connect(db_file)
        except Error as e:
            self.queue.put({
                'name': 'screens',
                'status': 'NOK',
                'message': "Error " + e + "."
            })
        return con

    def get_settings(self):
        sql = "SELECT name, param FROM stg"
        cursor = self.con.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        for row in rows:
            self.settings[row[0]] = row[1]

    def get_paths(self):
        sql = "SELECT game, path FROM paths"
        cursor = self.con.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        for row in rows:
            self.paths[row[0]] = row[1]


    def check_directories(self):
        for game_name, path in self.paths.items():
            if os.path.exists(path):
                error_path = path + "_error"
                processed_path = path + "_processed"
                for new_path in [error_path, processed_path]:
                    if not os.path.exists(new_path):
                        os.makedirs(new_path)
            else:
                self.queue.put({
                    'name': 'screens',
                    'status': 'NOK',
                    'message': "Screenshot Path ERROR"
                })

    def check_paths(self):
        for game_name, path in self.paths.items():
            files = []
            for (_, _, filenames) in os.walk(path):
                files.extend(filenames)
                break
            for file in files:
                self.post_screenshot(file, path, game_name)

    def post_screenshot(self, file, s_path, game_name):
        success = True
        results = {}
        files = {'files': open(os.path.join(s_path, file), 'rb')}
        results['key'] = self.settings['apiKey']
        results['game'] = game_name
        results['formidentifier'] = self.settings['formIdent']
        url = self.settings['url'] + self.settings['apiKey']
        response = requests.post(url, files=files, data=results, verify=True)
        print(response.text)
        response.close()
        files['files'].close()
        self.file_mover(file, s_path, game_name)
        self.queue.put({
            'name': 'screens',
            'status': 'OK',
            'message': "Screenshot posted from " + game_name + "."
        })

    def file_mover(self, file, s_path, game_name):
        ext = os.path.splitext(file)[1]
        now = datetime.now()
        flnm = f"{game_name}-{now.strftime('%Y%m%d%H%M%S')}{ext}"
        to_loc = os.path.join(s_path, "_processed", flnm)
        shutil.copy(os.path.join(s_path, file), to_loc)
        self.file_kibash(os.path.join(s_path, file))

    def file_kibash(self, file_path):
        for _ in range(5):
            try:
                os.unlink(file_path)
                break
            except:
                time.sleep(5)

class MyHandler(FileSystemEventHandler):

    def __init__(self, screen_poster, game_name, path, post_delay):
        self.screen_poster = screen_poster
        self.game_name = game_name
        self.path = path
        self.post_delay = post_delay
        self.screen_poster.check_paths()

    def on_created(self, event):
        if not event.is_directory:
            file = os.path.basename(event.src_path)
            time.sleep(self.post_delay)
            self.screen_poster.post_screenshot(file, self.path, self.game_name)
            
def main(queue):

    queue.put({
        'name': 'screens',
        'status': 'OK',
        'message': "Service started."
    })
    
    sp = ScreenPoster(queue)
    s = sched.scheduler(time.time, time.sleep)

    post_delay = 5

    for game_name, path in sp.paths.items():
        event_handler = MyHandler(sp, game_name, path, post_delay)
        observer = Observer()
        observer.schedule(event_handler, path=path, recursive=False)
        observer.start()

    try:
        s.run()
    except KeyboardInterrupt:
        observer.stop()

    observer.join()

if __name__ == "__main__":
    queue = Queue()
    main(queue)
