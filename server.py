# coding: utf-8

__author__ = 'Orclover'

"""
    个人博客
    ~~~~~~

    基于flask、MongoDB
"""

# DONE
# 1. 发布文章接口 + 页面
# 2. 发布评论接口，包括评论文章，也包括评论评论
# 3. 修改文章详情页面，主要在与子级评论和父级评论的渲染/展示
# 12. 文章内容编辑
# 3. classification的增删改查

# TODO todo-list
# 1. 页面样式与页面风格
# 2. 用户注册与登录(必要性?)
# 4. 文章的搜索功能，根据tags/classification
# 6. 评论文章/评论评论时，应该由jQuery去添加元素，还是将整个的重新加载
# 7. 纯接口，取回数据后，返回HTTP Status 200
# 8. 发布评论时的前后端校
# 9. 发布文章时的前后端校验
# 10. 使用pygments进行代码高亮显
# 11. 发布文章时，支持两种格式——富文本编辑/Markdown示
# 13. flask-admin中的级联删除/显示问题，如对于评论内容的增删改查等等
# 14. ?


from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash, make_response, Markup, json

# ODM mongoengine
from flask_mongoengine import MongoEngine
# import markdown
import misaka

import flask_login
# from hashlib import sha256
from werkzeug.security import generate_password_hash, check_password_hash
# wtforms
from wtforms import form, fields, validators

# 日志模块
import logging
import logging.config
from os import path
log_file_path = path.join(path.dirname(path.abspath(__file__)), 'logging.conf')
logging.config.fileConfig(log_file_path)
# TODO 使用的日志移入配置项，根据不同环境使用不同logger
logger = logging.getLogger("root")

# 创建应用
app = Flask(__name__)

# 从配置文件中读取配置
app.config.from_pyfile('app.conf')

# 不太明白这个的作用，看文档？！
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

# flask-admin初始化，已放入__main__中
# admin = Admin(app, name='博客管理后台', template_mode='bootstrap3')

# 创建数据库连接
db = MongoEngine(app)
# Or
# db = MongoEngine()
# db.init_app(app)


# flask_login相关，考虑从本文件中摘除
# 开始
login_manager = flask_login.LoginManager(app)


# TODO 将beautifulsoup从server.py中摘除，作为单独服务使用
from bs4 import BeautifulSoup


@login_manager.user_loader
def user_loader(id):
    '''
    TODO 提示用户不存在，在验证密码前的controller中做
    '''
    from bson import ObjectId
    if not ObjectId.is_valid(id):
        return
    user = User.objects(id=id).first()
    if not user:
        return

    return user


'''
暂时没有用到，request_loader存在的目的是什么？
@login_manager.request_loader
def request_loader(request):
    email = request.form.get('loginid')
    if email not in users:
        return

    user = User()
    user.login_id = email

    # DO NOT ever store passwords in plaintext and always compare password
    # hashes using constant-time comparison!
    user.is_authenticated = request.form['pw'] == users[email]['pw']

    return user
'''
# 结束

# flask_admin相关，考虑从本文件中摘除
# 开始
import flask_admin as admin
# from flask_admin.form import rules
from flask_admin.contrib.mongoengine import ModelView
from flask_admin import BaseView, expose


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
        return redirect(url_for('login', next=request.url))


# 基类，为BaseView添加用户身份控制
class AuthBaseView(BaseView):
    # flask-admin + flask-login
    def is_accessible(self):
        # 官方文档调用的是方法，如下：（错误，is_authenticated是current_user的一个属性）
        # return flask_login.current_user.is_authenticated()
        return flask_login.current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))


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
        return self.render('login.html')

    @expose('/logout/')
    def logout_view(self):
        flask_login.logout_user()
        return redirect(url_for('.index'))

# 结束


@login_manager.unauthorized_handler
def unauthorized_handler():
    return 'Unauthorized'

# 结束


# TODO 程序异常时添加处理，如关闭数据库连接等（MongoEngine应该可以自动关闭连接）
@app.teardown_appcontext
def close_db(error):
    # db.close()
    pass


# 页面
# 博客首页
@app.route('/')
def index():
    classifications = Classification.objects.order_by('+name')
    article = Article.objects.order_by('-create_time').first()
    '''
    if article:
        article.content = Markup(misaka.html(article.content))
    return render_template('index.html', classifications=classifications, article=article)
    '''

    '''
    '''
    # 添加最新发表文章列表，取最新发表的五篇文章
    recent_articles = Article.objects.order_by('-create_time').limit(5)
    if recent_articles:  # 文章不存在时，不进行转换
        article = recent_articles[0]
        #articles[0].content = Markup(misaka.html(articles[0].content))
        article.content = Markup(misaka.html(article.content))
    return render_template('index.html', classifications=classifications, article=article,
                next_article=recent_articles[1], recent_articles=recent_articles)



