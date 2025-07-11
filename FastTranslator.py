# coding=utf-8

import argparse
import json
import os
import readline
import requests
import sys
import time
import hashlib
import time
import uuid
import re

try:
    from StringIO import StringIO
    import ConfigParser
except ImportError:
    from io import StringIO
    import configparser

try:
    import api_config
except ImportError:
    print("API config no found, exit")
    sys.exit(1)

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)


def load_config(args):
    try:
        config = ConfigParser.ConfigParser()
    except NameError:
        config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(os.path.realpath(__file__)), '.config'))
    try:
        for k, v in config.items('Default'):
            if k == 'Say'.lower():
                args.say = v == 'True'
            elif k == 'Verbose'.lower():
                args.verbose = v == 'True'
            elif k == 'Noti'.lower():
                args.noti = v == 'True'
            elif k == 'Src'.lower():
                args.src = v
            elif k == 'Copy'.lower():
                args.copy = v == 'True'
    except:
        pass


def format(fg=None, bg=None, bright=False, bold=False, dim=False, reset=False):
    # Manually derived from http://en.wikipedia.org/wiki/ANSI_escape_code#Codes
    codes = []
    if reset:
        codes.append("0")
    else:
        if fg is not None:
            codes.append("3%d" % (fg))
        # if fg is not None:
        #     codes.append("38;5;100")
        if bg is not None:
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
    if sys.version_info[0] >= 3:
        uchar = str(uchar)
    else:
        uchar = unicode(uchar, "utf-8")
    if u'\u4e00' <= uchar <= u'\u9fff':
        return True
    else:
        return False


def is_english(s):
    return len(s) == len(s.encode())


def copy_last_result(need_print):
    last = os.popen('cat /tmp/FastTranslator.last').read()
    os.popen('cat /tmp/FastTranslator.last | tr -d "\n" | pbcopy')
    if need_print:
        print('Copied: ' + last)


def to_str(text):
    if not isinstance(text, str):
        text = text.encode('utf-8')
    return text


def print_fg(text, color):
    line_buf = StringIO()
    line_buf.write("%s%s%s " % (format(fg=color, bright=True), text, format(reset=True)))
    line = line_buf.getvalue()
    print(line)


def print_dim(text):
    line_buf = StringIO()
    line_buf.write("%s%s%s " % (format(dim=True), text, format(reset=True)))
    line = line_buf.getvalue()
    print(line)


def send_noti(title, message):
    # script = "osascript -e " + "\'display notification " + "\"" + message + "\"" + " with title " + "\"" + title + "\"" + "\'"
    cmd_exists = lambda x: any(
        os.access(os.path.join(path, x), os.X_OK) for path in os.environ["PATH"].split(os.pathsep))
    if cmd_exists("terminal-notifier") and cmd_exists("reattach-to-user-namespace"):
        script = "terminal-notifier -title FastTranslator " + "-subtitle " + "\"" + title + "\"" + " -message " + "\"" + message + "\"" + " -sender " + "\"com.googlecode.iterm2\""
        # print(script)
        os.popen(script)


def say_result(text, translation):
    if is_english(translation):
        os.popen('say ' + '"' + translation + '"')
    elif is_english(text):
        os.popen('say ' + '"' + text + '"')
    else:
        pass


def yd_add_auth_params(appKey, appSecret, params):
    q = params.get('q')
    if q is None:
        q = params.get('img')
    salt = str(uuid.uuid1())
    curtime = str(int(time.time()))
    sign = yd_calculate_sign(appKey, appSecret, q, salt, curtime)
    params['appKey'] = appKey
    params['salt'] = salt
    params['curtime'] = curtime
    params['signType'] = 'v3'
    params['sign'] = sign


def yd_calculate_sign(appKey, appSecret, q, salt, curtime):
    strSrc = appKey + yd_get_input(q) + salt + curtime + appSecret
    return yd_encrypt(strSrc)


def yd_encrypt(strSrc):
    hash_algorithm = hashlib.sha256()
    hash_algorithm.update(strSrc.encode('utf-8'))
    return hash_algorithm.hexdigest()


def yd_get_input(input):
    if input is None:
        return input
    inputLen = len(input)
    return input if inputLen <= 20 else input[0:10] + str(inputLen) + input[inputLen - 10:inputLen]


