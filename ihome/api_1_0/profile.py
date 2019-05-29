# coding:utf8

from flask import jsonify, request, g, current_app, session
from . import api
from ihome import db, constants
from ihome.utils.commons import login_required
from ihome.utils.response_code import RET
from ihome.utils.image_storage import storage
from ihome.models import User


@api.route("/users/avatar", methods=["POST"])
@login_required
def set_avatar():
    """设置用户的头像"""
    user_id = g.user_id
    # 获取图片
    image_file = request.files.get("avatar")
    if image_file is None:
        return jsonify(errno=RET.PARAMERR, errmsg="未上传图片")
    image_data = image_file.read()
    # 调用七牛上传图片
    try:
        file_name = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="上传图片失败")
    
    # 保存文件名到数据库中
    try:
        User.query.filter_by(id=user_id).update({"avatar_url": file_name})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存图片失败")

    # 保存成功返回
    avatar_url = constants.QINIU_URL_DOMAIN + file_name
    return jsonify(errno=RET.OK, errmsg="保存成功", data={"avatar_url": avatar_url})

    
@api.route("/users/username", methods=["PUT"])
@login_required
def change_user_name():
    """修改用户名"""
    user_id = g.user_id
    req_dict = request.get_json()
    if not req_dict:
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")
    username = req_dict.get("username")
    if username is None or username.strip() is None or username.strip()=="":
        return jsonify(errno=RET.PARAMERR, errmsg="用户名不得为空")
    
    
    # try:
    #     user = User.query.filter_by(id=user_id).first()
    # except Exception as e:
    #     current_app.logger.error(e)
    #     return jsonify(errno=RET.DBERR, errmsg="数据库错误")
    # if username == user.name:
    #     return jsonify(errno=RET.PARAMERR, errmsg="用户名已存在")

    # 利用数据库唯一索引来判断用户名是否重复
    # 保存用户名到数据库中
    try:
        User.query.filter_by(id=user_id).update({"name": username})
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存失败，数据库错误或用户名已存在")
    # 保存成功返回
    session["name"] = username
    return jsonify(errno=RET.OK, errmsg="保存成功")


@api.route("/users/profile", methods=["GET"])
@login_required
def get_user_profile():
    """获取用户信息"""
    user_id = g.user_id
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取用户信息失败")
    
    return jsonify(errno=RET.OK, errmsg="获取成功", data=user.to_dict())


@api.route("/users/auth", methods=["GET"])
@login_required
def get_user_auth():
    """获取实名认证信息"""
    user_id = g.user_id
    # 保存实名信息到数据库中
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取用户实名信息失败")
    
    if user is None:
        return jsonify(errno=RET.NODATA, errmsg="没有查询到数据")
    
    return jsonify(errno=RET.OK, errmsg="获取成功", data=user.auth_to_dict())


@api.route("/users/auth", methods=["POST"])
@login_required
def set_user_auth():
    """设置实名认证信息"""
    user_id = g.user_id
    req_dict = request.get_json()

    real_name = req_dict.get("real_name")
    id_card = req_dict.get("id_card")

    if not all([real_name, id_card]):
        return jsonify(errno=RET.PARAMERR, errmsg="请输入姓名和身份证号")

    # 保存实名信息到数据库中
    try:
        # User.query.filter_by(id=user_id).update({"real_name": real_name, "id_card": id_card})
        User.query.filter_by(id=user_id, real_name=None, id_card=None).update({"real_name": real_name, "id_card": id_card})
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存实名信息失败")
    # 保存成功返回
    return jsonify(errno=RET.OK, errmsg="保存成功")