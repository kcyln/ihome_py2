# coding: utf-8

from . import api
from ihome.utils.captcha.captcha import captcha
from ihome import redis_store, constants, db
from flask import current_app, jsonify, make_response, request
from ihome.utils.response_code import RET
from ihome.models import User
from ihome.libs.yuntongxun.sms import CCP
import random

@api.route('/image_codes/<image_code_id>')
def get_image_code(image_code_id):
    """
    获取图片验证码
    :params image_code_id 图片验证码编号
    :return  正常：验证码图片　异常：返回json
    """
    # 生成验证码图片
    #　名字，真实文本，图片数据
    name, text, image_data = captcha.generate_captcha()

    # 将验证码真实值与编号保存到redis中，设置有效期
    # 使用哈希维护有效期时只能整体设置，所以单条维护记录，选择字符串
    
    # redis_store.set("image_code_%s" % image_code_id, text)
    # redis_store.expire("image_code_%s" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES)
    try:
        redis_store.setex("image_code_%s" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        # 记录日志
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存验证码图片信息失败")
    # 返回图片
    resp = make_response(image_data)
    resp.headers["Content-Type"] = "image/jpg"
    return resp


# GET /api/v1.0/sms_codes/<mobile>?image_code=xxx&image_code_id=xxx
@api.route("/sms_codes/<re(r'1[34578]\d{9}'):mobile>")
def get_sms_code(mobile):
    """获取短信验证码"""
    # 获取参数
    image_code = request.args.get("image_code")
    image_code_id = request.args.get("image_code_id")
    # 校验参数
    if not all([image_code, image_code_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")
    
    #　业务处理
    #  从redis中取出真实的图片验证码
    try:
        real_image_code = redis_store.get("image_code_%s" % image_code_id)
    except Exception as e:
        current_app.logger.error(e) 
        return jsonify(errno=RET.DBERR, errmsg="redis数据库异常")
    # 判断图片验证码是否过期
    if real_image_code is None:
        return jsonify(errno=RET.NODATA, errmsg="图片验证码失效")
    # 与用户填写的进行对比
    if real_image_code.lower() != image_code.lower():
        # 用户填写错误
        return jsonify(errno=RET.DATAERR, errmsg="验证码填写错误")
    #  判断手机号是否存在
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        # return jsonify(errno=RET.DBERR, errmsg="mysql数据库异常")
    else:
        if user is not None:
            # 手机号码已存在
            return jsonify(errno=RET.DATAEXIST, errmsg="手机号已存在")
    # 如果不存在，生成短信验证码
    sms_code = "%6d" % random.randint(0,999999)

    # 保存真实的短信验证码
    try:
        redis_store.setex("sms_code_%s" % mobile,constants.SMS_CODE_REDIS_EXPIRES, sms_code)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存短信验证码异常")
        
    # 发送短信
    ccp = CCP()
    ccp.send_template_sms(mobile, [sms_code, ])

    
    
　