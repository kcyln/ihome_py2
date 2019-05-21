#coding:utf-8

# import ConfigParser

from CCPRestSDK import REST

#主帐号
accountSid= '8a216da86ab0b4d2016ad04df9dc1676'

#主帐号Token
accountToken= '9e4fd2440870465e8c4aae3887e826bf'

#应用Id
appId='8a216da86ab0b4d2016ad04dfa35167d'

#请求地址，格式如下，不需要写http://
serverIP='app.cloopen.com'

#请求端口 
serverPort='8883'

#REST版本号
softVersion='2013-12-26'

  # 发送模板短信
  # @param to 手机号码
  # @param datas 内容数据 格式为数组 例如：{'12','34'}，如不需替换请填 ''
  # @param $tempId 模板Id

# def sendTemplateSMS(to,datas,tempId):

    
#     #初始化REST SDK
#     rest = REST(serverIP,serverPort,softVersion)
#     rest.setAccount(accountSid,accountToken)
#     rest.setAppId(appId)
    
#     result = rest.sendTemplateSMS(to,datas,tempId)
#     for k,v in result.iteritems(): 
        
#         if k=='templateSMS' :
#                 for k,s in v.iteritems(): 
#                     print '%s:%s' % (k, s)
#         else:
#             print '%s:%s' % (k, v)
    
   
# #sendTemplateSMS(手机号码,内容数据,模板Id)


class CCP(object):
	"""自己封装的用来发送短信的辅助类"""
	# 用来保存对象的类属性
	instance = None

	def __new__(cls):
		# 判断CCP类是否有已经创建好的对象，如果没有，创建一个，并且保存；如果有，将保存的对象直接返回
		if cls.instance is None:
			obj = super(CCP, cls).__new__(cls)

			#初始化REST SDK
			obj.rest = REST(serverIP,serverPort,softVersion)
			obj.rest.setAccount(accountSid,accountToken)
			obj.rest.setAppId(appId)

			cls.instance = obj

		return cls.instance

	def send_template_sms(self, to, datas, temp_id):

		result = self.rest.sendTemplateSMS(to,datas,temp_id)
		# for k,v in result.iteritems(): 
			
		# 	if k=='templateSMS' :
		# 			for k,s in v.iteritems(): 
		# 				print '%s:%s' % (k, s)
		# 	else:
		# 		print '%s:%s' % (k, v)
		# ********************************
		# smsMessageSid:833cd26fcf5944808e3dee66d9a6453f
		# dateCreated:20190521211935
		# statusCode:000000

		status_code = result.get("statusCode")
		if status_code == "000000":
			# 表示发送成功
			return 0
		else:
			return -1

if __name__ == "__main__":
	ccp = CCP()
	ret = ccp.send_template_sms("17368878315", ["1234", "5"], 1)
	print ret
