# coding=utf-8
import requests,sys,json,os,StringIO,readline


#reload(sys)
#sys.setdefaultencoding('utf-8')

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

def format(fg=None, bg=None, bright=False, bold=False, dim=False, reset=False):
    # manually derived from http://en.wikipedia.org/wiki/ANSI_escape_code#Codes
    codes = []
    if reset: codes.append("0")
    else:
        if not fg is None: codes.append("3%d" % (fg))
        #if not fg is None: codes.append("38;5;100")
        if not bg is None:
            if not bright: codes.append("4%d" % (bg))
            else: codes.append("10%d" % (bg))
        if bold: codes.append("1")
        elif dim: codes.append("2")
        else: codes.append("22")
    return "\033[%sm" % (";".join(codes))

def is_chinese(uchar):
	if uchar >= u'\u4e00' and uchar<=u'\u9fa5':
		return True
	else:
		return False

def list_to_str(list):
	s = ""
	for i in list:
		if s =="":
			s = i
		else:
			s = s + " " + i
	return s

KEYFROM = 'YDTranslateTest'
APIKEY = '1826356811'

def translate(word):
	r = requests.get('http://fanyi.youdao.com/openapi.do?keyfrom=' + KEYFROM +
	'&key=' + APIKEY + '&type=data&doctype=json&version=1.1&q=' + word)
	# print r.text
	jsonDict = json.loads(r.text)
	jsonStr = json.dumps(jsonDict, ensure_ascii=False,sort_keys=True,indent=4, separators=(',', ': '))
	# print jsonStr
	try:
		translation = jsonDict['translation'][0].encode('utf-8')
	except:
		translation = ''
	linebuf = StringIO.StringIO()
	linebuf.write("%s%s%s " % (format(fg=MAGENTA,bg=None,bright=True), translation, format(reset=True)))
	line = linebuf.getvalue()
	print line
	# os.popen('echo ' + translation + " | " + "pbcopy")
	os.popen('echo ' + '"' + translation + '"' + " > /tmp/FastTranslator.last")
	#script = "osascript -e " + "\'display notification " + "\"" + translation + "\"" + " with title " + "\"" + word + "\"" + "\'"
	cmd_exists = lambda x: any(os.access(os.path.join(path, x), os.X_OK) for path in os.environ["PATH"].split(os.pathsep))
	if cmd_exists("terminal-notifier") and cmd_exists("reattach-to-user-namespace") :
		script = "terminal-notifier -title FastTranslator " + "-subtitle " + "\"" + word + "\"" + " -message " + "\"" + translation + "\"" + " -sender " + "\"com.googlecode.iterm2\""
		#print script
		os.popen(script)
	try:
		phonetic = jsonDict['basic']['phonetic']
		linebuf = StringIO.StringIO()
		linebuf.write("%s%s%s " % (format(fg=YELLOW,bg=None,bright=True), phonetic.encode('utf-8'), format(reset=True)))
		print linebuf.getvalue()
		#print phonetic.encode('utf-8')
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
			os.popen('say ' + '"' + translation + '"')
	else:
		os.popen('say ' + '"' + word + '"')



wordlist = sys.argv[1:]
if len(wordlist) != 0:
	if ''.join(wordlist) == '-c':
		last = os.popen('cat /tmp/FastTranslator.last').read()
		os.popen('cat /tmp/FastTranslator.last | tr -d "\n" | pbcopy')
		print 'copied ' + last
	else:
		translate(list_to_str(wordlist))
else:
	print 'Enter text to translate, Ctrl-D to exit.\n'
	try:
		while True:
			word = raw_input()
			if word !='':
				translate(word)
				print '\n'
	except KeyboardInterrupt:
		pass
	except EOFError:
		pass