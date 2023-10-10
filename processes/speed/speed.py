import requests
import json
import schedule
import time
from datetime import datetime
import speedtest
from multiprocessing import Queue


class SpeedTest:
    
    def __init__(self):
        super(SpeedTest, self).__init__()

    def test(self):
        
        servers = []
        threads = None

        s = speedtest.Speedtest(secure=True)
        s.get_servers(servers)
        s.get_best_server()
        s.download(threads=threads)
        s.upload(threads=threads)
        s.results.share()

        flds = {
            'download': round(s.results.dict()['download'] / 1000000, 3),
            'upload': round(s.results.dict()['upload'] / 1000000, 3),
            'ping': s.results.dict()['ping'],
            'timestamp': datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
            'bytes_sent': s.results.dict()['bytes_sent'],
            'bytes_received': s.results.dict()['bytes_received'],
            'share': s.results.dict()['share']
        }

        flds_server = {
            's_url': s.results.dict()['server']['url'],
            's_lat': s.results.dict()['server']['lat'],
            's_lon': s.results.dict()['server']['lon'],
            's_name': s.results.dict()['server']['name'],
            's_country': s.results.dict()['server']['country'],
            's_cc': s.results.dict()['server']['cc'],
            's_sponsor': s.results.dict()['server']['sponsor'],
            's_isp_id': s.results.dict()['server']['id'],
            's_host': s.results.dict()['server']['host'],
            's_d': s.results.dict()['server']['d'],
            's_latency': s.results.dict()['server']['latency']
        }

        flds_client = {
            'c_ip': s.results.dict()['client']['ip'],
            'c_lat': s.results.dict()['client']['lat'],
            'c_lon': s.results.dict()['client']['lon'],
            'c_isp': s.results.dict()['client']['isp'],
            'c_isprating': s.results.dict()['client']['isprating'],
            'c_rating': s.results.dict()['client']['rating'],
            'c_ispdlavg': s.results.dict()['client']['ispdlavg'],
            'c_ispulavg': s.results.dict()['client']['ispulavg'],
            'c_loggedin': s.results.dict()['client']['loggedin'],
            'c_country': s.results.dict()['client']['country']
        }

        res = dict(flds)
        res.update(flds_server)
        res.update(flds_client)

        return res


class DataPost:

    def post_to_kill_gorack(self, results, queue):
        
        with open('key.txt') as f:
            key_from_file = f.readline().strip()

        results['key'] = key_from_file
        results['app'] = "speedtest"
        results['formidentifier'] = "alacarte\\speedtest\\speedtest"

        try:

            url = f"https://www.killgorack.com/PX4/api.php?ap=spd&apikeyid=3&vc={key_from_file}&api=json"
            headers = {'Content-type': 'application/x-www-form-urlencoded', 'Accept': 'text/plain'}
            response = requests.post(url, data=results, headers=headers, verify=True)
            response.close()

        except requests.RequestException:

            queue.put({
                'name': 'speed',
                'status': 'NOK',
                'message': f"Posting speed data to killgorack.com failed."
            })


def main(queue):

    queue.put({
        'name': 'speed',
        'status': 'OK',
        'message': "Service started."
    })

    def job(queue):

        retry = True

        while retry:

            try:

                queue.put({
                    'name': 'speed',
                    'status': 'OK',
                    'message': "Starting speed test."
                })

                speed_test = SpeedTest()
                results = speed_test.test()
                data_post = DataPost()
                data_post.post_to_kill_gorack(results, queue)

                if results['download'] < 30:
                    st = "NOK"
                elif results['download'] < 60:
                    st = "COK"
                else:
                    st = "OK"

                queue.put({
                    'name': 'speed',
                    'status': st,
                    'message': f"speed: Down: {results['download']}, Up: {results['upload']}, Ping: {results['ping']}"
                })

                retry = False

            except Exception as e:

                queue.put({
                    'name': 'speed',
                    'status': 'NOK',
                    'message': f"{str(e)}"
                })

                time.sleep(60)

    schedule.every().hour.at(":00").do(lambda: job(queue))

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    queue = Queue()
    main(queue)
