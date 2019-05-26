# coding:utf8

import re

from flask import current_app, jsonify, request, session
from sqlalchemy.exc import IntegrityError
from ihome import redis_store, db, constants
from ihome.utils.response_code import RET
from ihome.models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import api


@api.route("/users", methods=["POST"])
def register():
    """注册
    请求的参数：　手机号，短信验证码，密码
    参数格式：json
    """
    # 获取请求的json数据，返回字典
    req_dict = request.get_json()

    mobile = req_dict.get("mobile")
    sms_code = req_dict.get("sms_code")
    password = req_dict.get("password")
    password2 = req_dict.get("password2")

    #　校验参数
    if not all([mobile, sms_code, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")
    
    # 判断手机号格式
    if not re.match(r"1[34578]\d{9}", mobile):
        # 手机号码不对
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式错误")
    
    if password != password2:
        return jsonify(errno=RET.PARAMERR, errmsg="两次密码不一致")
    
    # 校验短信验证码，是否过期，是否正确
    try:
        real_sms_code = redis_store.get("sms_code_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="读取短信验证码错误")
    if real_sms_code is None:
        return jsonify(errno=RET.NODATA, errmsg="短信验证码失效")
    # 删除redis中短信验证码，防止重复使用校验
    try:
        redis_store.delete("sms_code_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)
    
    if real_sms_code != sms_code:
        return jsonify(errno=RET.DATAERR, errmsg="短信验证码错误")
    
    # # 判断手机号是否注册过
    # try:
    #     user = User.query.filter_by(mobile=mobile).first()
    # except Exception as e:
    #     current_app.logger.error(e)
    #     return jsonify(errno=RET.DBERR, errmsg="数据库异常")
    # else:
    #     if user is not None:
    #         # 手机号码已存在
    #         return jsonify(errno=RET.DATAEXIST, errmsg="手机号已存在")
    
    # 处理密码

    # 注册
    user = User(name=mobile, mobile=mobile)
    # user.generate_password_hash(password)
    user.password = password
    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError as e:
        # 数据库操作错误回滚
        db.session.rollback()
        # 表示手机号重复，已经注册过
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAEXIST, errmsg="手机号已存在")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")
    # 保存登录状态到session
    session["name"] = mobile
    session["mobile"] = mobile
    session["user_id"] = user.id
    # 返回结果
    return jsonify(errno=RET.OK, errmsg="注册成功")


@api.route("/sessions", methods=["POST"])
def login():
    """登录
    请求的参数：　手机号，密码
    参数格式：json
    """
    # 获取参数
    req_dict = request.get_json()
    mobile = req_dict.get("mobile")
    password = req_dict.get("password")
    # 校验参数
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")
    # 手机号的格式校验
    if not re.match(r"1[34578]\d{9}", mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式错误")
    # 判断错误次数是否超过限制，如果超过限制，则返回
    user_ip = request.remote_addr  # 用户的ip地址
    try:
        access_nums = redis_store.get("access_nums_%s" % user_ip)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if access_nums is not None and int(access_nums) >= constants.LOGIN_ERROR_MAX_TIMES:
            return jsonify(errno=RET.REQERR, errmsg="错误次数过多，请稍后重试")

    # 从数据库查询手机号
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取用户信息失败")
    # 验证数据库密码和填写密码是否相同
    if user is None or not user.check_password(password):
        # 验证失败，记录错误次数
        try:
            redis_store.incr("access_nums_%s" % user_ip)
            redis_store.expire("access_nums_%s" % user_ip, constants.LOGIN_ERROR_FORBID_TIME)
        except Exception as e:
            current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="用户名或密码错误")
    # 业务处理：验证成功，保存登录状态
    session["name"] = user.name
    session["mobile"] = user.mobile
    session["user_id"] = user.id
    # 返回值
    return jsonify(errno=RET.OK, errmsg="登录成功")


@api.route("/session", methods=["GET"])
def check_login():
    """检查登录状态"""
    name = session.get("name")
    if name is not None:
        return jsonify(errno=RET.OK, errmsg="true", name=name)
    else:
        return jsonify(errno=RET.SESSIONERR, errmsg="false")
    

@api.route("/session", methods=["DELETE"])
def logout():
    """登出"""
    session.clear()
    return jsonify(errno=RET.OK, errmsg="OK")