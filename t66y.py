import datetime
import os
import re
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import cpu_count

import dateutil
import redis
import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from bs4 import BeautifulSoup

from articles import Articles

# 连接redis
redis_pool = redis.ConnectionPool(decode_responses=True)
redis_conn = redis.Redis(connection_pool=redis_pool)


class T66y(object):
    def __init__(self):
        self.T66Y_URL = os.environ.get('T66Y_URL')
        self.T66Y_SCHEMA = os.environ.get('T66Y_SCHEMA')

    def start_scrap(self):
        self.__get_index_pages()

    def __get_index_pages(self):
        """获取主页中所有栏目的链接"""
        data = requests.get(self.T66Y_URL)
        data.encoding = 'gbk'

        soup = BeautifulSoup(data.text, 'html.parser')

        links = soup.find_all('tr', class_='tr3 f_one')

        for item in links:
            index_url = item.th.h2.a['href']
            if index_url:
                self.__get_t66y_pages(index_url)

    def __get_t66y_pages(self, url):
        """对每个链接进行请求，当出现登录或者超过100页的时候就不再访问下一页退出"""
        page = 1
        while True:
            t66y_url = self.T66Y_SCHEMA + url + '&search=&page=' + str(page)
            data = requests.get(t66y_url)
            data.encoding = 'gbk'

            # 有账号限制
            if re.findall('您沒有登錄或者您沒有權限訪問此頁面', data.text) or page >= 101:
                print(str(t66y_url) + '已抓取结束')
                break
            else:
                self.__detail_pages_data(data.text)
                page += 1

    def __detail_pages_data(self, page_data):
        """获取每个页面中的所有链接"""
        soup = BeautifulSoup(page_data, 'html.parser')
        links = soup.find_all('tr', class_='tr3 t_one tac')
        with ThreadPoolExecutor(max_workers=cpu_count() * 2) as executor:
            for item in links:
                executor.submit(self.__get_t66y_list_data, item)

    def __get_t66y_list_data(self, item):
        """对每个页面中链接和信息进行提取"""
        # 抓取链接和标题
        td_item = item.find('td', class_='tal')
        if td_item is None:
            return
        url = td_item.h3.a['href']

        # 将url存到redis中，当出现重复的时候就不再抓取
        if url and redis_conn.sismember('t66y', url) is False:
            redis_conn.sadd('t66y', url)
            try:
                title = td_item.h3.a.get_text()
                author = item.find('a', class_='bl').get_text()
                if item.find('span', class_='s3'):
                    post_date = item.find('span', class_='s3').get_text()
                else:
                    post_date = item.find('div', class_='f12').get_text()
                # 处理时间
                post_date = self.__get__post_date(post_date)
                post_date_str = str(post_date.date())
                article = Articles(
                    url=url,
                    title=title,
                    author=author,
                    post_date=post_date,
                    post_date_str=post_date_str)
                self.__get_article_content(article)
            except Exception as e:
                redis_conn.sadd('t66y_bad', url)
                print(e)

    def __get_article_content(self, article: Articles):
        """获取文章的正文信息然后进行存储"""
        request_url = self.T66Y_SCHEMA + article.url
        t66y_data = requests.get(request_url)
        t66y_data.encoding = 'gbk'
        soup = BeautifulSoup(t66y_data.text, 'html.parser')
        content = soup.find('div', class_='tpc_content do_not_catch')
        if content:
            article.content = str(content)
            article.content_no_tag = content.get_text()
            article.save()

    def __get__post_date(self, post_date):
        """对时间进行判断和处理"""
        if '今天' in post_date:
            post_date = datetime.datetime.now()
        elif '昨天' in post_date:
            post_date = datetime.datetime.now() - datetime.timedelta(days=1)
        else:
            try:
                post_date = dateutil.parser.parse(post_date)
            except Exception as e:
                post_date = datetime.datetime.now()
                return post_date
        return post_date


def t66y_job():
    t66y = T66y()
    t66y.start_scrap()


if __name__ == '__main__':
    sched = BlockingScheduler()
    sched.add_job(t66y_job, 'cron', hour=3)
    sched.start()
    #  t66y = T66y()
    #  t66y.start_scrap()
