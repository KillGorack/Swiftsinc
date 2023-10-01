import sqlite3
import shutil
import os
import time
import schedule
from datetime import datetime
from multiprocessing import Queue

def backup_directory(sourcepath, archivepath, name, narchives, queue):
    if os.path.isdir(sourcepath):
        queue.put({
            'name': 'backups',
            'status': 'OK',
            'message': f"Backup of {name} started."
        })
        archivefile = os.path.join(
            archivepath, time.strftime("%Y%m%d-%H%M%S") + '.zip')
        if not os.path.exists(archivepath):
            os.makedirs(archivepath)
        shutil.make_archive(archivefile, 'zip', sourcepath)
        archives = sorted(os.listdir(archivepath), reverse=True)
        for archive in archives[narchives:]:
            os.remove(os.path.join(archivepath, archive))

        conn = sqlite3.connect('settings.db')
        c = conn.cursor()
        c.execute("UPDATE backups SET lastcomplete = ? WHERE name = ?",
                  (datetime.now(), name))
        conn.commit()
        conn.close()
        queue.put({
            'name': 'backups',
            'status': 'OK',
            'message': f"Backup of {name} completed."
        })

def main(queue):

    queue.put({
        'name': 'backups',
        'status': 'OK',
        'message': f"Service started."
    })

    def daily_check():
        conn = sqlite3.connect('settings.db')
        c = conn.cursor()
        c.execute('SELECT * FROM backups')
        rows = c.fetchall()

        for row in rows:
            name = row[0]
            sourcepath = row[1]
            archivepath = row[2]
            interval_days = row[3]
            lastcomplete = row[4]
            narchives = row[5]

            if not lastcomplete:
                backup_directory(sourcepath, archivepath, name, narchives, queue)
            else:
                days_since_last_backup = (
                    datetime.now() - datetime.strptime(lastcomplete, "%Y-%m-%d %H:%M:%S.%f")).days
                if days_since_last_backup >= interval_days:
                    backup_directory(sourcepath, archivepath, name, narchives, queue)

        conn.close()

    schedule.every().day.at("00:10").do(daily_check)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    queue = Queue()
    main(queue)