# coding:utf8

from . import api
from ihome import db
from flask import current_app, jsonify, request, g, session
from ihome.models import Area, House, Facility, HouseImage, User
from ihome.utils.commons import RET
from ihome import redis_store, constants
import json
from ihome.utils.commons import login_required
from ihome.utils.image_storage import storage


@api.route("/areas")
def get_area_info():
    """获取城区信息"""
    # 从redis中读取area_info
    try:
        resp_json = redis_store.get("area_info")
    except Exception as e:
        current_app.logger.error(e)
    else:
        if resp_json is not None:
            return resp_json, 200, {"Content-Type": "application/json"}
    
    # 查询数据库，读取城区信息       
    try:
        area_li = Area.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")
    
    area_dict_li = []
    for area in area_li:
        # 就对象转换为字典
        area_dict_li.append(area.to_dict())

    # 将数据转换为json字符串
    resp_dict = dict(errno=RET.OK, errmsg="ok", data=area_dict_li)
    resp_json = json.dumps(resp_dict)

    # 将数据保存到redis
    try:
        redis_store.setex("area_info", constants.AREA_INFO_REDIS_CACHE_EXPIRES, resp_json)
    except Exception as e:
        current_app.logger.error(e)
    
    return resp_json, 200, {"Content-Type": "application/json"}