def translate_youdao(text):
    translation = ""
    phonetic = ""
    explains = []
    web_results = []
    json_dict = {}

    via_api = True

    if via_api:
        q = text
        lang_from = 'auto'
        lang_to = 'auto'

        data = {'q': q, 'from': lang_from, 'to': lang_to}
        yd_add_auth_params(api_config.YOUDAO_APP_ID, api_config.YOUDAO_APP_KEY, data)
        header = {'content-type': 'application/x-www-form-urlencoded'}
        try:
            r = requests.post('https://openapi.youdao.com/api', data, header)
            json_dict = json.loads(r.content)

        except Exception as e:
            print(e)
            return

        try:
            if 'translation' in json_dict:
                translation = to_str(json_dict['translation'][0]).strip("\"")
            else:
                translation = json_dict['web'][0]['value'][0]
            if 'phonetic' in json_dict['basic']:
                phonetic = to_str(json_dict['basic']['phonetic'])
            if 'explains' in json_dict['basic']:
                explains = json_dict['basic']['explains']
            web_results = json_dict['web']
        except:
            pass

    r = requests.get('http://mobile.youdao.com/dict?le=eng&q=' + text)
    request_text = r.text
    # print(request_text)
    phonetic_pattern = r'"phonetic">(.+)<\/span>'
    try:
        phonetic = re.findall(phonetic_pattern, request_text)[-1].replace('[', '').replace(']', '')
    except:
        pass
    explains_pattern = r'<li>(\w.+)<\/li>'
    explains = re.findall(explains_pattern, request_text)
    if not explains:
        explains = re.findall(r'<a class="clickable".+>(.+[^:])</a>', request_text)

    if not translation and explains:
        # print(explains[0])
        translation = re.sub(r'（.*?）', '', explains[0].split('；')[0].split('，')[0].split('. ')[-1]).strip()

    if not web_results:
        r = requests.get('http://mobile.youdao.com/singledict?q=' + text + '&dict=web_trans&le=eng&more=false')
        request_text = r.text
        details = re.findall(r'pointer;">([\s\S]+?)\s</span>', request_text, re.DOTALL)
        values = []
        for i in range(len(details)):
             value = details[i].replace('<span class="grey">', '').replace('</span>\r\n', '').replace(' ', '').replace(']', '] ').strip()
             values.append(value)
             # web_results.append({'key': text, 'value': [value]})
        if values:
            web_results.append({'key': text, 'value': values})

        r = requests.get('http://mobile.youdao.com/singledict?q=' + text + '&dict=syno&le=eng&more=false')
        request_text = r.text
        details = re.findall(r'<a class="clickable" .+>(.+)<\/a>', request_text)
        if details:
            web_results.append({'key': text, 'value': details})
        # print(web_results)
    return json_dict, translation, phonetic, explains, web_results


def translate_deepl(text):
    translation = ""
    phonetic = ""
    explains = []
    web_results = []
    json_dict = {}

    via_api = True

    try:
        if is_chinese(text):
            target_lang = 'EN'
            source_lang = 'ZH'
        else:
            target_lang = 'ZH'
            source_lang = 'EN'
        if via_api:
            data = {'auth_key': api_config.DEEPL_AUTH_KEY, 'text': text, 'target_lang': target_lang}
            r = requests.post('https://api-free.deepl.com/v2/translate', data=data)
        else:
            headers = {
                'authority': 'www2.deepl.com',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36',
                'content-type': 'application/json',
            }
            params = (
                ('method', 'LMT_handle_jobs'),
            )
            data = '{"jsonrpc":"2.0","method": "LMT_handle_jobs","params":{"jobs":[{"kind":"default","raw_en_sentence":"Text","raw_en_context_before":[],"raw_en_context_after":[],"preferred_num_beams":4}],"lang":{"preference":{"weight":{},"default":"default"},"source_lang_computed":"EN","target_lang":"ZH"},"priority":1,"commonJobParams":{"browserType":1},"timestamp":1635842383821},"id":17200000}'
            json_data = json.loads(data)
            json_data["params"]["jobs"][0]["raw_en_sentence"] = text
            json_data["params"]["lang"]["source_lang_computed"] = source_lang
            json_data["params"]["lang"]["target_lang"] = target_lang
            json_data["params"]["timestamp"] = str(int(time.time())) + "000"
            r = requests.post('https://www2.deepl.com/jsonrpc', headers=headers, params=params,
                              data=data.encode('utf-8'))
        # print(r.text)
        json_dict = json.loads(r.text)
    except Exception as e:
        print(e)
        return

    try:
        if via_api:
            translation = to_str(json_dict["translations"][0]["text"])
        else:
            translation = to_str(json_dict['result']['translations'][0]["beams"][0]['postprocessed_sentence'])
            for i in json_dict['result']['translations'][0]["beams"]:
                explains.append(to_str(i['postprocessed_sentence']))
    except:
        pass
    return json_dict, translation, phonetic, explains, web_results


