# encoding:utf8

import datetime
from flask import jsonify, request, g, current_app, session
from . import api
from ihome import db, constants, redis_store
from ihome.utils.commons import login_required
from ihome.utils.response_code import RET
from ihome.models import User, House, Order

@api.route("/orders", methods=["POST"])
@login_required
def save_order():
    """保存订单"""
    user_id = g.user_id

    order_data = request.get_json()
    if not order_data:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    
    house_id = order_data.get("house_id")
    start_date_str = order_data.get("start_date")
    end_date_str = order_data.get("end_date")

    if not all([house_id, start_date_str, end_date_str]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    
    # 校验日期格式
    try:
        start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d")
        assert start_date<=end_date
        # 计算预订的天数
        days = (end_date - start_date).days + 1
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 查询房屋是否存在
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取信息失败")
    if not house:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    # 预定的房屋是否是房东自己的
    if user_id == house.user_id:
        return jsonify(errno=RET.ROLEERR, errmsg="不能预定自己的房屋")
    
    # 确保用户预订的时间内，房屋没有被人下单
    try:
        count = Order.query.filter(Order.house_id == house_id, Order.begin_date <= end_date, Order.end_date >= start_date).count()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="检查出错，请稍后重试")
    if count > 0:
        return jsonify(errno=RET.DATAERR, errmsg="房屋已被预定")

    amount = days * house.price

    order = Order(house_id=house_id,user_id=user_id,begin_date=start_date,
                end_date=end_date, days=days, house_price=house.price,
                amount=amount)
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存订单失败")

    return jsonify(errno=RET.OK, errmsg="OK", data={"order_id": order.id})


@api.route("/user/orders", methods=["GET"])
@login_required
def get_user_orders():
    """查询用户的订单信息"""
    user_id = g.user_id

    # 用户的身份，是作为房东查询客户的订单，还是作为房客查询别人房子的订单
    role = request.args.get("role", "")

    # 查询订单数据
    try:
        if "landlord" == role:
            # 以房东的身份查询订单
            houses = House.queery.filter(House.user_id == user_id).all()
            house_ids = [house.id for house in houses]

            orders = Order.query.filter(Order.house_id.in_(house_ids)).order_by(Order.create_time.desc()).all()
        else:
            orders = Order.query.filter(Order.user_id == user_id).order_by(Order.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询订单失败")

    # 将订单信息转换为字典数据
    orders_dict_list = []
    if orders:
        for order in orders:
            orders_dict_list.append(order.to_dict())
    
    return jsonify(errno=RET.OK, errmsg="OK", data={"orders": orders_dict_list})


@api.route("/orders/<int:order_id>/status", methods=["PUT"])
@login_required
def accept_reject_order(order_id):
    """接单｜拒单"""
    user_id = g.user_id

    # 获取参数
    req_data = request.get_json()
    if not req_data:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    
    # action参数表明客户端请求的是接单还是拒单行为
    action = req_data.get("action")
    if action not in ("accept", "reject"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        # 根据订单号查询订单，并且要求订单处于等待接单状态
        order = Order.query.filter(Order.id == order_id, Order.status == "WAIT_ACCEPT").first()
        house = order.house
    except Exception as e:
        current_app.loggre.error(e)
        return jsonify(errno=RET.DBERR, errmsg="无法获取订单数据")

    # 确保房东只能修改属于自己的房子订单
    if not order or house.user_id != user_id:
        return jsonify(errno=RET.REQERR, errmsg="操作无效")
    
    if action == "accept":
        # 接单，将订单状态设置为等待评论
        order.status = "WAIT_PAYMENT"
    elif action == "reject":
        # 拒单，要求用户传递拒单原因
        reason = req_data.get("reason")
        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
        order.status = "REJECTED"
        order.comment = reason
    
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.loggre.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="操作失败")
    return jsonify(errno=RET.OK, errmsg="ok")


@api.route("/orders/<int:order_id>/comment", methods=["PUT"])
@login_required
def save_order_comment(order_id):
    """保存订单评论信息"""
    user_id = g.user_id

    # 获取参数
    req_data = request.get_json()
    comment = req_data.get("comment")

    # 校验参数
    if not comment:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    
    try:
        # 需要确保只能评论自己下的订单，而且订单处于待评价状态
        order = Order.query.filter(Order.id == order_id,Order.user_id == user_id ,Order.status == "WAIT_COMMENT").first()
        house = order.house
    except Exception as e:
        current_app.loggre.error(e)
        return jsonify(errno=RET.DBERR, errmsg="无法获取订单数据")
    
    if not order:
        return jsonify(errno=RET.REQERR, errmsg="操作无效")
    
    try:
        # 将订单的状态设置为已完成
        order.status = "COMPLETE"
        # 保存订单的评价信息
        order.comment = comment
        # 将房屋的完成订单数加１
        house.order_count += 1
        db.session.add(order)
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.loggre.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="操作失败")
    
    # 因为房屋详情中有订单的评价信息，为了展示最新的评价信息，所以删除redis中关于本订单房屋的详情信息
    try:
        redis_store.delete("house_info_%s" % order.house.id)
    except Exception as e:
        current_app.loggre.error(e)

    return jsonify(errno=RET.OK, errmsg="ok")