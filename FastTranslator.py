import requests,sys

KEYFROM = 'YDTranslateTest'
APIKEY = '1826356811'

r = requests.get('http://fanyi.youdao.com/openapi.do?keyfrom=' + KEYFROM +
'&key=' + APIKEY + '&type=data&doctype=json&version=1.1&q=' + sys.argv[1])
print r.text
