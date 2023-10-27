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


class imageReaper:

    def __init__(self, queue) -> None:
        self.conn = sqlite3.connect('web_crawl.db')
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS webpages (url text UNIQUE)''')
        self.conn.commit()
        self.counter = 1

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
                #queue.put({
                    #'name': 'scraper',
                    #'status': 'NOK',
                    #'message': f"Error while accessing {url}: {e}"
                #})
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
                        #queue.put({
                            #'name': 'scraper',
                            #'status': 'NOK',
                            #'message': f"Error while processing {new_url}: {e}"
                        #})

            for element in soup.select('[data-href]'):
                s = element.get('data-href')
                if s is not None:
                    new_url = urljoin(url, s)
                    try:
                        urlqueue.append((new_url, depth + 1))
                        self.process_url(new_url, queue)
                    except Exception as e:
                        pass
                        #queue.put({
                            #'name': 'scraper',
                            #'status': 'NOK',
                            #'message': f"Error while processing {new_url}: {e}"
                        #})

    """
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
    """

    def process_url(self, url, queue):
        self.c.execute("SELECT url FROM webpages WHERE url=?", (url,))
        result = self.c.fetchone()
        if result is None:
            self.c.execute("INSERT INTO webpages VALUES (?)", (url,))
            self.conn.commit()
            if url.lower().endswith('.pdf'):
                self.download_pdf(url, queue)


    def download_image(self, img_url, queue):
        try:
            response = requests.get(img_url, stream=True)
            img = Image.open(io.BytesIO(response.content))
            filename = 'image' + str(self.counter)
            with open('images/' + filename + '.jpg', 'wb') as out_file:
                out_file.write(response.content)
            queue.put({
                'name': 'scraper',
                'status': 'OK',
                'message': "Image downloaded {}".format(self.counter)
            })
            self.counter += 1
        except Exception as e:
            pass

    def download_pdf(self, pdf_url, queue):
        try:
            response = requests.get(pdf_url, stream=True)
            filename = 'pdf' + str(self.counter)
            with open('pdfs/' + filename + '.pdf', 'wb') as out_file:
                out_file.write(response.content)
            queue.put({
                'name': 'scraper',
                'status': 'OK',
                'message': "PDF downloaded {}".format(self.counter)
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
                try:
                    img = Image.open(io.BytesIO(response.content))
                    if img.size[0] > 200 and img.size[1] > 200:
                        filename = 'image' + str(self.counter)
                        with open('images/' + filename + '.jpg', 'wb') as out_file:
                            out_file.write(response.content)
                        self.counter += 1
                except IOError:
                    pass
                    #queue.put({
                        #'name': 'scraper',
                        #'status': 'NOK',
                        #'message': f"Error: Cannot identify image file {img_url}"
                    #})
            except Exception as e:
                #queue.put({
                    #'name': 'scraper',
                    #'status': 'NOK',
                    #'message': f"Error downloading {img_url}: {e}"
                #})
                pass

def main(queue):

    queue.put({
        'name': 'scraper',
        'status': 'OK',
        'message': "Service running."
    })

    gi = imageReaper(queue)
    gi.crawl("https://www.google.com/search?q=ISO+22093&sca_esv=575449117&sxsrf=AM9HkKlK8WcOu381sgEe9F4Q-vMYGXCdcA%3A1697896662711&ei=1tgzZYf_KrWmqtsPvuKyoAo&ved=0ahUKEwiHwsj7pYeCAxU1k2oFHT6xDKQQ4dUDCBA&uact=5&oq=ISO+22093&gs_lp=Egxnd3Mtd2l6LXNlcnAiCUlTTyAyMjA5MzIEECMYJzIGEAAYFhgeMgYQABgWGB5Ijw1QAFgAcAB4AZABAJgBbaABbaoBAzAuMbgBA8gBAPgBAvgBAeIDBBgAIEGIBgE&sclient=gws-wiz-serp", 100, queue)

    while True:
        time.sleep(1)

if __name__ == "__main__":
    queue = Queue()
    main(queue)