@api.route("/houses/info", methods=["POST"])
@login_required
def save_house_info():
    
    # 获取数据
    user_id = g.user_id
    house_dict = request.get_json()

    title = house_dict.get("title")  # 房屋标题
    price = house_dict.get("price")  # 房屋单价
    area_id = house_dict.get("area_id")  # 房屋所属城区id
    address = house_dict.get("address")  # 房屋地址
    room_count = house_dict.get("room_count")  # 房屋包含房间数目
    acreage = house_dict.get("acreage")  # 房屋面积
    unit = house_dict.get("unit")  # 房屋布局（几室几厅）
    capacity = house_dict.get("capacity")  # 房屋容纳人数
    beds = house_dict.get("beds")  # 房屋卧床数目
    deposit = house_dict.get("deposit")  # 房屋押金
    min_days = house_dict.get("min_days")  # 最小入住天数
    max_days = house_dict.get("max_days")  # 最大入住天数

    # 校验参数
    if not all([title, price, area_id, address, room_count, acreage, unit, capacity, beds, deposit, min_days, max_days]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")
    
    # 判断金额是否正确
    try:
        price = int(float(price) * 100)
        deposit = int(float(deposit) * 100)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    
    # 判断城区是否存在
    try:
        area = Area.query.get(area_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    if area is None:
        return jsonify(errno=RET.NODATA, errmsg="城区信息有误")

    # 保存房屋信息
    house = House(
        user_id=user_id,
        area_id=area_id,
        title=title,
        price=price,
        address=address,
        room_count=room_count,
        acreage = acreage,
        unit = unit,
        capacity = capacity,
        beds = beds,
        deposit = deposit,
        min_days = min_days,
        max_days = max_days
    )
       
    # 处理房屋的设施信息
    facility_ids = house_dict.get("facility")

    # 如果用户勾选了设置信息，再保存到数据库
    if facility_ids:
        try:
            facilities = Facility.query.filter(Facility.id.in_(facility_ids)).all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="数据库异常")

        if facilities:
            # 表示有合法的设置数据，保存设施
            house.facilities = facilities
    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存数据失败")

    return jsonify(errno=RET.OK, errmsg="保存数据成功", data={"house_id": house.id})


@api.route("/houses/image", methods=["POST"])
@login_required
def save_house_image():
    """保存房屋图片"""
    image_files = request.files.get("house_image")
    house_id = request.form.get("house_id")

    if not all([image_files, house_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 判断house_id是否存在
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")
    
    if house is None:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")
    
    image_data = image_files.read()

    # 上传到七牛
    try:
        file_name = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="保存图片失败")

    # 将图片信息保存到数据库
    house_image = HouseImage(house_id=house_id, url=file_name)
    db.session.add(house_image)
     
    # 处理房屋的主图片
    if not house.index_image_url:
        house.index_image_url = file_name
        db.session.add(house)

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存失败")

    image_url = constants.QINIU_URL_DOMAIN + file_name

    return jsonify(errno=RET.OK, errmsg="保存成功", data={"image_url": image_url})
    

@api.route("/user/houses", methods=["GET"])
@login_required
def get_user_houses():
    """获取房东发布的房源信息"""
    user_id = g.user_id

    try:
        user = User.query.get(user_id)
        houses = user.houses
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取数据失败")
    
    # 将查询的房屋信息转换为字典存放到列表中
    house_list = []
    if houses:
        for house in houses:
            house_list.append(house.to_basic_dict())   
    return jsonify(errno=RET.OK, errmsg="ok", data={"houses": house_list})


@api.route("/houses/index", methods=["GET"])
def get_house_index():
    """获取主页幻灯片展示的房屋基本信息"""
    # 尝试从缓存中获取数据
    try:
        ret = redis_store.get("home_page_data")
    except Exception as e:
        current_app.logger.error(e)
        ret = None
    if ret:
        current_app.logger.info("hit house index info redis")
        # 因为redis中保存的是json字符串,所以直接进行字符串拼接返回
        return '{"errno": 0, "errmsg":"OK", "data":%s}' % ret, 200, {"Content-Type": "application/json"}
    else:
        try:
            # 查询数据库，返回房屋订单最多的５条数据
            houses = House.query.order_by(House.order_count.desc()).limit(constants.HOME_PAGE_MAX_HOUSES)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="获取数据失败")
        if not houses:
            return jsonify(errno=RET.NODATA, errmsg="查询无数据")
        
        houses_list = []
        for house in houses:
            if not house.index_image_url:
                continue
            houses_list.append(house.to_basic_dict())
        
        # 将数据转换为json，并保存到redis缓存
        json_houses = json.dumps(houses_list)
        try:
            redis_store.setex("home_page_data", constants.HOME_PAGE_DATA_REDIS_EXPIRES, json_houses)
        except Exception as e:
            current_app.logger.error(e)
        
        return '{"errno": 0, "errmsg":"OK", "data":%s}' % json_houses, 200, {"Content-Type": "application/json"}


@api.route("/houses/<int:house_id>", methods=["GET"])
def get_house_detail(house_id):
    """获取房屋详情"""
    # 前端在房屋详情页面访问时，如果浏览页面的用户不是该房屋的房东，则展示预定按钮，否则不展示
    # 所以需要后端返回登录用户的user_id
    # 尝试获取用户的登录信息，如果登录，返回登录用户的user_id,否则返回-1
    user_id = session.get("user_id", "-1")

    if not house_id:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 先从redis缓存获取信息
    try:
        ret = redis_store.get("house_info_%s" % house_id)
    except Exception as e:
        current_app.logger.error(e)
        ret = None
    if ret:
        current_app.logger.info("hit house info redis")
        # 因为redis中保存的是json字符串,所以直接进行字符串拼接返回
        return '{"errno": 0, "errmsg":"OK", "data":{"user_id":%s, "house":%s}}' % (user_id, ret), 200, {"Content-Type": "applcation/json"}


    # 查询数据库
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")
    
    if not house:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")
    
    # 将房屋对象转换为字典
    try:
        house_data = house.to_full_dict()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="数据出错")
    
    # 保存到redis
    json_house = json.dumps(house_data)
    try:
        redis_store.setex("house_info_%s" % house_id, constants.HOUSE_DETAIL_DATA_REDIS_EXPIRES, json_house)
    except Exception as e:
        current_app.logger.error(e)
    
    return '{"errno": 0, "errmsg":"OK", "data":{"user_id":%s, "house":%s}}' % (user_id, ret), 200, {"Content-Type": "applcation/json"}