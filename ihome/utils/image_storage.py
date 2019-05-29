# -*- coding: utf-8 -*-
# flake8: noqa
from qiniu import Auth, put_data, etag
import qiniu.config


#需要填写你的 Access Key 和 Secret Key
access_key = 'iEK6xNHwFyXng6dZOQFgrFeP_tr1QxCRa6NsB2r-'
secret_key = 'm3SmAo2N_6ia09C-m9JWhx2GfevYuDlD4Cm461Tm'

def storage(file_data):
    """
    上传文件到七牛
    :file_data 要上传的文件数据
    """
    #构建鉴权对象
    q = Auth(access_key, secret_key)

    #要上传的空间
    bucket_name = 'ihome'


    #生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, None, 3600)

    #要上传文件的本地路径
    ret, info = put_data(token, None, file_data)

    if info.status_code == 200:
        # 上传成功，返回文件名
        return ret.get("key")
    else:
        raise Exception("上传七牛失败")


if __name__ == "__main__":
    with open("ihome/utils/favicon.ico") as f:
        data = f.read()
        storage(data)