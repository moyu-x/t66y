import dateutil
import mongoengine
import requests
from bs4 import BeautifulSoup

mongoengine.connect('t66y', alias='t66y')

T66Y_SCHEAME = 'http://t66y.com/'


class Articles(mongoengine.Document):
    url = mongoengine.StringField()
    title = mongoengine.StringField()
    author = mongoengine.StringField()
    content = mongoengine.StringField()
    post_date = mongoengine.DateTimeField()
    content_no_tag = mongoengine.StringField()

    meta = {'db_alias': 't66y', 'indexes': ['url']}


def get_article_data(article: Articles):
    request_url = T66Y_SCHEAME + article.url
    t66y_data = requests.get(request_url)
    t66y_data.encoding = 'gbk'
    soup = BeautifulSoup(t66y_data.text, 'html.parser', from_encoding='utf-8')
    links = soup.find('div', class_='tpc_content do_not_catch')
    if links:
        article.content = str(links)
        article.content_no_tag = links.get_text()
        article.save()


def detail_t66y_page(page_url):
    article_list = requests.get(page_url)
    # 设置原来网页的编码
    article_list.encoding = 'gbk'
    soup = BeautifulSoup(
        article_list.text, 'html.parser', from_encoding='utf-8')
    links = soup.find_all('tr', class_='tr3 t_one tac')
    [get_t66y_list_data(item) for item in links]


def get_t66y_list_data(item):
    # 抓取链接和标题
    td_item = item.find('td', class_='tal')
    if td_item is None:
        return
    url = td_item.h3.a['href']
    if url:
        title = td_item.h3.a.get_text()
        author = item.find('a', class_='bl').get_text()
        if item.find('span', class_='s3'):
            post_date = item.find('span', class_='s3')['title']
            post_date = post_date.split(' - ')[1]
        else:
            post_date = item.find('div', class_='f12').get_text()
        post_date = dateutil.parser.parse(post_date)
        article = Articles(
            url=url, title=title, author=author, post_date=post_date)

        get_article_data(article)


def get_t66y_pages():
    base_url = 'http://t66y.com/thread0806.php?fid=7&search=&page='
    # 超过一百页之后需要登录，所以这里都不超过一百页
    # for item in range(1, 101):
    # page = base_url + str(item)
    # print(page)
    url = base_url + str(1)
    detail_t66y_page(url)


if __name__ == '__main__':
    #  get_article_list()
    get_t66y_pages()
