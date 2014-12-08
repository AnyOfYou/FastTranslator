import requests,sys,json,os

#reload(sys)
#sys.setdefaultencoding('utf-8')

def is_chinese(uchar):
	if uchar >= u'\u4e00' and uchar<=u'\u9fa5':
		return True
	else:
		return False

KEYFROM = 'YDTranslateTest'
APIKEY = '1826356811'

try:
	word = sys.argv[1]
except IndexError:
	print 'Error'
	sys.exit()

r = requests.get('http://fanyi.youdao.com/openapi.do?keyfrom=' + KEYFROM +
'&key=' + APIKEY + '&type=data&doctype=json&version=1.1&q=' + word)
#print r.text
jsonDict = json.loads(r.text)
jsonStr = json.dumps(jsonDict, ensure_ascii=False,sort_keys=True,indent=4, separators=(',', ': '))
#print jsonStr

translation = jsonDict['translation'][0].encode('utf-8')
print translation
os.popen('echo ' + translation + " | " + "pbcopy")
#script = "osascript -e " + "\'display notification " + "\"" + translation + "\"" + " with title " + "\"" + word + "\"" + "\'"
script = "terminal-notifier -title FastTranslator " + "-subtitle " + "\"" + word + "\"" + " -message " + "\"" + translation + "\"" + " -sender " + "\"com.googlecode.iterm2\""
#print script
os.popen(script)

try:
	phonetic = jsonDict['basic']['phonetic']	
	print phonetic.encode('utf-8')
except:
	pass

try:
	explains = jsonDict['basic']['explains']
	for e in explains:
		print e.encode('utf-8')
except:
	pass

if is_chinese(unicode(word,'utf-8')):
	if not is_chinese (unicode(translation,'utf-8')):
		os.popen('say ' + translation)
else:
	os.popen('say ' + word)