# 接口
# 用户注册
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        login_id = request.form.get('loginid')
        password = request.form.get('password')
        # 1. 使用hashlib.sha256作为摘要算法加密
        # encrypted_password = sha256(password.encode('utf-8')).hexdigest()
        # 2. 使用werkzeug.security中的摘要算法进行加密
        encrypted_password = generate_password_hash(password)
        if User.objects(login_id=login_id):
            # TODO 提示用户已存在
            pass
        User(login_id=login_id, password=encrypted_password).save()
        # return '注册成功', 200
        # TODO 跳转到注册成功页面
        # 如果需要，注册成功后帮助用户自动登录
        return redirect(url_for('index'))

    return render_template('register.html')


# 接口
# 用户登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        is_remember = request.form.get('remember', False)
        login_id = request.form.get('loginid')
        password = request.form.get('password')

        # 1. 使用hashlib.sha256作为摘要算法加密
        # if sha256(request.form.get('password').encode('utf-8')).hexdigest() == User.objects(login_id=login_id).first().password:
        # 2. 使用werkzeug.security中的摘要算法进行加密
        user = User.objects(login_id=login_id).first()
        if not user:
            # TODO 提示用户不存在
            pass
        elif check_password_hash(user.password, password):
            '''
            user = User()
            user.login_id = login_id
            user.id = login_id
            '''
            # remember参数默认为False，设置为True后可通过Cookie记录用户登录状态
            flask_login.login_user(user, remember=is_remember)
            # 经测试，query_param中没有next参数
            # next = request.args.get('next')
            return redirect(url_for('index'))

        # TODO 跳转到登录失败页面
        return '登录失败'

        '''
        if request.form.get('username') != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form.get('password') != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('index'))
        '''
    # return render_template('signin.html', error=error)
    return render_template('login.html', error=error)


# 接口
# 用户登出
@app.route('/logout')
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return redirect(url_for('index'))


# 测试
# 测试用户时候登录成功
@app.route('/protected')
@flask_login.login_required
# 相比于login_required注解，有一种更加严格的注解：fresh_login_required，这种注解要求session是fresh状态（从remember me自动登录时，
# 是non-fresh状态）
def protected():
    return 'Logged in as: ' + flask_login.current_user.login_id


# 页面
# 全部文章列表
@app.route('/articles', defaults={'page': 1})
@app.route('/articles/page-<int:page>', methods=['GET'])
def articles(page):
    # 分页相关
    start = (page - 1) * number_per_page
    limit = start + number_per_page
    tags = request.args.get('tags')
    classification = request.args.get('classification')
    if tags and classification:
        """ TODO 如何做到精确查询tags（多个）？
        tag_in_db_list = []
        if ',' in tags:
            for tag in tags.split(','):
                tag_in_db_list.append(Tag.objects(name=tag).first().id)
        else:
            tag_in_db_list.append(Tag.objects(name=tags).first().id)
        """
        tag_in_db = Tag.objects(name=tags).first()
        # 多条件查询，使用Q函数进行包装，通过|、&进行或、且操作
        articles = Article.objects(Q(tags=tag_in_db) & Q(classification=classification))\
        .order_by('-create_time')[start:limit]
        count = Article.objects(Q(tags=tag_in_db) & Q(classification=classification)).count()
    elif tags and not classification:
        tag_in_db = Tag.objects(name=tags).first()
        articles = Article.objects(tags=tag_in_db).order_by('-create_time')[start:limit]
        count = Article.objects(tags=tag_in_db).count()
    elif not tags and classification:
        articles = Article.objects(classification=classification).order_by('-create_time')[start:limit]
        count = Article.objects(classification=classification).count()
    else:
        articles = Article.objects.order_by('-create_time')[start:limit]  # .order_by('-create_time')
        count = Article.objects.count()
    from pagination import Pagination
    page_obj = Pagination(page, number_per_page, count)
    return render_template('articles.html', articles=articles, pagination=page_obj)

# 接口
# 分类文章列表
# 将接口合并到/articles,method=['GET']中
"""
@app.route('/articles/<string:classification_id>', methods=['GET'])
def articles_classify_show(classification_id):
    # ReferenceField
    # 使用如下查询方式
    articles = Article.objects(classification=classification_id)
    return render_template('articles.html', articles=articles)
"""


