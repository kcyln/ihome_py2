# coding:utf8

from flask import jsonify, request, g, current_app
from . import api
from ihome import db, constants
from ihome.utils.commons import login_required
from ihome.utils.response_code import RET
from ihome.utils.image_storage import storage
from ihome.models import User


@api.route("/users/avatar", methods=["GET", "POST"])
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

    
