# coding=utf-8
import requests, sys, json, os, StringIO, readline, argparse, ConfigParser

# reload(sys)
# sys.setdefaultencoding('utf-8')

KEY_FROM = 'YDTranslateTest'
API_KEY = '1826356811'

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)


def format(fg=None, bg=None, bright=False, bold=False, dim=False, reset=False):
    # manually derived from http://en.wikipedia.org/wiki/ANSI_escape_code#Codes
    codes = []
    if reset:
        codes.append("0")
    else:
        if not fg is None: codes.append("3%d" % (fg))
        # if not fg is None: codes.append("38;5;100")
        if not bg is None:
            if not bright:
                codes.append("4%d" % (bg))
            else:
                codes.append("10%d" % (bg))
        if bold:
            codes.append("1")
        elif dim:
            codes.append("2")
        else:
            codes.append("22")
    return "\033[%sm" % (";".join(codes))


def is_chinese(uchar):
    if uchar >= u'\u4e00' and uchar <= u'\u9fa5':
        return True
    else:
        return False


def copy_last_result(need_print):
    last = os.popen('cat /tmp/FastTranslator.last').read()
    os.popen('cat /tmp/FastTranslator.last | tr -d "\n" | pbcopy')
    if need_print:
        print 'copied ' + last


def translate(word):
    if args.only_say:
        os.popen('say ' + '"' + word + '"')
        return
    r = requests.get('http://fanyi.youdao.com/openapi.do?keyfrom=' + KEY_FROM +
                     '&key=' + API_KEY + '&type=data&doctype=json&version=1.1&q=' + word)
    # print r.text
    json_dict = json.loads(r.text)
    jsonStr = json.dumps(json_dict, ensure_ascii=False, sort_keys=True, indent=4, separators=(',', ': '))
    if args.debug:
        print '-' * 5
        print jsonStr
        print '-' * 5
    try:
        translation = json_dict['translation'][0].encode('utf-8')
    except:
        translation = ''
    linebuf = StringIO.StringIO()
    linebuf.write("%s%s%s " % (format(fg=MAGENTA, bg=None, bright=True), translation, format(reset=True)))
    line = linebuf.getvalue()
    print line
    os.popen('echo ' + '"' + translation + '"' + " > /tmp/FastTranslator.last")
    if args.copy:
        copy_last_result(False)
    # script = "osascript -e " + "\'display notification " + "\"" + translation + "\"" + " with title " + "\"" + word + "\"" + "\'"
    cmd_exists = lambda x: any(
        os.access(os.path.join(path, x), os.X_OK) for path in os.environ["PATH"].split(os.pathsep))
    if cmd_exists("terminal-notifier") and cmd_exists("reattach-to-user-namespace"):
        if args.noti:
            script = "terminal-notifier -title FastTranslator " + "-subtitle " + "\"" + word + "\"" + " -message " + "\"" + translation + "\"" + " -sender " + "\"com.googlecode.iterm2\""
            # print script
            os.popen(script)
    try:
        phonetic = json_dict['basic']['phonetic']
        linebuf = StringIO.StringIO()
        linebuf.write(
            "%s%s%s " % (format(fg=YELLOW, bg=None, bright=True), phonetic.encode('utf-8'), format(reset=True)))
        print linebuf.getvalue()
    # print phonetic.encode('utf-8')
    except:
        pass
    try:
        explains = json_dict['basic']['explains']
        for e in explains:
            print e.encode('utf-8')
    except:
        pass
    if args.verbose:
        try:
            web_result = json_dict['web']
            print
            for w in web_result:
                print w['key'].encode('utf-8') + '\t' + w['value'][0].encode('utf-8')
        except:
            pass
    global config_say
    if args.say or config_say:
        if is_chinese(unicode(word, 'utf-8')):
            if not is_chinese(unicode(translation, 'utf-8')):
                os.popen('say ' + '"' + translation + '"')
        else:
            os.popen('say ' + '"' + word + '"')


config_say = False
config = ConfigParser.ConfigParser()
config.read(os.path.join(os.path.dirname(os.path.realpath(__file__)), '.config'))
#  print(config.sections())
try:
    if config.getboolean('Default', 'Say'):
        config_say = True
except:
    pass

parser = argparse.ArgumentParser(description='Fast Translator')
parser.add_argument('-c', "--copy", help="copy translate result to clipboard", action="store_true")
parser.add_argument('-l', "--copy-last", help="copy last result to clipboard", action="store_true")
parser.add_argument('-n', "--noti", help="show notification, need terminal-notifier and reattach-to-user-namespace",
                    action="store_true")
parser.add_argument('-d', "--debug", help="debug mode", action="store_true")
parser.add_argument('-v', "--verbose", help="verbose output", action="store_true")
parser.add_argument('-s', "--say", help="say the result", action="store_true")
parser.add_argument('-o', "--only-say", help="only say the word", action="store_true")
parser.add_argument("text", help="translated words, empty to enter interactive mode", nargs='*')
args = parser.parse_args()
# print args.verbose
wordlist = ' '.join(args.text)
# print wordlist

# wordlist = sys.argv[1:]
if args.copy_last:
    copy_last_result(True)
else:
    if len(wordlist) != 0:
        translate(wordlist)
    else:
        print 'Enter text to translate, Ctrl-D to exit.\n'
        try:
            while True:
                word = raw_input()
                if word != '':
                    translate(word)
                    print '\n'
        except KeyboardInterrupt:
            pass
        except EOFError:
            pass
