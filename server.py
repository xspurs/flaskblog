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

# TODO todo-list
# 1. 页面样式与页面风格
# 2. 用户注册与登录(必要性?)
# 3. classification的增删改查
# 4. 文章的搜索功能，根据tags/classification
# 6. 评论文章/评论评论时，应该由jQuery去添加元素，还是将整个的野蛮
# 7. 纯接口，取回数据后，返回HTTP Status 200
# 8. 发布评论时的前后端校验
# 9. 发布文章时的前后端校验
# 10. 使用pygments进行代码高亮显示
# 11. 发布文章时，支持两种格式——富文本编辑/Markdown
# 12. 文章内容编辑

from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash, make_response, Markup, json

# ODM mongoengine
from flask_mongoengine import MongoEngine
from model import *
# import markdown
import misaka

# 创建应用
app = Flask(__name__)

# 从配置文件中读取配置
app.config.from_pyfile('app.cfg')

# 不太明白这个的作用，看文档？！
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

# 创建数据库连接
db = MongoEngine(app)


# TODO 程序异常时添加处理，如关闭数据库连接等（MongoEngine应该可以自动关闭连接）
@app.teardown_appcontext
def close_db(error):
    # db.close()
    pass


# 页面
# 博客首页
@app.route('/')
def show_entries():
    classifications = Classification.objects
    return render_template('index.html', classifications=classifications)


# 接口

# 用户登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)


# 接口
# 用户登出
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))


# 页面
# 全部文章列表
@app.route('/articles', methods=['GET'])
def articles_all_show():
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
        articles = Article.objects(Q(tags=tag_in_db) & Q(classification=classification)).order_by('-create_time')
    elif tags and not classification:
        tag_in_db = Tag.objects(name=tags).first()
        articles = Article.objects(tags=tag_in_db).order_by('-create_time')
    elif not tags and classification:
        articles = Article.objects(classification=classification).order_by('-create_time')
    else:
        articles = Article.objects.order_by('-create_time')
    return render_template('articles.html', articles=articles)

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
@app.route('/article/<string:article_id>', methods=['GET'])
def article(article_id):
    # 使用flask.Markup进行转义
    corresponding_article = Article.objects(id=article_id).first()
    corresponding_article.content = Markup(misaka.html(corresponding_article.content))
    return render_template('article.html', article=corresponding_article)


# 页面
# 文章内容修改
@app.route('/article/edit/<string:article_id>', methods=['GET'])
def article_edit(article_id):
    article = Article.objects(id=article_id).first()
    classifications = Classification.objects
    return render_template('write.html', classifications=classifications, article=article)


# 页面
# 关于我
@app.route('/aboutme', methods=['GET'])
def about_me():
    return render_template('aboutme.html')


# 接口
# 发表评论
@app.route('/comment', methods=['POST'])
def post_comment():
    """
    # 通过request.get_json()获取JSON数据
    # ==========
    # get_json中必须有非空参数，为什么？
    # ==========
    """
    data = request.get_json(force=True)
    user = User(name=data.get('username'), email=data.get('useremail'), link=data.get('userlink')).save()
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
    return '', 200
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


# 页面
# 新建文章
@app.route('/article', methods=['GET'])
def article_create():
    classifications = Classification.objects
    return render_template('write.html', classifications=classifications)


# 接口
# 发布/保存文章
# TODO 发布的文章需要支持markdown格式
@app.route('/article', methods=['POST', 'GET'])
def article_post():
    # 加上就报错，不知道为什么
    # if not session.get('logged_in'):
    #    abort(401)

    # 获取表单数据
    id = request.form.get('id')
    title = request.form.get('title')
    tags = request.form.get('tags')
    classification_id = request.form.get('classification')
    abstract = request.form.get('abstract')
    # content = markdown.markdown(request.form.get('content'), extensions=['markdown.extensions.extra'])
    # content = misaka.html(request.form.get('content'))
    # 保存数据库时，不保存HTML格式文本
    content = request.form.get('content')
    # 通过model中的默认值去添加，在此不再生成
    # create_time = datetime.datetime.now()

    tag_doc = []
    if ',' in tags:
        for tag in tags.split(','):
            tag_doc.append(Tag(name=tag).save())
    else:
        tag_doc.append(Tag(name=tags).save())
    classification_doc = Classification.objects(id=classification_id).first()

    if not id:
        article_posted = Article(title=title, tags=tag_doc, classification=classification_doc, abstract=abstract,
                                 content=content).save()
        return redirect('/article/' + str(article_posted.id))
    else:
        Article.objects(id=id).update_one(title=title, tags=tag_doc,
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
    return render_template('example.html')


# 接口
# 获取评论
@app.route('/comments/<string:article_id>', methods=['GET'])
def comments_corr_article(article_id):
    # comments = Article.objects(id=article_id)  # .only('comments')
    comments = Article.objects(id=article_id).only('comments').first().comments
    # return json.dumps(comments), 400
    return json.dumps(comments)

# 启动服务
if __name__ == '__main__':
    app.run(host=app.config['APP_HOST'], port=app.config['APP_PORT'])  # host='192.168.32.66', port=5000
