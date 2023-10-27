from tinytag import TinyTag
import os
import sqlite3
import shutil
from random import randint
from threading import Thread
import time
from multiprocessing import Queue

# =============================================
# Define paths (later use db relative)
# =============================================
path_error = "C://Users//David//Music//_error//"
path_read = "C://Users//David//Music//_drop//"
path_cleaned = "D://Music//"
path_data = "C://Users//David//Music//musical_data.db"
# =============================================
# Definition for checking paths
# =============================================


def check_paths(path_error, path_read, path_cleaned, path_data):
    rtrn = True
    if os.path.exists(os.path.dirname(os.path.abspath(path_data))) == False:
        rtrn = False
    if os.path.exists(path_error) == False:
        rtrn = False
    if os.path.exists(path_read) == False:
        rtrn = False
    if os.path.exists(path_cleaned) == False:
        rtrn = False
    return rtrn
# =============================================
# Definition for checking paths content
# =============================================


def check_content(path_error, path_cleaned):
    rtrn = True
    path, dirs, files = next(os.walk(path_error))
    if len(files) > 0:
        rtrn = False
    path, dirs, files = next(os.walk(path_cleaned))
    if len(files) > 0:
        rtrn = False
    return rtrn
# =============================================
# Database birth
# =============================================


def db_init(dbname):
    conn = sqlite3.connect(dbname, timeout=10)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS `music_data`
    (
    `ID`  INTEGER PRIMARY KEY AUTOINCREMENT,
    `album`             TEXT,
    `albumartist`       TEXT,
    `artist`            TEXT,
    `audio_offset`      TEXT,
    `bitrate`           TEXT,
    `comment`           TEXT,
    `disc`              TEXT,
    `disc_total`        TEXT,
    `duration`          TEXT,
    `filesize`          TEXT,
    `genre`             TEXT,
    `samplerate`        TEXT,
    `title`             TEXT,
    `track`             TEXT,
    `track_total`       TEXT,
    `year`              TEXT,
    `path`              TEXT,
    `ext`               TEXT
    )''')
    c.execute("delete from 'music_data'")
    conn.commit()
    c.execute("delete from sqlite_sequence where name='music_data'")
    conn.commit()
    conn.close()
    return True
# =============================================
# prestart check
# =============================================


def start_check(path_error, path_read, path_cleaned, path_data):
    stp = False
    msg = ""
    if (check_paths(path_error, path_read, path_cleaned, path_data) == False):
        msg = "One or more of the needed directories do not exist, check your py."
        stp = True
    if (check_content(path_error, path_cleaned) == False):
        msg = "One or more of the needed directories have files within, Delete from the error, and cleaned directories, as they need to be empty."
        stp = True
    return [stp, msg]
# =============================================
# A list of ALL files....
# =============================================


def getfiles(path_read):
    f = []
    for folder, subfolder, file in os.walk(path_read):
        for dbname in file:
            f.append(os.path.join(folder, dbname))
    return f
# =============================================
# Get musical data
# =============================================


def gather_data(file_list, path_data):
    cleaned = []
    duped = []
    error = []
    test = []
    err = 0
    conn = sqlite3.connect(path_data)
    c = conn.cursor()
    for song in file_list:
        try:
            tag = TinyTag.get(song)
            item = [
                tag.album,
                tag.albumartist,
                tag.artist,
                tag.audio_offset,
                tag.bitrate,
                tag.comment,
                tag.disc,
                tag.disc_total,
                tag.duration,
                tag.filesize,
                tag.genre,
                tag.samplerate,
                tag.title,
                tag.track,
                tag.track_total,
                tag.year,
                song,
                os.path.splitext(song)[1]
            ]
            comp = str(tag.album) + str(tag.albumartist) + str(tag.title) + \
                str(tag.filesize) + str(tag.samplerate) + str(tag.bitrate)
            if (comp in test):
                duped.append(item)
            elif len(tag.album.strip()) == 0 or len(tag.title.strip()) == 0:
                error.append(item)
            else:
                cleaned.append(item)
                test.append(comp)
                c.execute('insert into music_data(`album`,`albumartist`,`artist`,`audio_offset`,`bitrate`,`comment`,`disc`,`disc_total`,`duration`,`filesize`,`genre`,`samplerate`,`title`,`track`,`track_total`,`year`,`path`, ext) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', item)
        except:
            error.append(song)
    conn.commit()
    conn.close()
    return [cleaned, duped, error]
# =============================================
# Your basic cleaner
# =============================================


def string_cleaner(cleaned_string):
    bad_chars = ['~', '#', '%', '*', '(', ')', '[', ']',
                 '{', '}', '/', '/', ':', '?', '|', '\"', '\'', '\n', '\r']
    for i in bad_chars:
        cleaned_string = cleaned_string.replace(i, '')
    return cleaned_string
# =============================================
# Move to cleaned area..
# =============================================


def move_to_cleaned(files, movepath, queue):
    if (len(files) > 0):
        for file in files:
            dest = movepath + \
                string_cleaner(file[2]) + "//" + string_cleaner(file[0]) + "//"
            newpath = dest + \
                string_cleaner(file[12]) + " " + string_cleaner(file[17])
            if not os.path.exists(dest):
                os.makedirs(dest)
            shutil.copy(file[16], newpath)
            queue.put({
                'name': 'music',
                'status': 'OK',
                'message': f"{file[12]} moved."
            })
        return True
    else:
        return False
# =============================================
# Duplicates
# =============================================


def move_to_dupes(files, movepath, queue):
    if (len(files) > 0):
        for file in files:
            dest = movepath + \
                string_cleaner(file[1]) + "//" + string_cleaner(file[0]) + "//"
            newpath = dest + \
                string_cleaner(file[12]) + " " + string_cleaner(file[17])
            if not os.path.exists(dest):
                os.makedirs(dest)
            shutil.copy(file[16], newpath)
            queue.put({
                'name': 'music',
                'status': 'OK',
                'message': f"{file[12]} moved to duplicate folder."
            })
        return True
    else:
        return False
# =============================================
# error
# =============================================


def move_to_error(files, movepath, queue):
    if (len(files) > 0):
        for file in files:
            if (len(file) != 19):
                a = 1
            else:
                dest = movepath + \
                    string_cleaner(file[1]) + "//" + \
                    string_cleaner(file[0]) + "//"
                newpath = dest + \
                    string_cleaner(file[12]) + " " + string_cleaner(file[17])
                if not os.path.exists(dest):
                    os.makedirs(dest)
                shutil.copy(file[16], newpath)
                queue.put({
                    'name': 'music',
                    'status': 'OK',
                    'message': f"{file[12]} moved to error folder."
                })
        return True
    else:
        return False


def delete_from_source(files, queue):
    if len(files) > 0:
        for file in files:
            try:
                os.remove(file[16])
                queue.put({
                    'name': 'music',
                    'status': 'OK',
                    'message': f"{file[12]} deleted from source after moving."
                })
            except OSError as e:
                queue.put({
                    'name': 'music',
                    'status': 'OK',
                    'message': f"Error deleting file: {file[12]} - {e}"
                })
        return True
    else:
        return False


def main(queue):

    queue.put({
        'name': 'music',
        'status': 'OK',
        'message': "Service started."
    })
    while True:
        file_list = getfiles(path_read)
        if file_list:
            queue.put({
                'name': 'music',
                'status': 'OK',
                'message': "Music mover; files found in drop, calling for a file move."
            })
            file_list = getfiles(path_read)
            inventory = gather_data(file_list, path_data)
            move_to_cleaned(inventory[0], path_cleaned, queue)
            move_to_dupes(inventory[1], path_error, queue)
            move_to_error(inventory[2], path_error, queue)
            # Delete files from source
            delete_from_source(
                inventory[0] + inventory[1] + inventory[2], queue)
        queue.put({
            'name': 'music',
            'timeout': 1
        })
        time.sleep(10)


if __name__ == "__main__":
    queue = Queue()
    main(queue)