def print_result(args, text, result):
    if not result or not result[1]:
        print("Error")
        print("Result: ")
        print(result)
        return

    json_dict, translation, phonetic, explains, web_results = result

    if args.debug:
        json_str = json.dumps(json_dict, ensure_ascii=False, sort_keys=True, indent=4, separators=(',', ': '))
        print('-' * 5)
        print(json_str)
        print('-' * 5)

    print_fg(translation, MAGENTA)
    os.popen('echo ' + '"' + str(translation) + '"' + " > /tmp/FastTranslator.last")

    if args.copy:
        copy_last_result(False)
    if args.noti:
        send_noti(text, translation)
    if phonetic:
        print_fg(phonetic, YELLOW)
    for e in explains:
        print(to_str(e))
    if args.verbose:
        try:
            # print()
            for w in web_results:
                key = to_str(w['key'])
                value = ''
                for wv in w['value']:
                    if len(value) == 0:
                        value = to_str(wv)
                    else:
                        value = value + ", " + to_str(wv)
                print_dim(key + ' - ' + value)
                # print(to_str(w['key']) + ' - ' + to_str(w['value'][0]))
        except:
            pass
    if args.say:
        say_result(text, translation)


def cleanup_text(text):
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F700-\U0001F77F"
        "\U0001F780-\U0001F7FF"
        "\U0001F800-\U0001F8FF"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FA6F"
        "\U0001FA70-\U0001FAFF"
        "\U00002600-\U000026FF"
        "\U00002700-\U000027BF"
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub(r'', text)


def translate(args, text):
    text = cleanup_text(text)
    # print(text)
    if args.only_say:
        os.popen('say ' + '"' + text + '"')
        return

    if args.src == 'youdao':
        result = translate_youdao(text)
        print_result(args, text, result)
    elif args.src == 'deepl':
        result = translate_deepl(text)
        print_result(args, text, result)
    elif args.src == 'all':
        print('---')
        result = translate_youdao(text)
        print_result(args, text, result)
        print('-')
        result = translate_deepl(text)
        print_result(args, text, result)
        print('---')
    else:
        print("Src Error")
        return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fast Translator')
    parser.add_argument('-c', "--copy", help="copy translate result to clipboard", action="store_true")
    parser.add_argument('-l', "--copy-last", help="copy last result to clipboard", action="store_true")
    parser.add_argument('-n', "--noti", help="show notification, need terminal-notifier and reattach-to-user-namespace",
                        action="store_true")
    parser.add_argument('-d', "--debug", help="debug mode", action="store_true")
    parser.add_argument('-v', "--verbose", help="verbose output", action="store_true")
    parser.add_argument('-s', "--say", help="say the result", action="store_true")
    parser.add_argument('-o', "--only-say", help="only say the word", action="store_true")
    parser.add_argument('-r', "--src", help="translate source", default="youdao", choices=["youdao", "deepl", "all"])
    parser.add_argument("text", help="translated words, empty to enter interactive mode", nargs='*')
    args = parser.parse_args()

    load_config(args)

    text = ' '.join(args.text)
    # print(text)

    if args.copy_last:
        copy_last_result(True)
    else:
        if len(text) != 0:
            translate(args, text)
        else:
            print('Enter text to translate, Ctrl-D to exit.\n')
            try:
                while True:
                    try:
                        text = raw_input()
                    except NameError:
                        text = input()
                    if text != '':
                        translate(args, text)
                        print()
                        # print('\n')
            except KeyboardInterrupt:
                pass
            except EOFError:
                pass
