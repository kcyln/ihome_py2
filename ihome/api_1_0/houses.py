# coding:utf8

from . import api
from flask import current_app, jsonify
from ihome.models import Area
from ihome.utils.commons import RET
from ihome import redis_store, constants
import json

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