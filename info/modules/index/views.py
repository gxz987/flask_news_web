from flask import render_template, redirect, current_app, send_file, session, request, jsonify
from info.modules.index import index_blu
from info.models import User, News, Category
from response_code import RET


@index_blu.route("/news_list")
def get_news_list():
    """
    显示新闻列表，因是局部刷新，需要用jsonify返回数据故更改接口
    1、接收参数 cid  page  per_page
    2、校验参数是否合法
    3、查询出新闻（要关系分类）（根据创建时间排序）
    4、返回响应，及新闻数据
    :return:
    """
    # 1、接收参数
    cid = request.args.get("cid")
    page = request.args.get("page")
    per_page = request.args.get("per_page")

    # 2.校验数据
    try:
        cid = int(cid)
        page = int(page)
        per_page = int(per_page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 3、查询数据库
    try:
        paginate = News.query.filter(News.category_id==cid).order_by(News.create_time.desc()).paginate(page, per_page, False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库查询错误")

    news_list = paginate.items   # 当前页数据
    current_page = paginate.page    # 当前页数
    total_pages = paginate.pages  # 总页数

    news_dict_list = [news.to_basic_dict() for news in news_list]
    data = {
        "news_dict_list":news_dict_list,
        "news_page":current_page,
        "news_pages":total_pages
    }

    return jsonify(errno=RET.OK, errmsg="OK", data=data)




@index_blu.route('/')
def index():
    # 首页右上角的实现
    # 进入首页，需要判断用户是否登录，若已登录，将用户信息显示
    user_id = session.get("user_id")

    user = None
    if user_id:
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)

    # 1.显示新闻的点击排行
    clicks_news = []
    try:
        clicks_news = News.query.order_by(News.clicks.desc()).limit(6) # [news1, news2,...]
    except Exception as e:
        current_app.logger.error(e)

    clicks_news_li = [news.to_basic_dict() for news in clicks_news]

    # 2.显示新闻分类
    categorys = []

    try:
        categorys = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)

    categorys_dict_li = [category.to_dict() for category in categorys]
    # data = {"user_info":{"nick_name":"guo"}}
    data = {
        "user_info":user.to_dict() if user else None,
        "clicks_news_li":clicks_news_li,
        "categorys_dict_li":categorys_dict_li
    }

    print(data["categorys_dict_li"])

    return render_template("news/index.html", data=data)


@index_blu.route('/favicon.ico')
def favicon():
    # 返回logn图片
    # 第一种方法：
    # return redirect("/static/news/favicon.ico")  # 有302重定向问题

    # 第二种方法
    return current_app.send_static_file("news/favicon.ico")
    # send_static_file(filename)
    # Function used internally to send static files from the static
    # folder to the browser.

    # 第三种方法
    # return send_file("static/news/favicon.ico")
