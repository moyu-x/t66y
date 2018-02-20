from concurrent.futures import ThreadPoolExecutor
from multiprocessing import cpu_count

import jieba.analyse
import redis

from articles import AnalysisResults, Articles

redis_pool = redis.ConnectionPool(decode_responses=True)
redis_conn = redis.Redis(connection_pool=redis_pool)


class Participle(object):
    """对抓取到的文章进行分词处理"""

    def open_thread_pool(self):
        articles = Articles.objects(is_jieba=False)
        with ThreadPoolExecutor(max_workers=cpu_count() * 2) as executor:
            for item in articles:
                executor.submit(self.analyse_article, item)

    def analyse_article(self, article: Articles):
        """使用结巴抽取每篇文章排名前10的关键词"""
        tags = jieba.analyse.extract_tags(
            article.content_no_tag, topK=10, withWeight=True)
        [self.add_redis(tag) for tag, value in tags]
        article.top_key = tags
        article.is_jieba = True
        article.save()

    def add_redis(self, tag):
        """将分词数据放到redis中，统计词频"""
        redis_conn.zincrby('word_cloud', str(tag), amount=1)

    @classmethod
    def save_days_statistics(cls):
        """统计每天的数量"""
        pipline = [{
            '$group': {
                '_id': 'post_date_str',
                'sum': {
                    '$sum': 1
                }
            }
        }, {
            '$sort': {
                '_id': -1
            }
        }]
        data = list(Articles.objects().aggregate(*pipline))
        for item in data:
            AnalysisResults(
                date=item['post_date_str'], count=item['sum']).save()


if __name__ == "__main__":
    participle = Participle()
    participle.open_thread_pool()
    #  print(redis_conn.zrange('word_cloud', 0, 100, desc=True))
