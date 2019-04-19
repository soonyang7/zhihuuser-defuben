# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import re, time

import pymongo
from weibobishe.items import *


class TimePipeline():
    def process_item(self, item, spider):
        if isinstance(item, WeiboItem):
            now = time.strftime('%Y-%m-%d %H:%M', time.localtime())
            item['crawled_at'] = now
        return item


class WeiboPipeline():
    def parse_time(self, date):
        if re.match('刚刚', date):
            date = time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time()))
        if re.match('\d+分钟前', date):
            minute = re.match('(\d+)', date).group(1)
            date = time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time() - float(minute) * 60))
        if re.match('\d+小时前', date):
            hour = re.match('(\d+)', date).group(1)
            date = time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time() - float(hour) * 60 * 60))
        if re.match('昨天.*', date):
            date = re.match('昨天(.*)', date).group(1).strip()
            date = time.strftime('%Y-%m-%d', time.localtime() - 24 * 60 * 60) + ' ' + date
        if re.match('\d{2}-\d{2}', date):
            date = time.strftime('%Y-', time.localtime()) + date + ' 00:00'
        return date

    def process_item(self, item, spider):
        if isinstance(item, WeiboItem):
            if item.get('created_at'):
                item['created_at'] = item['created_at'].strip()
                item['created_at'] = self.parse_time(item.get('created_at'))
            if item.get('pictures'):
                item['pictures'] = [pic.get('url') for pic in item.get('pictures')]
        return item


class MongoPipeline(object):
    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        self.db[UserItem.collection].create_index([('id', pymongo.ASCENDING)])
        self.db[WeiboItem.collection].create_index([('id', pymongo.ASCENDING)])
        self.db[WeiboTextItem.collection].create_index([('id', pymongo.ASCENDING)])

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        if isinstance(item, WeiboTextItem) or isinstance(item, WeiboItem):
            self.db[item.collection].update({'id': item.get('id')}, {'$set': item}, True)
        # if isinstance(item, UserRelationItem):
        #     self.db[item.collection].update(
        #         {'id': item.get('id')},
        #         {'$addToSet':
        #             {
        #                 'follows': {'$each': item['follows']},
        #                 'fans': {'$each': item['fans']}
        #             }
        #         }, True)
        return item


        # class DuplicatesPipeline(object):
        #     """
        #     去重
        #     """
        #
        #     def __init__(self):
        #         self.book_set = set()
        #
        #     def process_item(self, item, spider):
        #         name = item['name']
        #         if name in self.book_set:
        #             raise DropItem("Duplicate book found:%s" % item)
        #
        #         self.book_set.add(name)
        #         return item

        # class DuplicatesPipeline(object):
        #
        #     def __init__(self):
        #         self.ids_seen = set()
        #
        #     def process_item(self, item, spider):
        #         if item['id'] in self.ids_seen:
        #             raise DropItem("Duplicate item found: %s" % item)
        #         else:
        #             self.ids_seen.add(item['id'])
        #             return item

        # redis_db = redis.Redis(host=settings.REDIS_HOST, port=6379, db=4, password='root')
        # redis_data_dict = "f_uuids"
        # class DuplicatePipeline(object):
        #     """
        #     去重(redis)
        #     """
        #     def __init__(self):
        #         if redis_db.hlen(redis_data_dict) == 0:
        #             sql = "SELECT uuid FROM f_data"
        #             df = pd.read_sql(sql, engine)
        #             for uuid in df['uuid'].get_values():
        #                 redis_db.hset(redis_data_dict, uuid, 0)
        #     def process_item(self, item, spider):
        #         if redis_db.hexists(redis_data_dict, item['uuid']):
        #              raise DropItem("Duplicate item found:%s" % item)
        #         return item