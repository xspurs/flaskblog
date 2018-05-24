# coding: utf-8

__author__ = 'Orclover'

"""
compositing with flask-admin
"""

# flask_admin相关，考虑从本文件中摘除
# 开始
import flask_admin as admin
from flask import redirect, url_for, request
from flask_admin.contrib.mongoengine import ModelView
from flask_admin import BaseView, expose
import flask_login
from model import Article, Classification


# 基类，为ModelView添加用户身份控制
class AuthModelView(ModelView):
    # flask-admin + flask-login
    def is_accessible(self):
        # 官方文档调用的是方法，如下：（错误，is_authenticated是current_user的一个属性）
        # return flask_login.current_user.is_authenticated()
        # flask_login.current_user.type == 1 为自定义的管理员属性，只有管理员用户才可以进入管理端进行操作
        return flask_login.current_user.is_authenticated and flask_login.current_user.type == 1

    def inaccessible_callback(self, name, **kwargs):
        # TODO 根据不同的情况，给予用户不同的提示（如未登录用户提示用户需要登录，已登录但非管理员用户提示用户身份错误等)
        '''
        if not flask_login.current_user.is_authenticated:
            return redirect(url_for('login', next=request.url))
        elif flask_login.current_user.type != 1:
            return redirect(url_for('wrong principal', next=request.url))
        '''
        return redirect(url_for('login', redirect_uri=request.url))


# 基类，为BaseView添加用户身份控制
# TODO 该类并没有使用上，剔除
class AuthBaseView(BaseView):
    # flask-admin + flask-login
    def is_accessible(self):
        # 官方文档调用的是方法，如下：（错误，is_authenticated是current_user的一个属性）
        # return flask_login.current_user.is_authenticated()
        return flask_login.current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', redirect_uri=request.url))


class UserView(AuthModelView):
    column_filters = ['login_id']
    create_modal, edit_modal = True, True

    column_searchable_list = ('login_id', 'name', 'email')


class ClassificationView(AuthModelView):
    column_searchable_list = ('name',)
    # 以模态框(modal)形式弹出编辑
    edit_modal, create_modal = True, True


class ArticleView(AuthModelView):
    column_searchable_list = ('title', 'abstract')
    column_exclude_list = ('coments', 'tags',)
    # 禁止对文章进行编辑和新建
    # can_create, can_edit = False, False

    # 允许再页面内部编辑
    # column_editable_list = ('',)

    # 单页条数
    page_size = 10

    '''
    form_ajax_refs = {
        ''
    }
    '''

    # 2016-06-27
    # 在基础上扩展，碉堡
    @expose('/edit')
    def edit_view(self):
        article_id = request.args.get('id')
        article = Article.objects(id=article_id).first()
        classifications = Classification.objects.order_by('+name')
        return self.render('write.html', classifications=classifications, article=article)

    @expose('/create')
    def create_view(self):
        classifications = Classification.objects.order_by('+name')
        return self.render('write.html', classifications=classifications)

    # 文章预览
    @expose('/preview', methods=('POST',))
    def preview(self):
        ''' Ajax请求，无论同步或者异步，都不能正确跳转；通过form.submit()实现
        article = request.get_json(force=True)
        return self.render('article.html', article=article, mode='preview')
        '''
        classification = Classification.objects(id=request.form.get('classification')).first()
        # TODO 异常处理
        article = {
            'title': request.form.get('title'),
            'content': request.form.get('content'),
            'abstract': request.form.get('abstract'),
            'classification': classification,
        }
        return self.render('article.html', article=article, mode='preview')


class CommentView(AuthModelView):
    column_searchable_list = ('content',)


'''
在自定义create_view和edit_view后，无需再自定义View
不过这是一种思路，可#总结
class WriteArticleView(AuthBaseView):
    @expose('/')
    def index(self):
        classifications = Classification.objects.order_by('+name')
        return self.render('write.html', classifications=classifications)
'''

'''
class EditArticleView(AuthBaseView):
    @expose('/')
    def index(self):
        articles = Article.objects.order_by('-create_time')
        # articles_admin.html模板文件已经删除，因为已经没有必要了
        return self.render('articles_admin.html', articles=articles)
        # return redirect(url_for('articles_all_show'))

    @expose('/article/edit/<string:article_id>', methods=('GET',))
    def article_edit(self):
        article = Article.objects(id=article_id).first()
        classifications = Classification.objects.order_by('+name')
        return render_template('write.html', classifications=classifications, article=article)
'''


# 自定义控制
class CustomizedAdminIndexView(admin.AdminIndexView):
    @expose('/')
    def index(self):
        if not flask_login.current_user.is_authenticated or flask_login.current_user.type != 1:
            return redirect(url_for('.login_view'))
        return super(CustomizedAdminIndexView, self).index()

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        return redirect(url_for('login'))

    @expose('/logout/')
    def logout_view(self):
        flask_login.logout_user()
        return redirect(url_for('.index'))


# 结束
