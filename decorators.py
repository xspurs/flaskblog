# coding: utf-8

__author__ = 'xspurs'

'''
实现特定功能的装饰器
'''

from functools import wraps
from model import *
from flask import g


# 增加文章阅读次数
# 将查询到的文章放入flask.g中，以便后续使用
def view_increase_wrapper(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        article_id = kwargs.get('article_id')
        g.article = Article.objects(id=article_id).first()
        g.article.view_number += 1
        g.article.save()
        return func(*args, **kwargs)
    return wrapper
