#coding: utf-8

# 图片验证码的redis有效期，单位：秒
IMAGE_CODE_REDIS_EXPIRES = 180

# 短信验证码的redis有效期，单位：秒
SMS_CODE_REDIS_EXPIRES = 300

# 发送短信验证码的间隔，单位：秒
SEND_SMS_CODE_INTERVAL = 60

# 登录错误尝试次数
LOGIN_ERROR_MAX_TIMES = 5

# 登录错误限制的时间，单位：秒
LOGIN_ERROR_FORBID_TIME = 600

# 七牛域名
QINIU_URL_DOMAIN = "http://ps7zhuv5m.bkt.clouddn.com/"

# area缓存时间，单位：秒
AREA_INFO_REDIS_CACHE_EXPIRES = 7200

# 主页图片显示数目
HOME_PAGE_MAX_HOUSES = 5

# 主页数据缓存过期时间
HOME_PAGE_DATA_REDIS_EXPIRES = 3600

# 房屋详情数据缓存过期时间
HOUSE_DETAIL_DATA_REDIS_EXPIRES = 3600

# 房屋详情页展示评论数目
HOUSE_DETAIL_COMMENT_DISPLAY_COUNTS = 20

# 房屋列表页面每页数据容量
HOUSE_LIST_PAGE_CAPACITY = 2

# 房屋列表页redis过期时间
HOUSE_LIST_PAGE_REDIS_CACHE_EXPIRES = 3600

# 支付宝的网关地址
ALIPAY_URL_PREFIX = "https://openapi.alipaydev.com/gateway.do?"