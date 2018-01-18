import requests
from bs4 import BeautifulSoup

T66Y_SCHEAME = 'http://t66y.com/'


def get_article_data(link):
    request_url = T66Y_SCHEAME + link
    t66y_data = requests.get(request_url)
    t66y_data.encoding = 'gbk'
    soup = BeautifulSoup(t66y_data.text, 'html.parser', from_encoding='utf-8')
    links = soup.find('div', class_='tpc_content do_not_catch')
    print(links.get_text())


def get_article_list():
    articles_list_data = requests.get('http://t66y.com/thread0806.php?fid=7')
    articles_list_data.encoding = 'gbk'

    soup = BeautifulSoup(
        articles_list_data.text, 'html.parser', from_encoding='utf-8')

    links = soup.find_all('tr', class_='tr3 t_one tac')
    for item in links[5:]:
        # 抓取链接和标题
        td_item = item.find('td', class_='tal')
        if td_item is None:
            continue
        title = td_item.h3.a.get_text()
        url = td_item.h3.a['href']
        author = item.find('a', class_='bl').get_text()
        if item.find('span', class_='s3'):
            post_date = item.find('span', class_='s3')['title']
            post_date = post_date.split(' - ')[1]
        else:
            post_date = item.find('div', class_='f12').get_text()
        get_article_data(url)

        print(title + ' ' + url + ' ' + author + ' ' + post_date)
        print('__________________')


if __name__ == '__main__':
    get_article_list()
