#coding:utf-8

from . import api
from ihome.utils.commons import login_required
from ihome.models import Order
from flask import g, current_app, jsonify
from ihome.utils.response_code import RET
from alipay import AliPay
import os
from ihome import constants

@api.route("/orders/<int:order_id>/payment", methods=["POST"])
@login_required
def order_pay(order_id):
    """发起支付宝支付"""
    user_id = g.user_id

    # 判断订单状态
    try:
        order = Order.query.filter(Order.id==order_id, Order.user_id==user_id, Order.status=="WAIT_PAYMENT").first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")
    
    if order is None:
        return jsonify(errno=RET.NODATA, errmsg="订单数据有误")
    
    app_private_key_string = open(os.path.join(os.path.dirname(__file__), "keys/app_private_key.pem")).read()
    alipay_public_key_string = open(os.path.join(os.path.dirname(__file__), "keys/alipay_public_key.pem")).read()
    # 创建支付宝sdk的工具对象
    alipay_client = AliPay(
        appid="2016100100638444",
        app_notify_url=None,  # 默认回调url
        app_private_key_string=app_private_key_string,
        # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        alipay_public_key_string=alipay_public_key_string,
        sign_type="RSA2", # RSA 或者 RSA2
        debug=True  # 默认False
    )
    
    # 手机网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
    order_string = alipay.api_alipay_trade_wap_pay(
        out_trade_no=order.id,
        total_amount=str(order.amount/100.0),
        subject="爱家租房　%ｓ" % order.id,  # 订单标题
        return_url="http://127.0.0.1:5000/orders.html",
        notify_url=None # 可选, 不填则使用默认notify url
    )

    # 构建让用户跳转的支付宝链接地址
    pay_url = constants.ALIPAY_URL_PREFIX + order_string

    return jsonify(errno=RET.Ok, errmsg="ok", data={"pay_url": pay_url})