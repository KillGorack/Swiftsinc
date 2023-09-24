import os
import os.path
import time
import datetime
import shutil
from PIL import Image
from PIL.ExifTags import TAGS
from multiprocessing import Queue

# Your paths
fromdir = "D://Pictures//_drop"
destdir = "D://Pictures//_organized"
errodir = "D://Pictures//_err"

def main(queue):

    queue.put({
        'name': 'photos',
        'status': 'OK',
        'message': "Service started."
    })

    # Definitions
    def month_converter(month):
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        return months.index(month) + 1

    # Main function that does the work
    def movinator(queue):
        for subdir, dirs, files in os.walk(fromdir):
            for file in files:
                filepath = subdir + os.sep + file
                try:
                    dt = Image.open(filepath)._getexif()[36867]
                    yr = dt[:4]
                    mo = dt[5:7] + "_" + datetime.date(1900, int(dt[5:7]), 1).strftime('%B')
                    dy = dt[8:10]
                    pre = "photo_"
                    path = destdir + "/" + yr + "/" + mo + "/" + str(int(dy)).zfill(2) + "/"
                except:
                    try:
                        dt = time.ctime(os.path.getmtime(filepath))
                        yr = dt[-4:]
                        moint = month_converter(dt[4:7])
                        mo = str(moint).zfill(2) + "_" + datetime.date(1900, int(moint), 1).strftime('%B')
                        dy = dt[8:10]
                        pre = "image_"
                        path = destdir + "/" + yr + "/" + mo + "/" + str(int(dy)).zfill(2) + "/"
                    except:
                        stp = True
                        pre = "unknown_"
                        path = errodir + "/"
                        queue.put({
                            'name': 'photos',
                            'status': 'NOK',
                            'message': "File moved to error directory."
                        })
                ext = os.path.splitext(file)[1]
                if not os.path.exists(path):
                    os.makedirs(path)
                file_list = os.listdir(path)
                cnt = len(file_list) + 1
                shutil.move(subdir + "/" + file, path + pre + str(cnt).zfill(2) + ext)
                queue.put({
                    'name': 'photos',
                    'status': 'OK',
                    'message': "moving file {file}."
                })

    movinator(queue)
    before = dict([(f, None) for f in os.listdir(fromdir)])
    while True:
        time.sleep(10)
        after = dict([(f, None) for f in os.listdir(fromdir)])
        added = [f for f in after if not f in before]
        removed = [f for f in before if not f in after]
        if added:
            movinator(queue)
            queue.put({
                'name': 'photos',
                'status': 'OK',
                'message': "Finished moving your images."
            })
        before = after

if __name__ == "__main__":
    queue = Queue()
    main(queue)