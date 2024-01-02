import sqlite3
import shutil
import os
import schedule
from multiprocessing import Queue
import time

def backup_directory(sourcepath, archivepath, name, narchives, queue):

    try:
        if os.path.isdir(sourcepath):

            queue.put({
                'name': 'Backups',
                'status': 'OK',
                'message': f"Backup of {name} started."
            })

            filename = "{} Backup {}".format(name, time.strftime("%Y%m%d-%H%M%S"))
            archivefile = os.path.join(archivepath, filename)
            if not os.path.exists(archivepath):
                os.makedirs(archivepath)
            shutil.make_archive(archivefile, 'zip', sourcepath)
            archives = sorted(os.listdir(archivepath), reverse=True)
            for archive in archives[narchives:]:
                os.remove(os.path.join(archivepath, archive))

            queue.put({
                'name': 'Backups',
                'status': 'OK',
                'message': f"Backup of {name} completed."
            })

        else:

            queue.put({
                'name': 'Backups',
                'status': 'NOK',
                'message': f"Bad source directory defined."
            })

    except Exception as e:
        
        queue.put({
            'name': 'Backups',
            'status': 'Error',
            'message': str(e)
        })

def main(queue):

    queue.put({
        'name': 'Backups',
        'status': 'OK',
        'message': f"Service running, waiting."
    })

    def scheduler():

        with sqlite3.connect('settings.db') as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM backups')
            rows = c.fetchall()

            counter = 0

            for row in rows:
                name = row[0]
                sourcepath = row[1]
                archivepath = row[2]
                interval = row[3]
                narchives = row[4]

                if interval == 'day':
                    schedule.every().day.at("08:39").do(backup_directory, sourcepath, archivepath, name, narchives, queue)
                elif interval == 'week':
                    schedule.every().monday.at("01:00").do(backup_directory, sourcepath, archivepath, name, narchives, queue)
                elif interval == 'month':
                    schedule.every(1).months.at("01:00").do(backup_directory, sourcepath, archivepath, name, narchives, queue)

                counter = counter + 1

        queue.put({
            'name': 'Backups',
            'status': 'OK',
            'message': "{} backup(s) scheduled.".format(counter)
        })

    scheduler()

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    queue = Queue()
    main(queue)
