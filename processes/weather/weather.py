import requests
import schedule
import time
from datetime import datetime
from multiprocessing import Queue

class DataPost:

    def __init__(self):
        super(DataPost, self).__init__()

    def PostToKillGorack(self):
        with open('key.txt') as f:
            key_from_file = f.readline().strip()

        data = {
            "app": "weather",
            "formidentifier": "alacarte\\weather\\weather",
        }

        headers = {'Content-type': 'application/x-www-form-urlencoded', 'Accept': 'text/plain'}
        encoded_data = '&'.join([f"{key}={value}" for key, value in data.items()])
        response = requests.post(f'https://www.killgorack.com/PX4/api.php?ap=weather&apikeyid=3&vc={key_from_file}&api=json', data=encoded_data, headers=headers, verify=True)

def main(queue):

    queue.put({
        'name': 'weather',
        'status': 'OK',
        'message': "Service started."
    })
    
    def job(queue):

        d = DataPost()
        d.PostToKillGorack()
        queue.put({
            'name': 'weather',
            'status': 'OK',
            'message': "Weather data posted."
        })

    schedule.every().hour.at(":00").do(lambda: job(queue))

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    queue = Queue()
    main(queue)