# 页面
# 文章详情
# 文章生成目录，方便查看，可以使用goose或html5lib（最终选型：beautifulsoup4）
# TODO 将生成目录功能抽取出来
from decorators import *
@app.route('/article/<string:article_id>')
@view_increase_wrapper
def article(article_id):
    logger.info("============================enter article pages===================================")
    article = Article.objects(id=article_id).first()
    # 使用flask.Markup进行转义
    article.content = Markup(misaka.html(article.content))
    # 指定使用lxml解析html，如不指定，默认使用html5lib
    soup = BeautifulSoup(article.content, 'lxml')
    # 为每个<h'x'>标签添加id，以便需要时进行定位
    from re import compile
    a_template = '<a href="#{id}">{value}</a>'
    # 使用collections.OrderedDict，以有序字典存储文章目录及对应缩进数
    from collections import OrderedDict
    article_contents = OrderedDict()
    for index, element in enumerate(soup.find_all(compile('^h[1-9]{1}$'))):
        element['id'] = index
        # 目录及对应缩进数
        article_contents.setdefault(Markup(a_template.format(id=index, value=element.string)), int(element.name[1:]) - 1)
        # 为每个<h'x'>标签添加permalink图标(¶)
        html_tag_a = soup.new_tag('a', **{'class': 'headerlink', 'href': '#' + str(index)})
        html_tag_a.string = '¶'
        element.append(html_tag_a)

    # 将修饰过到内容转换回来
    soup_string = str(soup.body.contents)
    # 去除转换过程中生成的的多余换行符 TODO 查看beautifulsoup API文档，能否在转换过程中不生成多余字符
    #article.content = Markup(soup_string[1:len(soup_string) - 1].replace(r", '\n\n',", "").replace(r", '\n'", ""))
    article.content = Markup(soup_string[1:len(soup_string) - 1].replace(r", '\n',", "").replace(r", '\n'", ""))
    # 是否需要按层级缩进显示目录
    need_indent = len({value for value in article_contents.values()}) != 1

    return render_template('article.html', article=article, mode='release',
                           article_contents=article_contents, need_indent=need_indent)


# 页面
# 文章预览
''' 已移入flask-admin中
@app.route('/article/preview', methods=['POST'])
def article_preview():
    # 使用flask.Markup进行转义
    # corresponding_article = Article.objects(id=article_id).first()
    # corresponding_article.content = Markup(misaka.html(corresponding_article.content))
    # return render_template('article.html', article=corresponding_article, mode='preview')
    article = request.get_json(force=True)
    # classification = Classification.objects(id=article.get('classification')).first()
    # article[kkk]
    return render_template('article.html', article=article, mode='preview')
'''


# 页面
# 新建文章
'''
* 现已移入管理端
@app.route('/article', methods=['GET'])
def article_create():
    classifications = Classification.objects.order_by('+name')
    return render_template('write.html', classifications=classifications)

# 页面
# 修改文章
@app.route('/article/edit/<string:article_id>', methods=['GET'])
def article_edit(article_id):
    article = Article.objects(id=article_id).first()
    classifications = Classification.objects.order_by('+name')
    return render_template('write.html', classifications=classifications, article=article)
'''


# 页面
# 关于我
@app.route('/about', methods=['GET'])
def about_me():
    return render_template('aboutme.html')


# 接口
# 发表评论
@app.route('/comment', methods=['POST'])
def comment_post():
    """
    # 通过request.get_json()获取JSON数据
    # ==========
    # get_json中必须有非空参数，为什么？因为——
    By default this function will return ``None`` if the mimetype is not
    :mimetype:`application/json` but this can be overridden by the
    ``force`` parameter.
    # ==========
    """
    data = request.get_json(force=True)
    user = User(name=data.get('username'), email=data.get('useremail'), link=data.get('userlink'), login_id='default_login_id', password='default_password').save()
    if data.get('parent_id'):
        parent_comment = Comment.objects(id=data.get('parent_id')).first()
        comment = Comment(content=data.get('content'), display_flag=app.config['DEFAULT_DISPLAY_FLAG'], user_info=user,
                          parent_comment=parent_comment).save()  # .save(cascade=True)
        parent_comment.sub_comments.append(comment)
        parent_comment.save(cascade=True)
    else:
        article = Article.objects(id=data.get('article_id')).first()
        comment = Comment(content=data.get('content'), display_flag=app.config['DEFAULT_DISPLAY_FLAG'],
                          user_info=user).save()  # cascade=True
        article.comments.append(comment)
        article.save()
    return '评论成功', 200
    # TODO 返回HTTP状态码
    """
    return make_response(status=200)
    response = make_response()
    response.status=200
    return response
    """


# 接口
# 删除评论
@app.route('/comment/<string:comment_id>', methods=['DELETE'])
def comment_delete(comment_id):
    Comment.objects(id=comment_id).first().delete()
    return '', 200


# 接口
# 删除文章
@app.route('/article/<string:article_id>', methods=['DELETE'])
def article_delete(article_id):
    Article.objects(id=article_id).first().delete()
    return '', 200


