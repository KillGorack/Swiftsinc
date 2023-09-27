import sqlite3
import shutil
import os
import time
import schedule
from multiprocessing import Process, Queue
from datetime import datetime

def backup_directory(sourcepath, archivepath, name, queue):
    if os.path.isdir(sourcepath):
        archivefile = os.path.join(archivepath, time.strftime("%Y%m%d-%H%M%S") + '.zip')
        if not os.path.exists(archivepath):
            os.makedirs(archivepath)
        shutil.make_archive(archivefile, 'zip', sourcepath)
        queue.put({
            'name': 'backups',
            'status': 'OK',
            'message': f'Backup of {name} completed.'
        })

        archives = sorted(os.listdir(archivepath), reverse=True)
        for archive in archives[2:]:
            os.remove(os.path.join(archivepath, archive))

        conn = sqlite3.connect('settings.db')
        c = conn.cursor()
        c.execute("UPDATE backups SET lastcomplete = ? WHERE name = ?", (datetime.now(), name))
        conn.commit()
        conn.close()



def main(queue):

    queue.put({
        'name': 'backups',
        'status': 'OK',
        'message': "Service started."
    })

    conn = sqlite3.connect('settings.db')
    c = conn.cursor()
    c.execute("ALTER TABLE backups ADD COLUMN lastcomplete TIMESTAMP")
    c.execute('SELECT * FROM backups')
    rows = c.fetchall()

    for row in rows:
        name = row[0]
        sourcepath = row[1]
        archivepath = row[2]
        interval_days = row[3]
        lastcomplete = row[4]

        if not lastcomplete:
            Process(target=backup_directory, args=(sourcepath, archivepath, name, queue)).start()
        else:
            days_since_last_backup = (datetime.now() - datetime.strptime(lastcomplete, "%Y-%m-%d %H:%M:%S")).days
            if days_since_last_backup >= interval_days:
                schedule.every(interval_days).days.do(Process(target=backup_directory, args=(sourcepath, archivepath, name, queue)).start())

    while True:
        schedule.run_pending()
        time.sleep(60)

    conn.close()

if __name__ == "__main__":
    queue = Queue()
    main(queue)

