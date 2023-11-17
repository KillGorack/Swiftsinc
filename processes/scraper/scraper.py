import os
import sqlite3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from collections import deque
from PIL import Image
from multiprocessing import Queue
import io
import time
import hashlib
from urllib.parse import urlparse
import configparser


class imageReaper:

    def __init__(self, queue) -> None:
        self.conn = sqlite3.connect('web_crawl.db')
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS webpages (url text UNIQUE)''')
        self.c.execute('''CREATE TABLE IF NOT EXISTS images (hash text UNIQUE)''')
        self.conn.commit()
        self.counter = 1

    def get_file_extension(self, url):
        parsed = urlparse(url)
        path = parsed.path
        path = path.split('?')[0]
        file_extension = os.path.splitext(path)[1]
        if len(file_extension) not in [4, 5]:
            return ".jpg"
        else:
            return os.path.splitext(path)[1]


    def crawl(self, start_url, max_depth, queue):
        urlqueue = deque([(start_url, 0)])

        while urlqueue:
            url, depth = urlqueue.popleft()
            if depth > max_depth:
                break
            try:
                r = requests.get(url)
                soup = BeautifulSoup(r.text, 'html.parser')
            except Exception as e:
                queue.put({
                    'name': 'scraper',
                    'status': 'OK',
                    'message': f"Error while accessing {url}: {e}"
                })
                continue

            for link in soup.find_all('a'):
                s = link.get('href')
                if s is not None:
                    new_url = urljoin(url, s)
                    try:
                        urlqueue.append((new_url, depth + 1))
                        self.process_url(new_url, queue)
                    except Exception as e:
                        pass
                        queue.put({
                            'name': 'scraper',
                            'status': 'OK',
                            'message': f"Error while processing {new_url}: {e}"
                        })

            for element in soup.select('[data-href]'):
                s = element.get('data-href')
                if s is not None:
                    new_url = urljoin(url, s)
                    try:
                        urlqueue.append((new_url, depth + 1))
                        self.process_url(new_url, queue)
                    except Exception as e:
                        pass
                        queue.put({
                            'name': 'scraper',
                            'status': 'OK',
                            'message': f"Error while processing {new_url}: {e}"
                        })


    def process_url(self, url, queue):
        self.c.execute("SELECT url FROM webpages WHERE url=?", (url,))
        result = self.c.fetchone()
        if result is None:
            self.c.execute("INSERT INTO webpages VALUES (?)", (url,))
            self.conn.commit()
            if url.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                self.download_image(url, queue)
            else:
                self.download_images(url, queue)


    def download_image(self, img_url, queue):
        try:
            response = requests.get(img_url, stream=True)
            img_data = response.content
            img_hash = hashlib.sha256(img_data).hexdigest()

            self.c.execute("SELECT hash FROM images WHERE hash=?", (img_hash,))
            result = self.c.fetchone()
            if result is not None:
                queue.put({
                    'name': 'scraper',
                    'status': 'OK',
                    'message': "Image already downloaded"
                })
                return

            img = Image.open(io.BytesIO(img_data))
            filename = 'imagea' + str(self.counter)
            file_extension = self.get_file_extension(img_url)
            with open('images/' + filename + file_extension, 'wb') as out_file:
                out_file.write(img_data)
            self.c.execute("INSERT INTO images VALUES (?)", (img_hash,))
            self.conn.commit()
            queue.put({
                'name': 'scraper',
                'status': 'OK',
                'message': "Image downloaded {}".format(self.counter)
            })
            self.counter += 1
        except Exception as e:
            pass



    def download_images(self, url, queue):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        img_tags = soup.find_all('img')

        if not os.path.exists('images'):
            os.makedirs('images')

        for img in img_tags:

            img_url = img.get('src')
            if 'http' not in img_url:
                img_url = urljoin(url, img_url)
            try:
                response = requests.get(img_url, stream=True)
                img_data = response.content
                img_hash = hashlib.sha256(img_data).hexdigest()
                self.c.execute("SELECT hash FROM images WHERE hash=?", (img_hash,))
                result = self.c.fetchone()
                if result is not None:
                    queue.put({
                        'name': 'scraper',
                        'status': 'OK',
                        'message': "Image already downloaded"
                    })
                    continue
                try:

                    img = Image.open(io.BytesIO(response.content))
                    
                    #if ((img.size[0] >= 1920 and img.size[1] >= 1080) or (img.size[0] >= 1080 and img.size[1] >= 2340)):
                    if img.size[0] >= 800 and img.size[1] >= 800:
                        
                        filename = 'image' + str(self.counter)
                        file_extension = self.get_file_extension(img_url)
                        with open('images/' + filename + file_extension, 'wb') as out_file:
                            out_file.write(response.content)
                        self.c.execute("INSERT INTO images (hash) VALUES (?)", (img_hash,))
                        self.conn.commit()

                        queue.put({
                            'name': 'scraper',
                            'status': 'OK',
                            'message': "Image downloaded! (#{})".format(self.counter)
                        })

                        self.counter += 1
                    else:

                        queue.put({
                            'name': 'scraper',
                            'status': 'COK',
                            'message': "Wrong dimensions. ({}X{})".format(img.size[0], img.size[1])
                        })

                except IOError:

                    pass


            except Exception as e:
                queue.put({
                    'name': 'scraper',
                    'status': 'OK',
                    'message': f"Error downloading {img_url}: {e}"
                })
                pass


def main(queue):

    queue.put({
        'name': 'scraper',
        'status': 'OK',
        'message': "Service running."
    })

    config = configparser.ConfigParser()
    config.read('config.ini')
    base_url = config.get('scraper', 'base_url')
    
    gi = imageReaper(queue)
    gi.crawl(base_url, 100, queue)

    while True:
        time.sleep(1)

if __name__ == "__main__":
    queue = Queue()
    main(queue)