# 接口
# 发布/保存文章
# TODO 发布的文章需要支持markdown格式
@app.route('/article', methods=['POST', 'GET'])
def article_post():
    # 获取表单数据
    id = request.form.get('id')
    title = request.form.get('title')
    tags = request.form.get('tags')
    classification_id = request.form.get('classification')
    abstract = request.form.get('abstract')
    # content = markdown.markdown(request.form.get('content'), extensions=['markdown.extensions.extra'])
    # content = misaka.html(request.form.get('content'))
    # 保存数据库时，不保存HTML格式文本；在读取后，显示前，做HTML格式处理
    content = request.form.get('content')
    # 通过model中的默认值去添加，在此不再生成
    # create_time = datetime.datetime.now()

    '''
    移除文章中的Tags字段
    tag_doc = []
    if ',' in tags:
        for tag in tags.split(','):
            tag_doc.append(Tag(name=tag).save())
    else:
        tag_doc.append(Tag(name=tags).save())
    '''
    classification_doc = Classification.objects(id=classification_id).first()

    if not id:
        article_posted = Article(title=title, classification=classification_doc, abstract=abstract,
                                 content=content).save()
        return redirect('/article/' + str(article_posted.id))
    else:
        Article.objects(id=id).update_one(title=title,
                                          classification=classification_doc, abstract=abstract,
                                          content=content)
        """
        article_putted.title = title
        article_putted.tags = tag_doc
        article_putted.classification = classification_doc
        article_putted.abstract = abstract
        article_putted.content = content
        article_putted.reload()
        """
        return redirect('/article/' + id)


# Bootstrap Example
@app.route('/example')
def example():
    classifications = Classification.objects
    article = Article.objects.order_by('-create_time').first()
    article.content = Markup(misaka.html(article.content))
    return render_template('new.html', classifications=classifications, article=article)


# 接口
# 获取评论
@app.route('/comments/<string:article_id>')
def comments_corr_article(article_id):
    # comments = Article.objects(id=article_id)  # .only('comments')
    comments = Article.objects(id=article_id).only('comments').first().comments
    # TODO to_json()报错
    comments.to_json()
    for comment in comments:
        comment['user_info'] = User.objects(id=comment.user_info.id).first()
    return json.dumps(comments)


# 接口
# 搜索
# TODO MOCK版，待完成
@app.route('/search', methods=['POST'])
def search():
    if request.method != 'POST':
        return redirect(url_for('index'))
    query_condition = request.form.get('query', None)
    if query_condition:
        return redirect(url_for('results', query_condition=query_condition))
    else:
        return redirect(url_for('index'))

# 页面
# 搜索结果
@app.route('/q/<string:query_condition>', defaults={'page': 1})
@app.route('/q/<string:query_condition>/page-<int:page>')
def results(query_condition, page):
    # 按文章题目搜索
    # @see: http://docs.mongoengine.org/guide/querying.html#limiting-and-skipping-results
    start = (page - 1) * number_per_page
    limit = page * number_per_page
    articles = Article.objects(title__contains=query_condition).order_by('-create_time')[start:limit]
    count = Article.objects(title__contains=query_condition).count()
    from pagination import Pagination
    page_obj = Pagination(page, number_per_page, count)
    return render_template('results.html', articles=articles, pagination=page_obj)

# TODO 移入utils中
def url_for_other_page(page):
    '''
    两种类型的参数：
    request.view_args   REST风格的参数
    request.args        query parameter风格的参数
    由于本博客未统一使用某种风格，因此两种参数均需带上
    '''
    view_args = request.view_args.copy()
    view_args['page'] = page
    for k, v in request.args.items():
        view_args[k] = v
    return url_for(request.endpoint, **view_args)

# 注册函数，注册后可在全局使用
app.jinja_env.globals['url_for_other_page'] = url_for_other_page


# 启动服务
if __name__ == '__main__':
    # flask-admin相关我用接口发表文章
    # 开始
    admin = admin.Admin(app, name='博客管理后台', template_mode='bootstrap3', index_view=CustomizedAdminIndexView(),
                        base_template='customized_master.html')  # base_template='....html'
    admin.add_view(UserView(User, name="用户管理"))
    admin.add_view(ClassificationView(Classification, name="分类管理"))
    admin.add_view(ArticleView(Article, name="文章管理"))
    admin.add_view(CommentView(Comment, name="评论管理"))
    '''
    admin.add_view(WriteArticleView(name='写文章'))  # , endpoint='lalala'))
    admin.add_view(EditArticleView(name='文章列表'))
    admin.add_view()
    '''
    # 结束
    # 每页显示条数
    number_per_page = app.config['NUMBER_PER_PAGE']

    app.run(host=app.config['APP_HOST'], port=app.config['APP_PORT'])  # host='192.168.32.66', port=5000

