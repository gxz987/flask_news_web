import datetime
from flask import render_template, request, current_app, session, url_for, redirect, g, jsonify

from info import constants
from info.utils.common import user_login
from info.modules.admin import admin_blu
from info.models import User, News
from info.utils.response_code import RET


@admin_blu.route("/news_edit")
def news_edit():
    """
    新闻编辑
    :return:
    """
    # 当表单是ｐｏｓｔ请求提交的时候才用request.form, 当表单是ｇｅｔ请求提交的时候用request.args
    page = request.args.get("page", 1)
    keywords = request.args.get("keywords", None)
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    news_list = []
    current_page = 1
    total_page = 1
    filters = [News.status == 0]
    # 如果关键字存在，那么就添加关键字搜索
    if keywords:
        filters.append(News.title.contains(keywords))
    try:
        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page,
                                                                                          constants.ADMIN_NEWS_PAGE_MAX_COUNT,
                                                                                          False)
        news_list = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    news_dict_li = [news.to_basic_dict() for news in news_list]

    data = {
        "news_dict_li": news_dict_li,
        "current_page": current_page,
        "total_page": total_page
    }

    return render_template("admin/news_edit.html", data=data)


@admin_blu.route("/news_review_action", methods=["POST"])
def news_review_action():
    """
    新闻审核
    :return:
    """
    news_id = request.json.get("news_id")
    action = request.json.get("action")

    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不全")
    if action not in ["accept", "reject"]:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 查询到指定的新闻数据
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库查询失败")
    if not news:
        return jsonify(errno=RET.NODATA, errmsg="未查询到数据")

    if action == "accept":
        # 代表审核通过
        news.status = 0
    else:
        # 代表拒绝通过
        reason = request.json.get("reason")
        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg="请输入拒绝通过的原因")
        news.status = -1
        news.reason = reason

    return jsonify(errno=RET.OK, errmsg="OK")


@admin_blu.route("/news_review_detail/<int:news_id>")
def news_review_detail(news_id):
    """
    新闻审核新闻详情页面的渲染
    :param news_id:
    :return:
    """
    news = None
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
    if not news:
        return render_template("admin/news_review_detail.html", data={"errmsg": "新闻未查到"})
    print(news)
    data = {
        "news": news.to_dict()
    }

    return render_template("admin/news_review_detail.html", data=data)


@admin_blu.route("/news_review")
def news_review():
    """
    新闻审核
    :return:
    """
    page = request.args.get("page", 1)
    keywords = request.args.get("keywords", None)
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    news_list = []
    current_page = 1
    total_page = 1
    filters = [News.status != 0]
    # 如果关键字存在，那么就添加关键字搜索
    if keywords:
        filters.append(News.title.contains(keywords))
    try:
        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page,
                                                                                          constants.ADMIN_NEWS_PAGE_MAX_COUNT,
                                                                                          False)
        news_list = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    news_dict_li = [news.to_review_dict() for news in news_list]
    print(news_dict_li)
    data = {
        "news_dict_li": news_dict_li,
        "current_page": current_page,
        "total_page": total_page
    }

    return render_template("admin/news_review.html", data=data)


@admin_blu.route("/user_list")
def user_list():
    """
    用户列表
    :return:
    """
    page = request.args.get("page", 1)
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    users = []
    current_page = 1
    total_page = 1
    try:
        paginate = User.query.filter(User.is_admin == 0).paginate(page, constants.ADMIN_USER_PAGE_MAX_COUNT, False)
        users = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)
    user_dict_li = [user.to_admin_dict() for user in users]  # 需要用到注册时间和最后一次登录时间

    data = {
        "user_dict_li": user_dict_li,
        "current_page": current_page,
        "total_page": total_page
    }

    return render_template("admin/user_list.html", data=data)


@admin_blu.route("/user_count")
def user_count():
    """
    用户数据展示
    :return:
    """
    # 1.总人数(不包含后台管理用户)
    total_count = 0
    try:
        total_count = User.query.filter(User.is_admin == 0).count()
    except Exception as e:
        current_app.logger.error(e)

    t = datetime.datetime.now()
    # 2.月新增人数
    month_count = 0
    begin_month_date_str = "%d-%02d-01" % (t.year, t.month)
    # 将字符串转成datetime对象
    begin_month_date = datetime.datetime.strptime(begin_month_date_str, "%Y-%m-%d")
    try:
        month_count = User.query.filter(User.is_admin == 0, User.create_time > begin_month_date).count()
    except Exception as e:
        current_app.logger.error(e)

    # 3.日新增人数
    day_count = 0
    begin_day_date_str = "%d-%02d-%02d" % (t.year, t.month, t.day)
    begin_day_date = datetime.datetime.strptime(begin_day_date_str, "%Y-%m-%d")
    try:
        day_count = User.query.filter(User.is_admin == 0, User.create_time > begin_day_date).count()
    except Exception as e:
        current_app.logger.error(e)

    # 4.折线图数据
    active_date = []
    active_count = []
    # 取到今天的时间字符串
    today_date_str = "%d-%02d-%02d" % (t.year, t.month, t.day)
    # 转成时间对象
    today_date = datetime.datetime.strptime(today_date_str, "%Y-%m-%d")

    for i in range(31):
        # 取到某一天的０点０分
        begin_date = today_date - datetime.timedelta(days=i - 0)
        # 取到下一天的０点０分
        end_date = today_date - datetime.timedelta(days=i - 1)
        count = User.query.filter(User.is_admin == 0,
                                  User.last_login >= begin_date,
                                  User.last_login < end_date).count()
        begin_date_str = begin_date.strftime("%Y-%m-%d")
        active_count.append(count)
        active_date.append(begin_date_str)
    active_date.reverse()
    active_count.reverse()

    data = {
        "total_count": total_count,
        "month_count": month_count,
        "day_count": day_count,
        "active_count": active_count,
        "active_date": active_date
    }

    return render_template("admin/user_count.html", data=data)


@admin_blu.route('/index')
@user_login
def index():
    """
    后台管理首页
    :return:
    """
    user = g.user
    data = {
        "user_info": user.to_dict()
    }
    return render_template("admin/index.html", data=data)


@admin_blu.route("/login", methods=["GET", "POST"])
def login():
    """
    后台管理员登录页面
    :return:
    """
    if request.method == "GET":
        # 在get请求中，先从session中去user_id和is_admin，如能取到，直接重定向到首页
        user_id = session.get("user_id")
        is_admin = session.get("is_admin")
        if user_id and is_admin:
            return redirect(url_for("admin.index"))
        return render_template("admin/login.html")

    username = request.form.get("username")
    password = request.form.get("password")

    if not all([username, password]):
        return render_template("admin/login.html", errmsg="请输入用户名或密码")
    try:
        user = User.query.filter(User.is_admin==1, User.mobile==username).first()
    except Exception as e:
        current_app.logger.error(e)
        return render_template("admin/login.html", errmsg="用户信息查询失败")
    if not user:
        return render_template("admin/login.html", errmsg="未查到用户信息")
    if not user.check_passowrd(password):
        return render_template("admin/login.html", errmsg="用户名或密码错误")

    session["user_id"] = user.id
    session["is_admin"] = user.is_admin

    return redirect(url_for("admin.index"))
