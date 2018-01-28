import datetime
import re

import redis
from apscheduler.schedulers.blocking import BlockingScheduler
from bs4 import BeautifulSoup

import requests
from articles import Articles

# 连接redis
redis_pool = redis.ConnectionPool(decode_responses=True)
redis_conn = redis.Redis(connection_pool=redis_pool)

T66Y_INDEX = 'http://t66y.com/index.php'
T66Y_SCHEAME = 'http://t66y.com/'


def get_article_data(article: Articles):
    """获取文章的正文信息然后进行存储"""
    request_url = T66Y_SCHEAME + article.url
    t66y_data = requests.get(request_url)
    t66y_data.encoding = 'gbk'
    soup = BeautifulSoup(t66y_data.text, 'html.parser')
    links = soup.find('div', class_='tpc_content do_not_catch')
    if links:
        article.content = str(links)
        article.content_no_tag = links.get_text()
        article.save()


def detail_t66y_page(page_data):
    """获取每个页面中的所有链接"""
    soup = BeautifulSoup(page_data, 'html.parser')
    links = soup.find_all('tr', class_='tr3 t_one tac')
    [get_t66y_list_data(item) for item in links]


def get_t66y_list_data(item):
    """对每个页面中链接和信息进行提取"""
    # 抓取链接和标题
    td_item = item.find('td', class_='tal')
    if td_item is None:
        return
    url = td_item.h3.a['href']
    if url and redis_conn.sismember('t66y', url) is False:
        redis_conn.sadd('t66y', url)
        try:
            title = td_item.h3.a.get_text()
            author = item.find('a', class_='bl').get_text()
            if item.find('span', class_='s3'):
                post_date = item.find('span', class_='s3').get_text()
            else:
                post_date = item.find('div', class_='f12').get_text()
            post_date = detail_post_date(post_date)
            article = Articles(
                url=url, title=title, author=author, post_date=post_date)
            get_article_data(article)
        except Exception as e:
            redis_conn.sadd('t66y_bad', url)
            print(e)


def detail_post_date(post_date):
    """对时间进行判断和处理"""
    if '今天' in post_date:
        post_date = str(datetime.date.today())
    elif '昨天' in post_date:
        post_date = str(
            (datetime.datetime.today() - datetime.timedelta(days=1)).date())


def get_t66y_pages(url):
    """对每个链接进行请求，当出现登录的时候就不再访问下一页退出"""
    page = 1
    while True:
        t66y_url = T66Y_SCHEAME + url + '&search=&page=' + str(page)
        data = requests.get(t66y_url)
        data.encoding = 'gbk'
        if re.findall('您沒有登錄或者您沒有權限訪問此頁面', data.text):
            break
        else:
            detail_t66y_page(data.text)
            page += 1


def get_index_pages():
    """获取主页中栏目的链接"""
    data = requests.get(T66Y_INDEX)
    data.encoding = 'gbk'

    soup = BeautifulSoup(data.text, 'html.parser')

    links = soup.find_all('tr', class_='tr3 f_one')

    for item in links:
        index_url = item.th.h2.a['href']
        if index_url:
            get_t66y_pages(index_url)


if __name__ == '__main__':
    sched = BlockingScheduler()
    sched.add_job(get_index_pages, 'cron', hour=3)
    sched.start()
    # get_index_pages()
