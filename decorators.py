# coding: utf-8

__author__ = 'Orclover'

'''
实现特定功能的装饰器
'''

import functools
from model import *

# 增加文章阅读次数
def view_increase_wrapper(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        article_id = kwargs.get('article_id')
        article = Article.objects(id=article_id).first()
        article.view_number += 1
        article.save()
        return func(*args, **kwargs)
    return wrapper
