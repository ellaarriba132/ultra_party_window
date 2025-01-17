# MIT License
#
# Copyright (c) 2022 Members of bombsquad-community organization, and contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

__author__ = ('Droopy', 'Pato')
__version__ = 5.1

# ba_meta require api 8
from baenv import TARGET_BALLISTICA_BUILD as build_number
import datetime
import json
import math
import os
import pickle
import random
import time
import urllib.request
import weakref
from threading import Thread
from typing import List, Tuple, Sequence, Optional, Dict, Any, cast
from hashlib import md5

import _babase
import babase
import _bascenev1
import _bauiv1
import bauiv1 as bui
import bascenev1 as bs
import bauiv1lib.party
from bauiv1lib.colorpicker import ColorPickerExact
from bauiv1lib.confirm import ConfirmWindow
from bauiv1lib.mainmenu import MainMenuWindow
from bauiv1lib.popup import PopupMenuWindow, PopupWindow, PopupMenu

_ip = '127.0.0.1'
_port = 43210
_ping = '-'
url = 'http://bombsquadprivatechat.ml'
last_msg = None

show_translate_result = True
config = babase.app.config
default_config = {'O Source Trans Lang': 'Auto Detect', 'O Target Trans Lang': babase.app.lang.default_language,
                  'Y Source Trans Lang': 'Auto Detect', 'Y Target Trans Lang': babase.app.lang.default_language}

for key in default_config:
    if not key in config:
        config[key] = default_config[key]

translate_languages = {'Auto Detect': 'auto', 'Arabic': 'ar', 'Chinese (simplified)': 'zh-CN', 'Chinese (traditional)': 'zh-TW', 'Croatian': 'hr', 'Czech': 'cs',
                       'Danish': 'da', 'Dutch': 'nl', 'English': 'en', 'Esperanto': 'eo',
                       'Finnish': 'fi',
                       'Tagalog': 'tl', 'French': 'fr', 'German': 'de', 'Greek': 'el',
                       'Hindi': 'hi', 'Hungarian': 'hu', 'Indonesian': 'id', 'Italian': 'it',
                       'Japanese': 'ja',
                       'Korean': 'ko', 'Malay': 'ms', 'Malayalam': 'ml', 'Marathi': 'mr', 'Persian': 'fa', 'Polish': 'pl',
                       'Portuguese': 'pt', 'Romanian': 'ro', 'Russian': 'ru', 'Serbian': 'sr',
                       'Slovak': 'sk', 'Spanish': 'es', 'Swedish': 'sv', 'Tamil': 'ta',
                       'Telugu': 'te',
                       'Thai': 'th', 'Turkish': 'tr', 'Ukrainian': 'uk', 'Vietnamese': 'vi'}
available_translate_languages = []
for lang in translate_languages:
    available_translate_languages.append(lang)
available_translate_languages.sort()
available_translate_languages.remove('Auto Detect')
available_translate_languages.insert(0, 'Auto Detect')

my_directory = _babase.env()['python_directory_user'] + '/UltraPartyWindowFiles/'
quick_msg_file = my_directory + 'QuickMessages.txt'
cookies_file = my_directory + 'cookies.txt'
saved_ids_file = my_directory + 'saved_ids.json'
my_location = my_directory

def translate(text, _callback, source='auto', target='en'):
    text = urllib.parse.quote(text)
    url = f'https://translate.google.com/m?tl={target}&sl={source}&q={text}'
    request = urllib.request.Request(url)
    data = urllib.request.urlopen(request).read().decode('utf-8')
    result = data[(data.find('"result-container">'))+len('"result-container">')
                   :data.find('</div><div class="links-container">')]
    replace_list = [('&#39;', '\''), ('&quot;', '"'), ('&amp;', '&')]
    for i in replace_list:
        result = result.replace(i[0], i[1])
    if show_translate_result:
        bui.pushcall(bui.Call(_callback, result), from_other_thread=True)

def initialize():
    config_defaults = {'Party Chat Muted': False,
                       'Chat Muted': False,
                       'ping button': True,
                       'IP button': True,
                       'copy button': True,
                       'Direct Send': False,
                       'Colorful Chat': True,
                       'Custom Commands': [],
                       'Message Notification': 'bottom',
                       'Self Status': 'online',
    #                    'Translate Source Language': 'arabic',
    #                    'Translate Destination Language': 'english',
                       'Pronunciation': True
                       }
    # config = bui.app.config
    # for key in config_defaults:
    #     if key not in config:
    #         config[key] = config_defaults[key]

    if not os.path.exists(my_directory):
        os.makedirs(my_directory)
    if not os.path.exists(cookies_file):
        with open(cookies_file, 'wb') as f:
            pickle.dump({}, f)
    if not os.path.exists(saved_ids_file):
        with open(saved_ids_file, 'w') as f:
            data = {}
            json.dump(data, f)


def display_error(msg=None):
    if msg:
        bs.broadcastmessage(msg, (1, 0, 0))
    else:
        bs.broadcastmessage('Failed!', (1, 0, 0))
    bui.getsound('error').play()


def display_success(msg=None):
    if msg:
        bs.broadcastmessage(msg, (0, 1, 0))
    else:
        bs.broadcastmessage('Successful!', (0, 1, 0))


# class Translate(Thread):
#     def __init__(self, data, callback):
#         super().__init__()
#         self.data = data
#         self._callback = callback

#     def run(self):
#         _babase.pushcall(bui.Call(bs.broadcastmessage, 'Nothing is going to happen u re a ediot...'), from_other_thread=True)
#         response = messenger._send_request(f'{url}/translate', self.data)
#         if response:
#             _babase.pushcall(bui.Call(self._callback, response), from_other_thread=True)


class ColorTracker:
    def __init__(self):
        self.saved = {}

    def _get_safe_color(self, sender):
        while True:
            color = (random.random(), random.random(), random.random())
            s = 0
            background = bui.app.config.get('PartyWindow Main Color', (0.5, 0.5, 0.5))
            for i, j in zip(color, background):
                s += (i - j) ** 2
            if s > 0.1:
                self.saved[sender] = color
                if len(self.saved) > 20:
                    self.saved.pop(list(self.saved.keys())[0])
                break
            time.sleep(0.1)

    def _get_sender_color(self, sender):
        if sender not in self.saved:
            self.thread = Thread(target=self._get_safe_color, args=(sender,))
            self.thread.start()
            return (1, 1, 1)
        else:
            return self.saved[sender]


class PrivateChatHandler:
    def __init__(self):
        self.pvt_msgs = {}
        self.login_id = None
        self.last_msg_id = None
        self.logged_in = False
        self.cookieProcessor = urllib.request.HTTPCookieProcessor()
        self.opener = urllib.request.build_opener(self.cookieProcessor)
        self.filter = 'all'
        self.pending_messages = []
        self.friends_status = {}
        self.error = ''
        Thread(target=self._ping).start()

    def _load_ids(self):
        with open(saved_ids_file, 'r') as f:
            saved = json.load(f)
            if self.myid in saved:
                self.saved_ids = saved[self.myid]
            else:
                self.saved_ids = {'all': '<all>'}

    def _dump_ids(self):
        with open(saved_ids_file, 'r') as f:
            saved = json.load(f)
        with open(saved_ids_file, 'w') as f:
            saved[self.myid] = self.saved_ids
            json.dump(saved, f)

    def _ping(self):
        self.server_online = False
        response = self._send_request(url=f'{url}')
        if not response:
            self.error = 'Server offline'
        elif response:
            try:
                self.server_online = True
                version = float(response.replace('v', ''))
            except:
                self.error = 'Server offline'

    def _signup(self, registration_key):
        data = dict(pb_id=self.myid, registration_key=registration_key)
        response = self._send_request(url=f'{url}/signup', data=data)
        if response:
            if response == 'successful':
                display_success('Account Created Successfully')
                self._login(registration_key=registration_key)
                return True
            display_error(response)

    def _save_cookie(self):
        with open(cookies_file, 'rb') as f:
            cookies = pickle.load(f)
        with open(cookies_file, 'wb') as f:
            for c in self.cookieProcessor.cookiejar:
                cookie = pickle.dumps(c)
                break
            cookies[self.myid] = cookie
            pickle.dump(cookies, f)

    def _cookie_login(self):
        self.myid = bui.app.plus.get_v1_account_misc_read_val_2('resolvedAccountID', '')
        try:
            with open(cookies_file, 'rb') as f:
                cookies = pickle.load(f)
        except:
            return False
        if self.myid in cookies:
            cookie = pickle.loads(cookies[self.myid])
            self.cookieProcessor.cookiejar.set_cookie(cookie)
            self.opener = urllib.request.build_opener(self.cookieProcessor)
            response = self._send_request(url=f'{url}/login')
            if response.startswith('logged in as'):
                self.logged_in = True
                self._load_ids()
                display_success(response)
                return True

    def _login(self, registration_key):
        self.myid = bui.app.plus.get_v1_account_misc_read_val_2('resolvedAccountID', '')
        data = dict(pb_id=self.myid, registration_key=registration_key)
        response = self._send_request(url=f'{url}/login', data=data)
        if response == 'successful':
            self.logged_in = True
            self._load_ids()
            self._save_cookie()
            display_success('Account Logged in Successfully')
            return True
        else:
            display_error(response)

    def _query(self, pb_id=None):
        if not pb_id:
            pb_id = self.myid
        response = self._send_request(url=f'{url}/query/{pb_id}')
        if response == 'exists':
            return True
        return False

    def _send_request(self, url, data=None):
        try:
            if not data:
                response = self.opener.open(url)
            else:
                response = self.opener.open(url, data=json.dumps(data).encode())
            if response.getcode() != 200:
                display_error(response.read().decode())
                return None
            else:
                return response.read().decode()
        except:
            return None

    def _save_id(self, account_id, nickname='<default>', verify=True):
        # display_success(f'Saving {account_id}. Please wait...')
        if verify:
            url = 'http://bombsquadgame.com/accountquery?id=' + account_id
            response = json.loads(urllib.request.urlopen(url).read().decode())
            if 'error' in response:
                display_error('Enter valid account id')
                return False
            self.saved_ids[account_id] = {}
            name = None
            if nickname == '<default>':
                name_html = response['name_html']
                name = name_html.split('>')[1]
            nick = name if name else nickname
        else:
            nick = nickname
        self.saved_ids[account_id] = nick
        self._dump_ids()
        display_success(f'Account added: {nick}({account_id})')
        return True

    def _remove_id(self, account_id):
        removed = self.saved_ids.pop(account_id)
        self._dump_ids()
        bs.broadcastmessage(f'Removed successfully: {removed}({account_id})', (0, 1, 0))
        bui.getsound('shieldDown').play()

    def _format_message(self, msg):
        filter = msg['filter']
        if filter in self.saved_ids:
            if self.filter == 'all':
                message = '[' + self.saved_ids[filter] + ']' + msg['message']
            else:
                message = msg['message']
        else:
            message = '[' + msg['filter'] + ']: ' + \
                'Message from unsaved id. Save id to view message.'
        return message

    def _get_status(self, id, type='status'):
        info = self.friends_status.get(id, {})
        if not info:
            return '-'
        if type == 'status':
            return info['status']
        else:
            last_seen = info["last_seen"]
            last_seen = _get_local_time(last_seen)
            bs.broadcastmessage(f'Last seen on: {last_seen}')


def _get_local_time(utctime):
    d = datetime.datetime.strptime(utctime, '%d-%m-%Y %H:%M:%S')
    d = d.replace(tzinfo=datetime.timezone.utc)
    d = d.astimezone()
    return d.strftime('%B %d,\t\t%H:%M:%S')


def update_status():
    if messenger.logged_in:
        if bui.app.config['Self Status'] == 'online':
            host = bs.get_connection_to_host_info_2()
            if host is not None and host.name != '':
                my_status = f'Playing in {host}'
            else:
                my_status = 'in Lobby'
            ids_to_check = [i for i in messenger.saved_ids if i != 'all']
            response = messenger._send_request(url=f'{url}/updatestatus',
                                               data=dict(self_status=my_status, ids=ids_to_check))
            if response:
                messenger.friends_status = json.loads(response)
        else:
            messenger.friends_status = {}


def messenger_thread():
    counter = 0
    while True:
        counter += 1
        time.sleep(0.6)
        check_new_message()
        if counter > 5:
            counter = 0
            update_status()


def check_new_message():
    if messenger.logged_in:
        if messenger.login_id != messenger.myid:
            response = messenger._send_request(f'{url}/first')
            if response:
                messenger.pvt_msgs = json.loads(response)
                if messenger.pvt_msgs['all']:
                    messenger.last_msg_id = messenger.pvt_msgs['all'][-1]['id']
                    messenger.login_id = messenger.myid
        else:
            response = messenger._send_request(f'{url}/new/{messenger.last_msg_id}')
            if response:
                new_msgs = json.loads(response)
                if new_msgs:
                    for msg in new_msgs['messages']:
                        if msg['id'] > messenger.last_msg_id:
                            messenger.last_msg_id = msg['id']
                            messenger.pvt_msgs['all'].append(
                                dict(id=msg['id'], filter=msg['filter'], message=msg['message'], sent=msg['sent']))
                            if len(messenger.pvt_msgs['all']) > 40:
                                messenger.pvt_msgs['all'].pop(0)
                            if msg['filter'] not in messenger.pvt_msgs:
                                messenger.pvt_msgs[msg['filter']] = [
                                    dict(id=msg['id'], filter=msg['filter'], message=msg['message'], sent=msg['sent'])]
                            else:
                                messenger.pvt_msgs[msg['filter']].append(
                                    dict(id=msg['id'], filter=msg['filter'], message=msg['message'], sent=msg['sent']))
                                if len(messenger.pvt_msgs[msg['filter']]) > 20:
                                    messenger.pvt_msgs[msg['filter']].pop(0)
                            messenger.pending_messages.append(
                                (messenger._format_message(msg), msg['filter'], msg['sent']))


def display_message(msg, msg_type, filter=None, sent=None):
    flag = None
    notification = bui.app.config['Message Notification']
    if babase.app.classic.party_window:
        if babase.app.classic.party_window():
            if babase.app.classic.party_window()._private_chat:
                flag = 1
                if msg_type == 'private':
                    if messenger.filter == filter or messenger.filter == 'all':
                        babase.app.classic.party_window().on_chat_message(msg, sent)
                    else:
                        if notification == 'top':
                            bs.broadcastmessage(msg, (1, 1, 0), True, coin)
                        else:
                            bs.broadcastmessage(msg, (1, 1, 0), False)
                else:
                    bs.broadcastmessage(msg, (0.2, 1.0, 1.0), True, tex)
            else:
                flag = 1
                if msg_type == 'private':
                    if notification == 'top':
                        bs.broadcastmessage(msg, (1, 1, 0), True, coin)
                    else:
                        bs.broadcastmessage(msg, (1, 1, 0), False)
    if not flag:
        if msg_type == 'private':
            if notification == 'top':
                bs.broadcastmessage(msg, (1, 1, 0), True, coin)
            else:
                bs.broadcastmessage(msg, (1, 1, 0), False)
        else:
            bs.broadcastmessage(msg, (0.2, 1.0, 1.0), True, tex)


def msg_displayer():
    for msg in messenger.pending_messages:
        display_message(msg[0], 'private', msg[1], msg[2])
        messenger.pending_messages.remove(msg)
    if bui.app.config.resolve('Chat Muted') and not bui.app.config['Party Chat Muted']:
        global last_msg
        last = bs.get_chat_messages()
        lm = last[-1] if last else None
        if lm != last_msg:
            last_msg = lm
            display_message(lm, 'public')


class SortQuickMessages:
    def __init__(self):
        uiscale = bui.app.ui_v1.uiscale
        bg_color = bui.app.config.get('PartyWindow Main Color', (0.5, 0.5, 0.5))
        self._width = 750 if uiscale is bui.UIScale.SMALL else 600
        self._height = (300 if uiscale is bui.UIScale.SMALL else
                        325 if uiscale is bui.UIScale.MEDIUM else 350)
        self._root_widget = bui.containerwidget(
            size=(self._width, self._height),
            transition='in_scale',
            on_outside_click_call=babase.Call(self._save),
            color=bg_color,
            parent=bui.get_special_widget('overlay_stack'),
            scale=(2 if uiscale is babase.UIScale.SMALL else
                    1.4 if uiscale is babase.UIScale.MEDIUM else 1.3),
            stack_offset=(0, -16) if uiscale is bui.UIScale.SMALL else (0, 0)
            )
        bui.textwidget(parent=self._root_widget,
                      position=(0, self._height - 50),
                      size=(self._width, 25),
                      text='Sort Quick Messages',
                      color=bui.app.ui_v1.title_color,
                      scale=1.05,
                      h_align='center',
                      v_align='center',
                      maxwidth=270)
        b_textcolor = (0.4, 0.75, 0.5)
        
        self.back_button = bui.buttonwidget(parent=self._root_widget,
                                     autoselect=True,
                                     position=(30, self._height - 60),
                                     size=(41, 41),
                                     color=bg_color,
                                     label='',
                                     on_activate_call=self._save,
                                     icon=bui.gettexture('crossOut'),
                                     iconscale=1.0)
        
        up_button = bui.buttonwidget(parent=self._root_widget,
                                      position=(10, 170),
                                      size=(60, 60),
                                      on_activate_call=self._move_up,
                                      label=babase.charstr(babase.SpecialChar.UP_ARROW),
                                      button_type='square',
                                      color=bg_color,
                                      textcolor=b_textcolor,
                                      autoselect=True,
                                      repeat=True)
        down_button = bui.buttonwidget(parent=self._root_widget,
                                      position=(10, 75),
                                      size=(60, 60),
                                      on_activate_call=self._move_down,
                                      label=babase.charstr(babase.SpecialChar.DOWN_ARROW),
                                      button_type='square',
                                      color=bg_color,
                                      textcolor=b_textcolor,
                                      autoselect=True,
                                      repeat=True)
        self._scroll_width = self._width - 150
        self._scroll_height = self._height - 110
        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            size=(self._scroll_width, self._scroll_height),
            color=bg_color,
            position=(100, 40))
        self._columnwidget = bui.columnwidget(
            parent=self._scrollwidget,
            border=2,
            margin=0)
        with open(quick_msg_file, 'r') as f:
            self.msgs = f.read().split('\n')
        self._msg_selected = None
        self._refresh()
        bui.containerwidget(edit=self._root_widget,
                           on_cancel_call=self._save)

    def _refresh(self):
        for child in self._columnwidget.get_children():
            child.delete()
        for msg in enumerate(self.msgs):
            txt = bui.textwidget(
                parent=self._columnwidget,
                size=(self._scroll_width - 10, 30),
                selectable=True,
                always_highlight=True,
                on_select_call=bui.Call(self._on_msg_select, msg),
                text=msg[1],
                h_align='left',
                v_align='center',
                maxwidth=self._scroll_width)
            if msg == self._msg_selected:
                bui.columnwidget(edit=self._columnwidget,
                                selected_child=txt,
                                visible_child=txt)

    def _on_msg_select(self, msg):
        self._msg_selected = msg

    def _move_up(self):
        index = self._msg_selected[0]
        msg = self._msg_selected[1]
        if index:
            self.msgs.insert((index - 1), self.msgs.pop(index))
            self._msg_selected = (index - 1, msg)
            self._refresh()

    def _move_down(self):
        index = self._msg_selected[0]
        msg = self._msg_selected[1]
        if index + 1 < len(self.msgs):
            self.msgs.insert((index + 1), self.msgs.pop(index))
            self._msg_selected = (index + 1, msg)
            self._refresh()

    def _save(self) -> None:
        try:
            with open(quick_msg_file, 'w') as f:
                f.write('\n'.join(self.msgs))
        except:
            babase.print_exception()
            bs.broadcastmessage('Error!', (1, 0, 0))
        bui.containerwidget(
            edit=self._root_widget,
            transition='out_right', cancel_button=self.back_button)
        bui.getsound('swish').play()


class TranslationSettings:
    def __init__(self):
        uiscale = bui.app.ui_v1.uiscale
        height = (300 if uiscale is bui.UIScale.SMALL else
                  350 if uiscale is bui.UIScale.MEDIUM else 400)
        width = (500 if uiscale is bui.UIScale.SMALL else
                 600 if uiscale is bui.UIScale.MEDIUM else 650)
        self._transition_out: Optional[str]
        scale_origin: Optional[Tuple[float, float]]
        self._transition_out = 'out_scale'
        scale_origin = 10
        transition = 'in_scale'
        scale_origin = None
        cancel_is_selected = False
        cfg = bui.app.config
        bg_color = cfg.get('PartyWindow Main Color', (0.5, 0.5, 0.5))

        LANGUAGES = {
            '': 'Auto-Detect',
            'af': 'afrikaans',
            'sq': 'albanian',
            'am': 'amharic',
            'ar': 'arabic',
            'hy': 'armenian',
            'az': 'azerbaijani',
            'eu': 'basque',
            'be': 'belarusian',
            'bn': 'bengali',
            'bs': 'bosnian',
            'bg': 'bulgarian',
            'ca': 'catalan',
            'ceb': 'cebuano',
            'ny': 'chichewa',
            'zh-cn': 'chinese (simplified)',
            'zh-tw': 'chinese (traditional)',
            'co': 'corsican',
            'hr': 'croatian',
            'cs': 'czech',
            'da': 'danish',
            'nl': 'dutch',
            'en': 'english',
            'eo': 'esperanto',
            'et': 'estonian',
            'tl': 'filipino',
            'fi': 'finnish',
            'fr': 'french',
            'fy': 'frisian',
            'gl': 'galician',
            'ka': 'georgian',
            'de': 'german',
            'el': 'greek',
            'gu': 'gujarati',
            'ht': 'haitian creole',
            'ha': 'hausa',
            'haw': 'hawaiian',
            'iw': 'hebrew',
            'he': 'hebrew',
            'hi': 'hindi',
            'hmn': 'hmong',
            'hu': 'hungarian',
            'is': 'icelandic',
            'ig': 'igbo',
            'id': 'indonesian',
            'ga': 'irish',
            'it': 'italian',
            'ja': 'japanese',
            'jw': 'javanese',
            'kn': 'kannada',
            'kk': 'kazakh',
            'km': 'khmer',
            'ko': 'korean',
            'ku': 'kurdish (kurmanji)',
            'ky': 'kyrgyz',
            'lo': 'lao',
            'la': 'latin',
            'lv': 'latvian',
            'lt': 'lithuanian',
            'lb': 'luxembourgish',
            'mk': 'macedonian',
            'mg': 'malagasy',
            'ms': 'malay',
            'ml': 'malayalam',
            'mt': 'maltese',
            'mi': 'maori',
            'mr': 'marathi',
            'mn': 'mongolian',
            'my': 'myanmar (burmese)',
            'ne': 'nepali',
            'no': 'norwegian',
            'or': 'odia',
            'ps': 'pashto',
            'fa': 'persian',
            'pl': 'polish',
            'pt': 'portuguese',
            'pa': 'punjabi',
            'ro': 'romanian',
            'ru': 'russian',
            'sm': 'samoan',
            'gd': 'scots gaelic',
            'sr': 'serbian',
            'st': 'sesotho',
            'sn': 'shona',
            'sd': 'sindhi',
            'si': 'sinhala',
            'sk': 'slovak',
            'sl': 'slovenian',
            'so': 'somali',
            'es': 'spanish',
            'su': 'sundanese',
            'sw': 'swahili',
            'sv': 'swedish',
            'tg': 'tajik',
            'ta': 'tamil',
            'te': 'telugu',
            'th': 'thai',
            'tr': 'turkish',
            'uk': 'ukrainian',
            'ur': 'urdu',
            'ug': 'uyghur',
            'uz': 'uzbek',
            'vi': 'vietnamese',
            'cy': 'welsh',
            'xh': 'xhosa',
            'yi': 'yiddish',
            'yo': 'yoruba',
            'zu': 'zulu'}

        self.root_widget = bui.containerwidget(
            size=(width, height),
            color=bg_color,
            transition=transition,
            toolbar_visibility='menu_minimal_no_back',
            parent=bui.get_special_widget('overlay_stack'),
            on_outside_click_call=self._cancel,
            scale=(2.1 if uiscale is bui.UIScale.SMALL else
                   1.5 if uiscale is bui.UIScale.MEDIUM else 1.0),
            scale_origin_stack_offset=scale_origin)
        bui.textwidget(parent=self.root_widget,
                      position=(width * 0.5, height - 45),
                      size=(20, 20),
                      h_align='center',
                      v_align='center',
                      text="Text Translation",
                      scale=0.9,
                      color=(5, 5, 5))
        cbtn = btn = bui.buttonwidget(parent=self.root_widget,
                                     autoselect=True,
                                     position=(30, height - 60),
                                     size=(30, 30),
                                     label=babase.charstr(babase.SpecialChar.BACK),
                                     button_type='backSmall',
                                     on_activate_call=self._cancel)

        source_lang_text = bui.textwidget(parent=self.root_widget,
                                         position=(40, height - 110),
                                         size=(20, 20),
                                         h_align='left',
                                         v_align='center',
                                         text="Source Language : ",
                                         scale=0.9,
                                         color=(1, 1, 1))

        # source_lang_menu = PopupMenu(
        #     parent=self.root_widget,
        #     position=(330 if uiscale is bui.UIScale.SMALL else 400, height - 115),
        #     width=200,
        #     scale=(2.8 if uiscale is bui.UIScale.SMALL else
        #            1.8 if uiscale is bui.UIScale.MEDIUM else 1.2),
        #     current_choice=cfg['Translate Source Language'],
        #     choices=LANGUAGES.keys(),
        #     choices_display=(bui.Lstr(value=i) for i in LANGUAGES.values()),
        #     button_size=(130, 35),
        #     on_value_change_call=self._change_source)

        destination_lang_text = bui.textwidget(parent=self.root_widget,
                                              position=(40, height - 165),
                                              size=(20, 20),
                                              h_align='left',
                                              v_align='center',
                                              text="Destination Language : ",
                                              scale=0.9,
                                              color=(1, 1, 1))

        destination_lang_menu = PopupMenu(
            parent=self.root_widget,
            position=(330 if uiscale is bui.UIScale.SMALL else 400, height - 170),
            width=200,
            scale=(2.8 if uiscale is bui.UIScale.SMALL else
                   1.8 if uiscale is bui.UIScale.MEDIUM else 1.2),
            current_choice=cfg['Translate Destination Language'],
            choices=list(LANGUAGES.keys())[1:],
            choices_display=list(bui.Lstr(value=i) for i in LANGUAGES.values())[1:],
            button_size=(130, 35),
            on_value_change_call=self._change_destination)

        bui.containerwidget(edit=self.root_widget, cancel_button=btn)

    # def _change_source(self, choice):
    #     cfg = bui.app.config
    #     cfg['Translate Source Language'] = choice
    #     cfg.apply_and_commit()

    def _change_destination(self, choice):
        cfg = bui.app.config
        cfg['Translate Destination Language'] = choice
        cfg.apply_and_commit()

    def _actions_changed(self, v: str) -> None:
        cfg = bui.app.config
        cfg['Pronunciation'] = v
        cfg.apply_and_commit()

    def _cancel(self) -> None:
        bui.containerwidget(edit=self.root_widget, transition='out_scale')
        SettingsWindow()


class SettingsWindow:

    def __init__(self):
        uiscale = bui.app.ui_v1.uiscale
        height = (300 if uiscale is bui.UIScale.SMALL else
                  350 if uiscale is bui.UIScale.MEDIUM else 400)
        width = (500 if uiscale is bui.UIScale.SMALL else
                 600 if uiscale is bui.UIScale.MEDIUM else 650)
        scroll_h = (200 if uiscale is bui.UIScale.SMALL else
                    250 if uiscale is bui.UIScale.MEDIUM else 270)
        scroll_w = (450 if uiscale is bui.UIScale.SMALL else
                    550 if uiscale is bui.UIScale.MEDIUM else 600)
        self._transition_out: Optional[str]
        scale_origin: Optional[Tuple[float, float]]
        self._transition_out = 'out_scale'
        scale_origin = 10
        transition = 'in_scale'
        scale_origin = None
        cancel_is_selected = False
        cfg = bui.app.config
        bg_color = cfg.get('PartyWindow Main Color', (0.5, 0.5, 0.5))

        self.root_widget = bui.containerwidget(
            size=(width, height),
            color=bg_color,
            transition=transition,
            toolbar_visibility='menu_minimal_no_back',
            parent=bui.get_special_widget('overlay_stack'),
            on_outside_click_call=self._cancel,
            scale=(2.1 if uiscale is bui.UIScale.SMALL else
                   1.5 if uiscale is bui.UIScale.MEDIUM else 1.0),
            scale_origin_stack_offset=scale_origin)
        bui.textwidget(parent=self.root_widget,
                      position=(width * 0.5, height - 45),
                      size=(20, 20),
                      h_align='center',
                      v_align='center',
                      text="Custom Settings",
                      scale=0.9,
                      color=(5, 5, 5))
        cbtn = btn = bui.buttonwidget(parent=self.root_widget,
                                     autoselect=True,
                                     position=(30, height - 60),
                                     size=(30, 30),
                                     label=babase.charstr(babase.SpecialChar.BACK),
                                     button_type='backSmall',
                                     on_activate_call=self._cancel)
        scroll_position = (30 if uiscale is bui.UIScale.SMALL else
                           40 if uiscale is bui.UIScale.MEDIUM else 50)
        self._scrollwidget = bui.scrollwidget(parent=self.root_widget,
                                             position=(30, scroll_position),
                                             simple_culling_v=20.0,
                                             highlight=False,
                                             size=(scroll_w, scroll_h),
                                             selection_loops_to_parent=True)
        bui.widget(edit=self._scrollwidget, right_widget=self._scrollwidget)
        self._subcontainer = bui.columnwidget(parent=self._scrollwidget,
                                             selection_loops_to_parent=True)
        ip_button = bui.checkboxwidget(
            parent=self._subcontainer,
            size=(300, 30),
            maxwidth=300,
            textcolor=((0, 1, 0) if cfg['IP button'] else (0.95, 0.65, 0)),
            scale=1,
            value=cfg['IP button'],
            autoselect=True,
            text="IP Button",
            on_value_change_call=self.ip_button)
        ping_button = bui.checkboxwidget(
            parent=self._subcontainer,
            size=(300, 30),
            maxwidth=300,
            textcolor=((0, 1, 0) if cfg['ping button'] else (0.95, 0.65, 0)),
            scale=1,
            value=cfg['ping button'],
            autoselect=True,
            text="Ping Button",
            on_value_change_call=self.ping_button)
        copy_button = bui.checkboxwidget(
            parent=self._subcontainer,
            size=(300, 30),
            maxwidth=300,
            textcolor=((0, 1, 0) if cfg['copy button'] else (0.95, 0.65, 0)),
            scale=1,
            value=cfg['copy button'],
            autoselect=True,
            text="Copy Text Button",
            on_value_change_call=self.copy_button)
        direct_send = bui.checkboxwidget(
            parent=self._subcontainer,
            size=(300, 30),
            maxwidth=300,
            textcolor=((0, 1, 0) if cfg['Direct Send'] else (0.95, 0.65, 0)),
            scale=1,
            value=cfg['Direct Send'],
            autoselect=True,
            text="Directly Send Custom Commands",
            on_value_change_call=self.direct_send)
        colorfulchat = bui.checkboxwidget(
            parent=self._subcontainer,
            size=(300, 30),
            maxwidth=300,
            textcolor=((0, 1, 0) if cfg['Colorful Chat'] else (0.95, 0.65, 0)),
            scale=1,
            value=cfg['Colorful Chat'],
            autoselect=True,
            text="Colorful Chat",
            on_value_change_call=self.colorful_chat)
        msg_notification_text = bui.textwidget(parent=self._subcontainer,
                                              scale=0.8,
                                              color=(1, 1, 1),
                                              text='Message Notifcation:',
                                              size=(100, 30),
                                              h_align='left',
                                              v_align='center')
        msg_notification_widget = PopupMenu(
            parent=self._subcontainer,
            position=(100, height - 1200),
            width=200,
            scale=(2.8 if uiscale is bui.UIScale.SMALL else
                   1.8 if uiscale is bui.UIScale.MEDIUM else 1.2),
            choices=['top', 'bottom'],
            current_choice=bui.app.config['Message Notification'],
            button_size=(80, 25),
            on_value_change_call=self._change_notification)
        self_status_text = bui.textwidget(parent=self._subcontainer,
                                         scale=0.8,
                                         color=(1, 1, 1),
                                         text='Self Status:',
                                         size=(100, 30),
                                         h_align='left',
                                         v_align='center')
        self_status_widget = PopupMenu(
            parent=self._subcontainer,
            position=(50, height - 1000),
            width=200,
            scale=(2.8 if uiscale is bui.UIScale.SMALL else
                   1.8 if uiscale is bui.UIScale.MEDIUM else 1.2),
            choices=['online', 'offline'],
            current_choice=bui.app.config['Self Status'],
            button_size=(80, 25),
            on_value_change_call=self._change_status)
        bui.containerwidget(edit=self.root_widget, cancel_button=btn)
        bui.containerwidget(edit=self.root_widget,
                           selected_child=(cbtn if cbtn is not None
                                           and cancel_is_selected else None),
                           start_button=None)

        self._translation_btn = bui.buttonwidget(parent=self._subcontainer,
                                                scale=1.2,
                                                position=(100, 1200),
                                                size=(150, 50),
                                                label='Translate Settings',
                                                on_activate_call=self._translaton_btn,
                                                autoselect=True)

    def ip_button(self, value: bool):
        cfg = bui.app.config
        cfg['IP button'] = value
        cfg.apply_and_commit()
        if cfg['IP button']:
            bs.broadcastmessage("IP Button is now enabled", color=(0, 1, 0))
        else:
            bs.broadcastmessage("IP Button is now disabled", color=(1, 0.7, 0))

    def ping_button(self, value: bool):
        cfg = bui.app.config
        cfg['ping button'] = value
        cfg.apply_and_commit()
        if cfg['ping button']:
            bs.broadcastmessage("Ping Button is now enabled", color=(0, 1, 0))
        else:
            bs.broadcastmessage("Ping Button is now disabled", color=(1, 0.7, 0))

    def copy_button(self, value: bool):
        cfg = bui.app.config
        cfg['copy button'] = value
        cfg.apply_and_commit()
        if cfg['copy button']:
            bs.broadcastmessage("Copy Text Button is now enabled", color=(0, 1, 0))
        else:
            bs.broadcastmessage("Copy Text Button is now disabled", color=(1, 0.7, 0))

    def direct_send(self, value: bool):
        cfg = bui.app.config
        cfg['Direct Send'] = value
        cfg.apply_and_commit()

    def colorful_chat(self, value: bool):
        cfg = bui.app.config
        cfg['Colorful Chat'] = value
        cfg.apply_and_commit()

    def _change_notification(self, choice):
        cfg = bui.app.config
        cfg['Message Notification'] = choice
        cfg.apply_and_commit()

    def _change_status(self, choice):
        cfg = bui.app.config
        cfg['Self Status'] = choice
        cfg.apply_and_commit()

    def _translaton_btn(self):
        try:
            bui.containerwidget(edit=self.root_widget, transition='out_scale')
            TranslateWindow()
        except Exception as e:
            print(e)
            pass

    def _cancel(self) -> None:
        bui.containerwidget(edit=self.root_widget, transition='out_scale')


class PartyWindow(bauiv1lib.party.PartyWindow):
    """Party list/chat window."""

    def __del__(self) -> None:
        bui.set_party_window_open(False)

    def __init__(self, origin: Sequence[float] = (0, 0)):
        self._private_chat = False
        self._firstcall = True
        self.ping_server()
        bui.set_party_window_open(True)
        self._r = 'partyWindow'
        self._popup_type: Optional[str] = None
        self._popup_party_member_client_id: Optional[int] = None
        self._last_msg_clicked: str = None
        self._last_time_pressed_msg: float = 0.0
        self._last_time_pressed_translate: float = 0.0
        self._double_press_interval: float = 0.3
        self._popup_party_member_is_host: Optional[bool] = None
        self._width = 500
        uiscale = bui.app.ui_v1.uiscale
        self._height = (365 if uiscale is bui.UIScale.SMALL else
                        480 if uiscale is bui.UIScale.MEDIUM else 600)
        self.bg_color = bui.app.config.get('PartyWindow Main Color', (0.5, 0.5, 0.5))
        self.ping_timer = bui.AppTimer(5, bui.WeakCall(self.ping_server), repeat=True)
        self._display_old_msgs = True

        bui.Window.__init__(self, root_widget=bui.containerwidget(
            size=(self._width, self._height),
            transition='in_scale',
            color=self.bg_color,
            parent=bui.get_special_widget('overlay_stack'),
            on_outside_click_call=self.close_with_sound,
            scale_origin_stack_offset=origin,
            scale=(2.0 if uiscale is bui.UIScale.SMALL else
                   1.35 if uiscale is bui.UIScale.MEDIUM else 1.0),
            stack_offset=(0, -10) if uiscale is babase.UIScale.SMALL else (
                240, 0) if uiscale is bui.UIScale.MEDIUM else (330, 20)))

        self._cancel_button = bui.buttonwidget(parent=self._root_widget,
                                              scale=0.7,
                                              position=(30, self._height - 47),
                                              size=(50, 50),
                                              label='',
                                              on_activate_call=self.close,
                                              autoselect=True,
                                              color=self.bg_color,
                                              icon=bui.gettexture('crossOut'),
                                              iconscale=1.2)
        bui.containerwidget(edit=self._root_widget,
                           cancel_button=self._cancel_button)

        self._menu_button = bui.buttonwidget(
            parent=self._root_widget,
            scale=0.7,
            position=(self._width - 80, self._height - 47),
            size=(50, 50),
            label='...',
            autoselect=True,
            button_type='square',
            on_activate_call=bs.WeakCall(self._on_menu_button_press),
            color=self.bg_color,
            iconscale=1.2)

        info = bs.get_connection_to_host_info_2()
        if info is not None and info.name != '':
            self.title = bui.Lstr(value=info.name)
        else:
            self.title = bui.Lstr(resource=self._r + '.titleText')

        self._title_text = bui.textwidget(parent=self._root_widget,
                                         scale=0.9,
                                         color=(0.5, 0.7, 0.5),
                                         text=self.title,
                                         size=(0, 0),
                                         position=(self._width * 0.47,
                                                   self._height - 29),
                                         maxwidth=self._width * 0.6,
                                         h_align='center',
                                         v_align='center')
        self._empty_str = bui.textwidget(parent=self._root_widget,
                                        scale=0.75,
                                        size=(0, 0),
                                        position=(self._width * 0.5,
                                                  self._height - 65),
                                        maxwidth=self._width * 0.85,
                                        h_align='center',
                                        v_align='center')

        self._scroll_width = self._width - 50
        self._scrollwidget = bui.scrollwidget(parent=self._root_widget,
                                             size=(self._scroll_width,
                                                   self._height - 200),
                                             position=(30, 80),
                                             color=self.bg_color)
        self._columnwidget = bui.columnwidget(parent=self._scrollwidget,
                                             border=2,
                                             margin=0)
        bui.widget(edit=self._menu_button, down_widget=self._columnwidget)

        self._muted_text = bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.5),
            size=(0, 0),
            h_align='center',
            v_align='center',
            text=bui.Lstr(resource='chatMutedText'))

        self._text_field = txt = bui.textwidget(
            parent=self._root_widget,
            editable=True,
            size=(500, 40),
            position=(54, 39),
            text='',
            maxwidth=494,
            shadow=0.3,
            flatness=1.0,
            description=bui.Lstr(resource=self._r + '.chatMessageText'),
            autoselect=True,
            v_align='center',
            corner_scale=0.7)

        bui.widget(edit=self._scrollwidget,
                  autoselect=True,
                  left_widget=self._cancel_button,
                  up_widget=self._cancel_button,
                  down_widget=self._text_field)
        bui.widget(edit=self._columnwidget,
                  autoselect=True,
                  up_widget=self._cancel_button,
                  down_widget=self._text_field)
        bui.containerwidget(edit=self._root_widget, selected_child=txt)
        self._send_button = btn = bui.buttonwidget(parent=self._root_widget,
                                                  size=(50, 35),
                                                  label=bui.Lstr(resource=self._r + '.sendText'),
                                                  button_type='square',
                                                  autoselect=True,
                                                  color=self.bg_color,
                                                  position=(self._width - 90, 35),
                                                  on_activate_call=self._send_chat_message)
        bui.textwidget(edit=txt, on_return_press_call=btn.activate)
        self._previous_button = bui.buttonwidget(parent=self._root_widget,
                                                size=(30, 30),
                                                label=babase.charstr(babase.SpecialChar.UP_ARROW),
                                                button_type='square',
                                                autoselect=True,
                                                position=(15, 57),
                                                color=self.bg_color,
                                                scale=0.75,
                                                on_activate_call=self._previous_message)
        self._next_button = bui.buttonwidget(parent=self._root_widget,
                                            size=(30, 30),
                                            label=babase.charstr(babase.SpecialChar.DOWN_ARROW),
                                            button_type='square',
                                            autoselect=True,
                                            color=self.bg_color,
                                            scale=0.75,
                                            position=(15, 28),
                                            on_activate_call=self._next_message)
        self._translate_button = bui.buttonwidget(
                                           parent=self._root_widget,
                                           size=(35, 34),
                                           label="Trans",
                                           button_type='square',
                                           color=self.bg_color,
                                           autoselect=True,
                                           position=(self._width - 28, 35),
                                           on_activate_call=self._translate_your_chat)
        if bui.app.config['copy button']:
            self._copy_button = bui.buttonwidget(parent=self._root_widget,
                                                size=(15, 15),
                                                label='©',
                                                button_type='backSmall',
                                                autoselect=True,
                                                color=self.bg_color,
                                                position=(self._width - 40, 80),
                                                on_activate_call=self._copy_to_clipboard)
        self._ping_button = None
        if info is not None and info.name != '':
            if bui.app.config['ping button']:
                self._ping_button = bui.buttonwidget(
                    parent=self._root_widget,
                    scale=0.7,
                    position=(self._width - 538, self._height - 57),
                    size=(75, 75),
                    autoselect=True,
                    button_type='square',
                    label=f'{_ping}',
                    on_activate_call=self._send_ping,
                    color=self.bg_color,
                    text_scale=2.3,
                    iconscale=1.2)
            if bui.app.config['IP button']:
                self._ip_port_button = bui.buttonwidget(parent=self._root_widget,
                                                       size=(30, 30),
                                                       label='IP',
                                                       button_type='square',
                                                       autoselect=True,
                                                       color=self.bg_color,
                                                       position=(self._width - 530,
                                                                 self._height - 100),
                                                       on_activate_call=self._ip_port_msg)
        self._settings_button = bui.buttonwidget(parent=self._root_widget,
                                                size=(50, 50),
                                                scale=0.5,
                                                button_type='square',
                                                autoselect=True,
                                                color=self.bg_color,
                                                position=(self._width - 40, self._height - 47),
                                                on_activate_call=self._on_setting_button_press,
                                                icon=bui.gettexture('settingsIcon'),
                                                iconscale=1.2)
        self._privatechat_button = bui.buttonwidget(parent=self._root_widget,
                                                   size=(50, 50),
                                                   scale=0.5,
                                                   button_type='square',
                                                   autoselect=True,
                                                   color=self.bg_color,
                                                   position=(self._width - 40, self._height - 80),
                                                   on_activate_call=self._on_privatechat_button_press,
                                                   icon=bui.gettexture('ouyaOButton'),
                                                   iconscale=1.2)
        self._name_widgets: List[bui.Widget] = []
        self._roster: Optional[List[Dict[str, Any]]] = None
        self._update_timer = bui.AppTimer(1.0,
                                      bui.WeakCall(self._update),
                                      repeat=True,
        )
        self._update()

    def _translate_your_chat(self):
        def _apply_translation(translated):
            if self._text_field.exists():
                bui.textwidget(edit=self._text_field, text=translated)
        msg = bui.textwidget(query=self._text_field)
        if msg == '':
            bs.broadcastmessage('Nothing to translate.', (1, 0, 0))
            bui.getsound('error').play()
        else:
            _babase.pushcall(babase.Call(bs.broadcastmessage, 'Translating...'))
            translated = Thread(target=translate, args=(str(bui.textwidget(query=self._text_field)),
                                                              _apply_translation,
                                                              translate_languages[config['Y Source Trans Lang']],
                                                              translate_languages[config['Y Target Trans Lang']])).start()
            show_translate_result = True
            self._last_time_pressed_translate = babase.apptime()

    
    def on_chat_message(self, msg: str, sent=None) -> None:
        """Called when a new chat message comes through."""
        if bui.app.config['Party Chat Muted'] and not babase.app.classic.party_window()._private_chat:
            return
        if sent:
            self._add_msg(msg, sent)
        else:
            self._add_msg(msg)

    def _add_msg(self, msg: str, sent=None) -> None:
        if bui.app.config['Colorful Chat']:
            sender = msg.split(': ')[0]
            color = color_tracker._get_sender_color(sender) if sender else (1, 1, 1)
        else:
            color = (1, 1, 1)
        
        maxwidth = self._scroll_width * 0.94
        txt = bui.textwidget(parent=self._columnwidget,
                            text=msg,
                            h_align='left',
                            v_align='center',
                            size=(0, 13),
                            scale=0.55,
                            color=color,
                            maxwidth=maxwidth,
                            shadow=0.3,
                            flatness=1.0
        )
        if sent:
            bui.textwidget(edit=txt, size=(100, 15),
                          selectable=True,
                          click_activate=True,
                          on_activate_call=bui.Call(bs.broadcastmessage, f'Message sent: {_get_local_time(sent)}'))
        
        self._chat_texts.append(txt)
        if len(self._chat_texts) > 40:
            self._chat_texts.pop(0).delete()
        bui.containerwidget(edit=self._columnwidget, visible_child=txt)
 
    def _on_menu_button_press(self) -> None:
        is_muted = bui.app.config.resolve('Chat Muted')
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale

        choices = ['muteOption', 'modifyColor', 'add_to_favorites', 'addQuickReply', 'removeQuickReply', 'credits']
        choices_display = ['Mute Option', 'Modify Main Color', 'Add Server as Favorite',
                           'Add as Quick Reply', 'Remove a Quick Reply', 'Credits']

        if hasattr(bs.get_foreground_host_activity(), '_map'):
            choices.append('manualCamera')
            choices_display.append('Manual Camera')

        PopupMenuWindow(
            position=self._menu_button.get_screen_space_center(),
            color=self.bg_color,
            scale=(2.3 if uiscale is bui.UIScale.SMALL else
                   1.65 if uiscale is bui.UIScale.MEDIUM else 1.23),
            choices=choices,
            choices_display=self._create_baLstr_list(choices_display),
            current_choice='unmute' if is_muted else 'mute',
            delegate=self)
        self._popup_type = 'menu'

    def _update(self) -> None:
        if not self._private_chat:
            bui.set_party_window_open(True)
            bui.textwidget(edit=self._title_text, text=self.title)
            if self._firstcall:
                if hasattr(self, '_status_text'):
                    self._status_text.delete()
                self._roster = []
                self._firstcall = False
                self._chat_texts: List[bui.Widget] = []
                if not bui.app.config['Party Chat Muted']:
                    msgs = bs.get_chat_messages()
                    for msg in msgs:
                        self._add_msg(msg)
            # update muted state
            if bui.app.config['Party Chat Muted']:
                bui.textwidget(edit=self._muted_text, color=(1, 1, 1, 0.3))
                # clear any chat texts we're showing
                if self._chat_texts:
                    while self._chat_texts:
                        first = self._chat_texts.pop()
                        first.delete()
            else:
                bui.textwidget(edit=self._muted_text, color=(1, 1, 1, 0.0))
            if self._ping_button:
                bui.buttonwidget(edit=self._ping_button,
                                label=f'{_ping}',
                                textcolor=self._get_ping_color())

            # update roster section
            roster = bs.get_game_roster()
            if roster != self._roster or self._firstcall:

                self._roster = roster

                # clear out old
                for widget in self._name_widgets:
                    widget.delete()
                self._name_widgets = []
                if not self._roster:
                    top_section_height = 60
                    bui.textwidget(edit=self._empty_str,
                                  text=bui.Lstr(resource=self._r + '.emptyText'))
                    bui.scrollwidget(edit=self._scrollwidget,
                                    size=(self._width - 50,
                                          self._height - top_section_height - 110),
                                    position=(30, 80))
                else:
                    columns = 1 if len(
                        self._roster) == 1 else 2 if len(self._roster) == 2 else 3
                    rows = int(math.ceil(float(len(self._roster)) / columns))
                    c_width = (self._width * 0.9) / max(3, columns)
                    c_width_total = c_width * columns
                    c_height = 24
                    c_height_total = c_height * rows
                    for y in range(rows):
                        for x in range(columns):
                            index = y * columns + x
                            if index < len(self._roster):
                                t_scale = 0.65
                                pos = (self._width * 0.53 - c_width_total * 0.5 +
                                       c_width * x - 23,
                                       self._height - 65 - c_height * y - 15)

                                # if there are players present for this client, use
                                # their names as a display string instead of the
                                # client spec-string
                                try:
                                    if self._roster[index]['players']:
                                        # if there's just one, use the full name;
                                        # otherwise combine short names
                                        if len(self._roster[index]
                                               ['players']) == 1:
                                            p_str = self._roster[index]['players'][
                                                0]['name_full']
                                        else:
                                            p_str = ('/'.join([
                                                entry['name'] for entry in
                                                self._roster[index]['players']
                                            ]))
                                            if len(p_str) > 25:
                                                p_str = p_str[:25] + '...'
                                    else:
                                        p_str = self._roster[index][
                                            'display_string']
                                except Exception:
                                    babase.print_exception(
                                        'Error calcing client name str.')
                                    p_str = '???'
                                widget = bui.textwidget(parent=self._root_widget,
                                                       position=(pos[0], pos[1]),
                                                       scale=t_scale,
                                                       size=(c_width * 0.85, 30),
                                                       maxwidth=c_width * 0.85,
                                                       color=(1, 1,
                                                              1) if index == 0 else
                                                       (1, 1, 1),
                                                       selectable=True,
                                                       autoselect=True,
                                                       click_activate=True,
                                                       text=bui.Lstr(value=p_str),
                                                       h_align='left',
                                                       v_align='center')
                                self._name_widgets.append(widget)

                                # in newer versions client_id will be present and
                                # we can use that to determine who the host is.
                                # in older versions we assume the first client is
                                # host
                                if self._roster[index]['client_id'] is not None:
                                    is_host = self._roster[index][
                                        'client_id'] == -1
                                else:
                                    is_host = (index == 0)

                                # FIXME: Should pass client_id to these sort of
                                #  calls; not spec-string (perhaps should wait till
                                #  client_id is more readily available though).
                                bui.textwidget(edit=widget,
                                              on_activate_call=bui.Call(
                                                  self._on_party_member_press,
                                                  self._roster[index]['client_id'],
                                                  is_host, widget))
                                pos = (self._width * 0.53 - c_width_total * 0.5 +
                                       c_width * x,
                                       self._height - 65 - c_height * y)

                                # Make the assumption that the first roster
                                # entry is the server.
                                # FIXME: Shouldn't do this.
                                if is_host:
                                    twd = min(
                                        c_width * 0.85,
                                        _babase.get_string_width(
                                            p_str, suppress_warning=True) *
                                        t_scale)
                                    self._name_widgets.append(
                                        bui.textwidget(
                                            parent=self._root_widget,
                                            position=(pos[0] + twd + 1,
                                                      pos[1] - 0.5),
                                            size=(0, 0),
                                            h_align='left',
                                            v_align='center',
                                            maxwidth=c_width * 0.96 - twd,
                                            color=(0.1, 1, 0.1, 0.5),
                                            text=bui.Lstr(resource=self._r +
                                                         '.hostText'),
                                            scale=0.4,
                                            shadow=0.1,
                                            flatness=1.0))
                    bui.textwidget(edit=self._empty_str, text='')
                    bui.scrollwidget(edit=self._scrollwidget,
                                    size=(self._width - 50,
                                          max(100, self._height - 139 -
                                              c_height_total)),
                                    position=(30, 80))
        else:
            bui.set_party_window_open(False)
            for widget in self._name_widgets:
                widget.delete()
            self._name_widgets = []
            bui.textwidget(edit=self._title_text, text='Private Chat')
            bui.textwidget(edit=self._empty_str, text='')
            if self._firstcall:
                self._firstcall = False
                if hasattr(self, '_status_text'):
                    self._status_text.delete()
                try:
                    msgs = messenger.pvt_msgs[messenger.filter]
                except:
                    msgs = []
                if self._chat_texts:
                    while self._chat_texts:
                        first = self._chat_texts.pop()
                        first.delete()
                uiscale = bui.app.ui_v1.uiscale
                scroll_height = (165 if uiscale is bui.UIScale.SMALL else
                                 280 if uiscale is bui.UIScale.MEDIUM else 400)
                bui.scrollwidget(edit=self._scrollwidget,
                                size=(self._width - 50, scroll_height))
                for msg in msgs:
                    message = messenger._format_message(msg)
                    self._add_msg(message, msg['sent'])
                self._filter_text = bui.textwidget(parent=self._root_widget,
                                                  scale=0.6,
                                                  color=(0.9, 1.0, 0.9),
                                                  text='Filter: ',
                                                  size=(0, 0),
                                                  position=(self._width * 0.3,
                                                            self._height - 70),
                                                  h_align='center',
                                                  v_align='center')
                choices = [i for i in messenger.saved_ids]
                choices_display = [bui.Lstr(value=messenger.saved_ids[i])
                                   for i in messenger.saved_ids]
                choices.append('add')
                choices_display.append(bui.Lstr(value='***Add New***'))
                filter_widget = PopupMenu(
                    parent=self._root_widget,
                    position=(self._width * 0.4,
                              self._height - 80),
                    width=200,
                    scale=(2.8 if uiscale is bui.UIScale.SMALL else
                           1.8 if uiscale is bui.UIScale.MEDIUM else 1.2),
                    choices=choices,
                    choices_display=choices_display,
                    current_choice=messenger.filter,
                    button_size=(120, 30),
                    on_value_change_call=self._change_filter)
                self._popup_button = filter_widget.get_button()
                if messenger.filter != 'all':
                    user_status = messenger._get_status(messenger.filter)
                    if user_status == 'Offline':
                        color = (1, 0, 0)
                    elif user_status.startswith(('Playing in', 'in Lobby')):
                        color = (0, 1, 0)
                    else:
                        color = (0.9, 1.0, 0.9)
                    self._status_text = bui.textwidget(parent=self._root_widget,
                                                      scale=0.5,
                                                      color=color,
                                                      text=f'Status:\t{user_status}',
                                                      size=(200, 30),
                                                      position=(self._width * 0.3,
                                                                self._height - 110),
                                                      h_align='center',
                                                      v_align='center',
                                                      autoselect=True,
                                                      selectable=True,
                                                      click_activate=True)
                    bui.textwidget(edit=self._status_text,
                                  on_activate_call=bui.Call(messenger._get_status, messenger.filter, 'last_seen'))

    def _change_filter(self, choice):
        if choice == 'add':
            self.close()
            AddNewIdWindow()
        else:
            messenger.filter = choice
            self._firstcall = True
            self._filter_text.delete()
            self._popup_button.delete()
            if self._chat_texts:
                while self._chat_texts:
                    first = self._chat_texts.pop()
                    first.delete()
            self._update()

    def popup_menu_selected_choice(self, popup_window: PopupMenuWindow,
                                   choice: str) -> None:

        """Called when a choice is selected in the popup."""
        if self._popup_type == 'partyMemberPress':
            playerinfo = self._get_player_info(self._popup_party_member_client_id)
            if choice == 'kick':
                name = playerinfo['ds']
                ConfirmWindow(text=f'Are you sure to kick {name}?',
                              action=self._vote_kick_player,
                              cancel_button=True,
                              cancel_is_selected=True,
                              color=self.bg_color,
                              text_scale=1.0,
                              origin_widget=self.get_root_widget())
            elif choice == 'mention':
                players = playerinfo['players']
                choices = []
                namelist = [playerinfo['ds']]
                for player in players:
                    name = player['name_full']
                    if name not in namelist:
                        namelist.append(name)
                choices_display = self._create_baLstr_list(namelist)
                for i in namelist:
                    i = i.replace('"', '\"')
                    i = i.replace("'", "\'")
                    choices.append(f'self._edit_text_msg_box("{i}")')
                PopupMenuWindow(position=popup_window.root_widget.get_screen_space_center(),
                                color=self.bg_color,
                                scale=self._get_popup_window_scale(),
                                choices=choices,
                                choices_display=choices_display,
                                current_choice=choices[0],
                                delegate=self)
                self._popup_type = "executeChoice"
            elif choice == 'adminkick':
                name = playerinfo['ds']
                ConfirmWindow(text=f'Are you sure to use admin\ncommand to kick {name}',
                              action=self._send_admin_kick_command,
                              cancel_button=True,
                              cancel_is_selected=True,
                              color=self.bg_color,
                              text_scale=1.0,
                              origin_widget=self.get_root_widget())
            elif choice == 'customCommands':
                choices = []
                choices_display = []
                playerinfo = self._get_player_info(self._popup_party_member_client_id)
                account = playerinfo['ds']
                try:
                    name = playerinfo['players'][0]['name_full']
                except:
                    name = account
                for i in bui.app.config.get('Custom Commands'):
                    i = i.replace('$c', str(self._popup_party_member_client_id))
                    i = i.replace('$a', str(account))
                    i = i.replace('$n', str(name))
                    if bui.app.config['Direct Send']:
                        choices.append(f'bs.chatmessage("{i}")')
                    else:
                        choices.append(f'self._edit_text_msg_box("{i}")')
                    choices_display.append(bui.Lstr(value=i))
                choices.append('AddNewChoiceWindow()')
                choices_display.append(bui.Lstr(value='***Add New***'))
                PopupMenuWindow(position=popup_window.root_widget.get_screen_space_center(),
                                color=self.bg_color,
                                scale=self._get_popup_window_scale(),
                                choices=choices,
                                choices_display=choices_display,
                                current_choice=choices[0],
                                delegate=self)
                self._popup_type = 'executeChoice'

            elif choice == 'addNew':
                AddNewChoiceWindow()

        elif self._popup_type == 'menu':
            if choice == 'muteOption':
                current_choice = self._get_current_mute_type()
                PopupMenuWindow(
                    position=(self._width - 60, self._height - 47),
                    color=self.bg_color,
                    scale=self._get_popup_window_scale(),
                    choices=['muteInGameOnly', 'mutePartyWindowOnly', 'muteAll', 'unmuteAll'],
                    choices_display=self._create_baLstr_list(
                        ['Mute In Game Messages Only', 'Mute Party Window Messages Only', 'Mute all', 'Unmute All']),
                    current_choice=current_choice,
                    delegate=self
                )
                self._popup_type = 'muteType'
            elif choice == 'modifyColor':
                ColorPickerExact(parent=self.get_root_widget(),
                                 position=self.get_root_widget().get_screen_space_center(),
                                 initial_color=self.bg_color,
                                 delegate=self, tag='')
            elif choice == 'addQuickReply':
                try:
                    newReply = bui.textwidget(query=self._text_field)
                    oldReplies = self._get_quick_responds()
                    oldReplies.append(newReply)
                    self._write_quick_responds(oldReplies)
                    bs.broadcastmessage(f'"{newReply}" is added.', (0, 1, 0))
                    bui.getsound('dingSmallHigh').play()
                except:
                    babase.print_exception()
            if choice == 'add_to_favorites':
                info = bs.get_connection_to_host_info_2()
                if info is not None:
                    self._add_to_favorites(
                        name=info.name,
                        address=info.address,
                        port_num=info.port,
                    )
                else:
                    # We should not allow the user to see this option
                    # if they aren't in a server; this is our bad.
                    bui.screenmessage(
                        bui.Lstr(resource='errorText'), color=(1, 0, 0)
                    )
                    bui.getsound('error').play()
            elif choice == 'removeQuickReply':
                quick_reply = self._get_quick_responds()
                PopupMenuWindow(position=self._send_button.get_screen_space_center(),
                                color=self.bg_color,
                                scale=self._get_popup_window_scale(),
                                choices=quick_reply,
                                choices_display=self._create_baLstr_list(quick_reply),
                                current_choice=quick_reply[0],
                                delegate=self)
                self._popup_type = 'removeQuickReplySelect'
            elif choice == 'credits':
                ConfirmWindow(
                    text=u'\ue043Party Window Reloaded V5.1 API 8 by LaZoeXD\ue043\n\nCredits - Droopy & Pato \nSpecial Thanks - Qhinot#3601',
                    action=self.join_discord,
                    width=420,
                    height=230,
                    color=self.bg_color,
                    text_scale=1.0,
                    ok_text=bui.Lstr(resource='discordJoinText'),
                    origin_widget=self.get_root_widget())
            elif choice == 'manualCamera':
                bui.containerwidget(edit=self._root_widget, transition='out_scale')
                Manual_camera_window()

        elif self._popup_type == 'muteType':
            self._change_mute_type(choice)

        elif self._popup_type == 'executeChoice':
            exec(choice)

        elif self._popup_type == 'quickMessage':
            if choice == '*** EDIT ORDER ***':
                SortQuickMessages()
            else:
                self._edit_text_msg_box(choice)

        elif self._popup_type == 'removeQuickReplySelect':
            data = self._get_quick_responds()
            data.remove(choice)
            self._write_quick_responds(data)
            bs.broadcastmessage(f'"{choice}" is removed.', (1, 0, 0))
            bui.getsound('shieldDown').play()

        else:
            print(f'unhandled popup type: {self._popup_type}')
        del popup_window  # unused

    def _add_to_favorites(
        self, name: str, address: str | None, port_num: int | None
    ) -> None:
        addr = address
        if addr == '':
            bui.screenmessage(
                bui.Lstr(resource='internal.invalidAddressErrorText'),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
            return
        port = port_num if port_num is not None else -1
        if port > 65535 or port < 0:
            bui.screenmessage(
                bui.Lstr(resource='internal.invalidPortErrorText'),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
            return

        # Avoid empty names.
        if not name:
            name = f'{addr}@{port}'

        config = bui.app.config

        if addr:
            if not isinstance(config.get('Saved Servers'), dict):
                config['Saved Servers'] = {}
            config['Saved Servers'][f'{addr}@{port}'] = {
                'addr': addr,
                'port': port,
                'name': name,
            }
            config.commit()
            bui.getsound('gunCocking').play()
            bui.screenmessage(
                bui.Lstr(
                    resource='addedToFavoritesText', subs=[('${NAME}', name)]
                ),
                color=(0, 1, 0),
            )
        else:
            bui.screenmessage(
                bui.Lstr(resource='internal.invalidAddressErrorText'),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
    
    def _vote_kick_player(self):
        if self._popup_party_member_is_host:
            bui.getsound('error').play()
            bs.broadcastmessage(
                bui.Lstr(resource='internal.cantKickHostError'),
                color=(1, 0, 0))
        else:
            assert self._popup_party_member_client_id is not None

            # Ban for 5 minutes.
            result = bs.disconnect_client(
                self._popup_party_member_client_id, ban_time=5 * 60)
            if not result:
                bui.getsound('error').play()
                bs.broadcastmessage(
                    bui.Lstr(resource='getTicketsWindow.unavailableText'),
                    color=(1, 0, 0))

    def _send_admin_kick_command(self):
        bs.chatmessage('/kick ' + str(self._popup_party_member_client_id))

    # def _translate(self):
    #     def _apply_translation(translated):
    #         if self._text_field.exists():
    #             bui.textwidget(edit=self._text_field, text=translated)
    #     msg = bui.textwidget(query=self._text_field)
    #     cfg = bui.app.config
    #     if msg == '':
    #         bs.broadcastmessage('Nothing to translate.', (1, 0, 0))
    #         bui.getsound('error').play()
    #     else:
    #         data = dict(message=msg)
    #         if cfg['Translate Source Language']:
    #             data['src'] = cfg['Translate Source Language']
    #         if cfg['Translate Destination Language']:
    #             data['dest'] = cfg['Translate Destination Language']
    #         if cfg['Pronunciation']:
    #             data['type'] = 'pronunciation'
    #         Translate(data, _apply_translation).start()

    def _copy_to_clipboard(self):
        msg = bui.textwidget(query=self._text_field)
        if msg == '':
            bs.broadcastmessage('Nothing to copy.', (1, 0, 0))
            bui.getsound('error').play()
        else:
            bui.clipboard_set_text(msg)
            bs.broadcastmessage(f'"{msg}" is copied to clipboard.', (0, 1, 0))
            bui.getsound('dingSmallHigh').play()

    def _get_current_mute_type(self):
        cfg = bui.app.config
        if cfg['Chat Muted'] == True:
            if cfg['Party Chat Muted'] == True:
                return 'muteAll'
            else:
                return 'muteInGameOnly'
        else:
            if cfg['Party Chat Muted'] == True:
                return 'mutePartyWindowOnly'
            else:
                return 'unmuteAll'

    def _change_mute_type(self, choice):
        cfg = bui.app.config
        if choice == 'muteInGameOnly':
            cfg['Chat Muted'] = True
            cfg['Party Chat Muted'] = False
        elif choice == 'mutePartyWindowOnly':
            cfg['Chat Muted'] = False
            cfg['Party Chat Muted'] = True
        elif choice == 'muteAll':
            cfg['Chat Muted'] = True
            cfg['Party Chat Muted'] = True
        else:
            cfg['Chat Muted'] = False
            cfg['Party Chat Muted'] = False
        cfg.apply_and_commit()
        self._update()

    def popup_menu_closing(self, popup_window: PopupWindow) -> None:
        """Called when the popup is closing."""

    def _on_party_member_press(self, client_id: int, is_host: bool,
                               widget: bui.Widget) -> None:
        # if we're the host, pop up 'kick' options for all non-host members
        if bs.get_foreground_host_session() is not None:
            kick_str = bui.Lstr(resource='kickText')
        else:
            # kick-votes appeared in build 14248
            info = bs.get_connection_to_host_info_2()
            if info is None or info.build_number < 14248:
                return
            kick_str = bui.Lstr(resource='kickVoteText')
        uiscale = bui.app.ui_v1.uiscale
        choices = ['kick', 'mention', 'adminkick']
        choices_display = [kick_str] + \
            list(self._create_baLstr_list(['Mention this guy', f'Kick ID: {client_id}']))
        choices.append('customCommands')
        choices_display.append(bui.Lstr(value='Custom Commands'))
        PopupMenuWindow(
            position=widget.get_screen_space_center(),
            color=self.bg_color,
            scale=(2.3 if uiscale is bui.UIScale.SMALL else
                   1.65 if uiscale is bui.UIScale.MEDIUM else 1.23),
            choices=choices,
            choices_display=choices_display,
            current_choice='mention',
            delegate=self)
        self._popup_type = 'partyMemberPress'
        self._popup_party_member_client_id = client_id
        self._popup_party_member_is_host = is_host

    def _send_chat_message(self) -> None:
        msg = bui.textwidget(query=self._text_field)
        bui.textwidget(edit=self._text_field, text='')
        if '\\' in msg:
            msg = msg.replace('\\d', ('\ue048'))
            msg = msg.replace('\\c', ('\ue043'))
            msg = msg.replace('\\h', ('\ue049'))
            msg = msg.replace('\\s', ('\ue046'))
            msg = msg.replace('\\n', ('\ue04b'))
            msg = msg.replace('\\f', ('\ue04f'))
            msg = msg.replace('\\g', ('\ue027'))
            msg = msg.replace('\\i', ('\ue03a'))
            msg = msg.replace('\\m', ('\ue04d'))
            msg = msg.replace('\\t', ('\ue01f'))
            msg = msg.replace('\\bs', ('\ue01e'))
            msg = msg.replace('\\j', ('\ue010'))
            msg = msg.replace('\\e', ('\ue045'))
            msg = msg.replace('\\l', ('\ue047'))
            msg = msg.replace('\\a', ('\ue020'))
            msg = msg.replace('\\b', ('\ue00c'))
        if not msg:
            choices = self._get_quick_responds()
            choices.append('*** EDIT ORDER ***')
            PopupMenuWindow(position=self._send_button.get_screen_space_center(),
                            scale=self._get_popup_window_scale(),
                            color=self.bg_color,
                            choices=choices,
                            current_choice=choices[0],
                            delegate=self)
            self._popup_type = 'quickMessage'
            return
        elif msg.startswith('/info '):
            account = msg.replace('/info ', '')
            if account:
                from bauiv1lib.account import viewer
                viewer.AccountViewerWindow(
                    account_id=account)
                bui.textwidget(edit=self._text_field, text='')
                return
        if not self._private_chat:
            if msg == '/id':
                myid = bui.app.plus.get_v1_account_misc_read_val_2('resolvedAccountID', '')
                bs.chatmessage(f"My Unique ID : {myid}")
            elif msg == '/ping':
                bs.chatmessage(f"My ping = {_ping}ms")
            elif msg == '/save':
                info = bs.get_connection_to_host_info_2()
                config = bui.app.config
                if info is not None and info.name != '':
                    title = bui.Lstr(value=info.name)
                    if not isinstance(config.get('Saved Servers'), dict):
                        config['Saved Servers'] = {}
                    config['Saved Servers'][f'{_ip}@{_port}'] = {
                        'addr': _ip,
                        'port': _port,
                        'name': title
                    }
                    config.commit()
                    bs.broadcastmessage("Server Added To Manual", color=(0, 1, 0), transient=True)
                    bui.getsound('gunCocking').play()
            elif msg != '':
                bs.chatmessage(cast(str, msg))
        else:
            receiver = messenger.filter
            name = bui.app.plus.get_v1_account_display_string()
            if not receiver:
                display_error('Choose a valid receiver id')
                return
            data = {'receiver': receiver, 'message': f'{name}: {msg}'}
            if msg.startswith('/rename '):
                if messenger.filter != 'all':
                    nickname = msg.replace('/rename ', '')
                    messenger._save_id(messenger.filter, nickname, verify=False)
                    self._change_filter(messenger.filter)
            elif msg == '/remove':
                if messenger.filter != 'all':
                    messenger._remove_id(messenger.filter)
                    self._change_filter('all')
                else:
                    display_error('Cant delete this')
                bui.textwidget(edit=self._text_field, text='')
                return
            bui.Call(messenger._send_request, url, data)
            bui.Call(check_new_message)
            Thread(target=messenger._send_request, args=(url, data)).start()
            Thread(target=check_new_message).start()
            bui.textwidget(edit=self._text_field, text='')

    def _write_quick_responds(self, data):
        try:
            with open(quick_msg_file, 'w') as f:
                f.write('\n'.join(data))
        except:
            bui.print_exception()
            bs.broadcastmessage('Error!', (1, 0, 0))
            bui.getsound('error').play()

    def _get_quick_responds(self):
        if os.path.exists(quick_msg_file):
            with open(quick_msg_file, 'r') as f:
                return f.read().split('\n')
        else:
            default_replies = ['What the hell?', 'Dude that\'s amazing!']
            self._write_quick_responds(default_replies)
            return default_replies

    def color_picker_selected_color(self, picker, color) -> None:
        bui.containerwidget(edit=self._root_widget, color=color)
        color = tuple(round(i, 2) for i in color)
        self.bg_color = color
        bui.app.config['PartyWindow Main Color'] = color

    def color_picker_closing(self, picker) -> None:
        bui.app.config.apply_and_commit()

    def _remove_sender_from_message(self, msg=''):
        msg_start = msg.find(": ") + 2
        return msg[msg_start:]

    def _previous_message(self):
        msgs = self._chat_texts
        if not hasattr(self, 'msg_index'):
            self.msg_index = len(msgs) - 1
        else:
            if self.msg_index > 0:
                self.msg_index -= 1
            else:
                del self.msg_index
        try:
            msg_widget = msgs[self.msg_index]
            msg = bui.textwidget(query=msg_widget)
            msg = self._remove_sender_from_message(msg)
            if msg in ('', '   '):
                self._previous_message()
                return
        except:
            msg = ''
        self._edit_text_msg_box(msg, 'replace')

    def _next_message(self):
        msgs = self._chat_texts
        if not hasattr(self, 'msg_index'):
            self.msg_index = 0
        else:
            if self.msg_index < len(msgs) - 1:
                self.msg_index += 1
            else:
                del self.msg_index
        try:
            msg_widget = msgs[self.msg_index]
            msg = bui.textwidget(query=msg_widget)
            msg = self._remove_sender_from_message(msg)
            if msg in ('', '   '):
                self._next_message()
                return
        except:
            msg = ''
        self._edit_text_msg_box(msg, 'replace')

    def _ip_port_msg(self):
        try:
            msg = f'IP : {_ip}     PORT : {_port}'
        except:
            msg = ''
        self._edit_text_msg_box(msg, 'replace')

    def ping_server(self):
        info = bs.get_connection_to_host_info_2()
        if info is not None and info.name != '':
            self.pingThread = PingThread(_ip, _port)
            self.pingThread.start()

    def _get_ping_color(self):
        try:
            if _ping < 100:
                return (0, 1, 0)
            elif _ping < 500:
                return (1, 1, 0)
            else:
                return (1, 0, 0)
        except:
            return (0.1, 0.1, 0.1)

    def _send_ping(self):
        if isinstance(_ping, int):
            bs.chatmessage(f'My ping = {_ping}ms')

    def close(self) -> None:
        """Close the window."""
        bui.containerwidget(edit=self._root_widget, transition='out_scale')

    def close_with_sound(self) -> None:
        """Close the window and make a lovely sound."""
        bui.getsound('swish').play()
        self.close()

    def _get_popup_window_scale(self) -> float:
        uiscale = bui.app.ui_v1.uiscale
        return (2.4 if uiscale is bui.UIScale.SMALL else
                1.5 if uiscale is bui.UIScale.MEDIUM else 1.0)

    def _create_baLstr_list(self, list1):
        return (bui.Lstr(value=i) for i in list1)

    def _get_player_info(self, clientID):
        info = {}
        for i in bs.get_game_roster():
            if i['client_id'] == clientID:
                info['ds'] = i['display_string']
                info['players'] = i['players']
                info['aid'] = i['account_id']
                break
        return info

    def _edit_text_msg_box(self, text, action='add'):
        if isinstance(text, str):
            if action == 'add':
                bui.textwidget(edit=self._text_field, text=bui.textwidget(
                    query=self._text_field) + text)
            elif action == 'replace':
                bui.textwidget(edit=self._text_field, text=text)

    def _on_setting_button_press(self):
        try:
            SettingsWindow()
        except Exception as e:
            babase.print_exception()
            pass

    def _on_privatechat_button_press(self):
        try:
            if messenger.logged_in:
                self._firstcall = True
                if self._chat_texts:
                    while self._chat_texts:
                        first = self._chat_texts.pop()
                        first.delete()
                if not self._private_chat:
                    self._private_chat = True
                else:
                    self._filter_text.delete()
                    self._popup_button.delete()
                    self._private_chat = False
                self._update()
            else:
                if messenger.server_online:
                    if not messenger._cookie_login():
                        if messenger._query():
                            LoginWindow(wtype='login')
                        else:
                            LoginWindow(wtype='signup')
                else:
                    display_error(messenger.error)
        except Exception as e:
            babase.print_exception()
            pass

    def join_discord(self):
        bui.open_url("https://discord.gg/lazoexd-official-bs-1132511264900390994")


class LoginWindow:
    def __init__(self, wtype):
        self.wtype = wtype
        if self.wtype == 'signup':
            title = 'Sign Up Window'
            label = 'Sign Up'
        else:
            title = 'Login Window'
            label = 'Log In'
        uiscale = bui.app.ui_v1.uiscale
        bg_color = bui.app.config.get('PartyWindow Main Color', (0.5, 0.5, 0.5))
        self._root_widget = bui.containerwidget(size=(500, 250),
                                               transition='in_scale',
                                               color=bg_color,
                                               toolbar_visibility='menu_minimal_no_back',
                                               parent=bui.get_special_widget('overlay_stack'),
                                               on_outside_click_call=self._close,
                                               scale=(2.1 if uiscale is bui.UIScale.SMALL else
                                                      1.5 if uiscale is bui.UIScale.MEDIUM else 1.0),
                                               stack_offset=(0, -10) if uiscale is bui.UIScale.SMALL else (
                                                   240, 0) if uiscale is bui.UIScale.MEDIUM else (330, 20))
        self._title_text = bui.textwidget(parent=self._root_widget,
                                         scale=0.8,
                                         color=(1, 1, 1),
                                         text=title,
                                         size=(0, 0),
                                         position=(250, 200),
                                         h_align='center',
                                         v_align='center')
        self._id = bui.textwidget(parent=self._root_widget,
                                 scale=0.5,
                                 color=(1, 1, 1),
                                 text=f'Account: ' +
                                 bui.app.plus.get_v1_account_misc_read_val_2(
                                     'resolvedAccountID', ''),
                                 size=(0, 0),
                                 position=(220, 170),
                                 h_align='center',
                                 v_align='center')
        self._registrationkey_text = bui.textwidget(parent=self._root_widget,
                                                   scale=0.5,
                                                   color=(1, 1, 1),
                                                   text=f'Registration Key:',
                                                   size=(0, 0),
                                                   position=(100, 140),
                                                   h_align='center',
                                                   v_align='center')
        self._text_field = bui.textwidget(
            parent=self._root_widget,
            editable=True,
            size=(200, 40),
            position=(175, 130),
            text='',
            maxwidth=410,
            flatness=1.0,
            autoselect=True,
            v_align='center',
            corner_scale=0.7)
        self._connect_button = bui.buttonwidget(parent=self._root_widget,
                                               size=(150, 30),
                                               color=(0, 1, 0),
                                               label='Get Registration Key',
                                               button_type='square',
                                               autoselect=True,
                                               position=(150, 80),
                                               on_activate_call=self._connect)
        self._confirm_button = bui.buttonwidget(parent=self._root_widget,
                                               size=(50, 30),
                                               label=label,
                                               button_type='square',
                                               autoselect=True,
                                               position=(200, 40),
                                               on_activate_call=self._confirmcall)
        bui.textwidget(edit=self._text_field, on_return_press_call=self._confirm_button.activate)

    def _close(self):
        bui.containerwidget(edit=self._root_widget,
                           transition=('out_scale'))

    def _connect(self):
        try:
            host = url.split('http://')[1].split(':')[0]
            import socket
            address = socket.gethostbyname(host)
            bs.disconnect_from_host()
            bs.connect_to_party(address, port=11111)
        except Exception:
            display_error('Cant get ip from hostname')

    def _confirmcall(self):
        if self.wtype == 'signup':
            key = bui.textwidget(query=self._text_field)
            answer = messenger._signup(registration_key=key) if key else None
            if answer:
                self._close()
        else:
            if messenger._login(registration_key=bui.textwidget(query=self._text_field)):
                self._close()

# Plugin Codes byFreaku
class TranslateWindow:
    def __init__(self):
        bg_color = bui.app.config.get('PartyWindow Main Color', (0.5, 0.5, 0.5))
        self.tips = ['You must go to the settings section the\ntool icon then look for "Setting Translate"', 'Click others message to\ntranslate them',
                     'You can set the language\nfor the translate!', 'Close & reopen chat window\n to see original messages']
        self._uiscale = bui.app.ui_v1.uiscale

        self._root_widget = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                                size=(450, 250),
                                                transition='in_scale',
                                                color=bg_color,
                                                scale=(2 if self._uiscale is babase.UIScale.SMALL else
                                                       1.4 if self._uiscale is babase.UIScale.MEDIUM else 1.3),
                                                on_activate_call=babase.Call(self._back, sound=True))
        
        self._back_button = bui.buttonwidget(parent=self._root_widget,
                                     autoselect=True,
                                     position=(30, 200),
                                     size=(30, 30),
                                     label=babase.charstr(babase.SpecialChar.BACK),
                                     button_type='backSmall',
                                     on_activate_call=self._back)
        
        self._tips_text = bui.textwidget(parent=self._root_widget,
                                         color=(0, 1, 1),
                                         h_align='center',
                                         v_align='center',
                                         text='Tips: '+random.choice(self.tips),
                                         position=(200, 188),
                                         maxwidth=250)

        self.other_chat = bui.textwidget(parent=self._root_widget,
                                         color=(1, 1, 1),
                                         h_align='left',
                                         v_align='center',
                                         text='Others chat:',
                                         position=(-10, 140),
                                         maxwidth=59)

        self.your_chat = bui.textwidget(parent=self._root_widget,
                                        color=(1, 1, 1),
                                        h_align='left',
                                        v_align='center',
                                        text='Your chat:',
                                        position=(-10, 55),
                                        maxwidth=59)

        self.other_chat_arrow = bui.textwidget(parent=self._root_widget,
                                               color=(1, 1, 1),
                                               h_align='center',
                                               v_align='center',
                                               text=babase.charstr(babase.SpecialChar.RIGHT_ARROW),
                                               position=(200, 140),
                                               maxwidth=59)

        self.your_chat_arrow = bui.textwidget(parent=self._root_widget,
                                              color=(1, 1, 1),
                                              h_align='center',
                                              v_align='center',
                                              text=babase.charstr(babase.SpecialChar.RIGHT_ARROW),
                                              position=(200, 55),
                                              maxwidth=59)

        self.other_source_button = PopupMenu(parent=self._root_widget,
                                             position=(54, 140),
                                             autoselect=False,
                                             on_value_change_call=babase.Call(
                                                 self._set_translate_language, 'O Source Trans Lang'),
                                             choices=available_translate_languages,
                                             button_size=(150, 30),
                                             current_choice=config['O Source Trans Lang'])

        self.other_target_button = PopupMenu(parent=self._root_widget,
                                             position=(243, 140),
                                             autoselect=False,
                                             on_value_change_call=babase.Call(
                                                 self._set_translate_language, 'O Target Trans Lang'),
                                             choices=available_translate_languages[1:],
                                             button_size=(150, 30),
                                             current_choice=config['O Target Trans Lang'])

        self.your_source_button = PopupMenu(parent=self._root_widget,
                                            position=(54, 55),
                                            autoselect=False,
                                            on_value_change_call=babase.Call(
                                                self._set_translate_language, 'Y Source Trans Lang'),
                                            choices=available_translate_languages,
                                            button_size=(150, 30),
                                            current_choice=config['Y Source Trans Lang'])

        self.your_target_button = PopupMenu(parent=self._root_widget,
                                            position=(243, 55),
                                            autoselect=False,
                                            on_value_change_call=babase.Call(
                                                self._set_translate_language, 'Y Target Trans Lang'),
                                            choices=available_translate_languages[1:],
                                            button_size=(150, 30),
                                            current_choice=config['Y Target Trans Lang'])
    
        bui.containerwidget(edit=self._root_widget, cancel_button=self._back_button)    
    

    def _set_translate_language(self, lang, choice):
        config[lang] = choice

    def _back(self, sound=False):
        self.other_source_button = None
        self.other_target_button = None
        self.your_source_button = None
        self.your_target_button = None
        self._back_button = None
        bui.containerwidget(edit=self._root_widget, transition='out_scale')
        if sound:
            bui.getsound('swish').play()

class AddNewIdWindow:
    def __init__(self):
        uiscale = bui.app.ui_v1.uiscale
        bg_color = bui.app.config.get('PartyWindow Main Color', (0.5, 0.5, 0.5))
        self._root_widget = bui.containerwidget(size=(500, 250),
                                               transition='in_scale',
                                               color=bg_color,
                                               toolbar_visibility='menu_minimal_no_back',
                                               parent=bui.get_special_widget('overlay_stack'),
                                               on_outside_click_call=self._close,
                                               scale=(2.1 if uiscale is bui.UIScale.SMALL else
                                                      1.5 if uiscale is bui.UIScale.MEDIUM else 1.0))
        self._title_text = bui.textwidget(parent=self._root_widget,
                                         scale=0.8,
                                         color=(1, 1, 1),
                                         text='Add New ID',
                                         size=(0, 0),
                                         position=(250, 200),
                                         h_align='center',
                                         v_align='center')
        self._accountid_text = bui.textwidget(parent=self._root_widget,
                                             scale=0.6,
                                             color=(1, 1, 1),
                                             text='pb-id: ',
                                             size=(0, 0),
                                             position=(50, 155),
                                             h_align='center',
                                             v_align='center')
        self._accountid_field = bui.textwidget(
            parent=self._root_widget,
            editable=True,
            size=(250, 40),
            position=(100, 140),
            text='',
            maxwidth=410,
            flatness=1.0,
            autoselect=True,
            v_align='center',
            corner_scale=0.7)
        self._nickname_text = bui.textwidget(parent=self._root_widget,
                                            scale=0.5,
                                            color=(1, 1, 1),
                                            text='Nickname: ',
                                            size=(0, 0),
                                            position=(50, 115),
                                            h_align='center',
                                            v_align='center')
        self._nickname_field = bui.textwidget(
            parent=self._root_widget,
            editable=True,
            size=(250, 40),
            position=(100, 100),
            text='<default>',
            maxwidth=410,
            flatness=1.0,
            autoselect=True,
            v_align='center',
            corner_scale=0.7)
        self._help_text = bui.textwidget(parent=self._root_widget,
                                        scale=0.4,
                                        color=(0.1, 0.9, 0.9),
                                        text='Help:\nEnter pb-id of account you\n    want to chat to\nEnter nickname of id to\n    recognize id easily\nLeave nickname <default>\n    to use their default name',
                                        size=(0, 0),
                                        position=(325, 120),
                                        h_align='left',
                                        v_align='center')
        self._add = bui.buttonwidget(parent=self._root_widget,
                                    size=(50, 30),
                                    label='Add',
                                    button_type='square',
                                    autoselect=True,
                                    position=(100, 50),
                                    on_activate_call=bui.Call(self._relay_function))
        bui.textwidget(edit=self._accountid_field, on_return_press_call=self._add.activate)
        self._remove = bui.buttonwidget(parent=self._root_widget,
                                       size=(75, 30),
                                       label='Remove',
                                       button_type='square',
                                       autoselect=True,
                                       position=(170, 50),
                                       on_activate_call=self._remove_id)
        bui.containerwidget(edit=self._root_widget,
                           on_cancel_call=self._close)

    def _relay_function(self):
        account_id = bui.textwidget(query=self._accountid_field)
        nickname = bui.textwidget(query=self._nickname_field)
        try:
            if messenger._save_id(account_id, nickname):
                self._close()
        except:
            display_error('Enter valid pb-id')

    def _remove_id(self):
        uiscale = bui.app.ui_v1.uiscale
        if len(messenger.saved_ids) > 1:
            choices = [i for i in messenger.saved_ids]
            choices.remove('all')
            choices_display = [bui.Lstr(value=messenger.saved_ids[i]) for i in choices]
            PopupMenuWindow(position=self._remove.get_screen_space_center(),
                            color=bui.app.config.get('PartyWindow Main Color', (0.5, 0.5, 0.5)),
                            scale=(2.4 if uiscale is bui.UIScale.SMALL else
                                   1.5 if uiscale is bui.UIScale.MEDIUM else 1.0),
                            choices=choices,
                            choices_display=choices_display,
                            current_choice=choices[0],
                            delegate=self)
            self._popup_type = 'removeSelectedID'

    def popup_menu_selected_choice(self, popup_window: PopupMenuWindow,
                                   choice: str) -> None:
        """Called when a choice is selected in the popup."""
        if self._popup_type == 'removeSelectedID':
            messenger._remove_id(choice)
            self._close()

    def popup_menu_closing(self, popup_window: PopupWindow) -> None:
        """Called when the popup is closing."""

    def _close(self):
        bui.containerwidget(edit=self._root_widget,
                           transition=('out_scale'))


class AddNewChoiceWindow:
    def __init__(self):
        uiscale = bui.app.ui_v1.uiscale
        bg_color = bui.app.config.get('PartyWindow Main Color', (0.5, 0.5, 0.5))
        self._root_widget = bui.containerwidget(size=(500, 250),
                                               transition='in_scale',
                                               color=bg_color,
                                               toolbar_visibility='menu_minimal_no_back',
                                               parent=bui.get_special_widget('overlay_stack'),
                                               on_outside_click_call=self._close,
                                               scale=(2.1 if uiscale is bui.UIScale.SMALL else
                                                      1.5 if uiscale is bui.UIScale.MEDIUM else 1.0),
                                               stack_offset=(0, -10) if uiscale is bui.UIScale.SMALL else (
                                                   240, 0) if uiscale is bui.UIScale.MEDIUM else (330, 20))
        self._title_text = bui.textwidget(parent=self._root_widget,
                                         scale=0.8,
                                         color=(1, 1, 1),
                                         text='Add Custom Command',
                                         size=(0, 0),
                                         position=(250, 200),
                                         h_align='center',
                                         v_align='center')
        self._text_field = bui.textwidget(
            parent=self._root_widget,
            editable=True,
            size=(500, 40),
            position=(75, 140),
            text='',
            maxwidth=410,
            flatness=1.0,
            autoselect=True,
            v_align='center',
            corner_scale=0.7)
        self._help_text = bui.textwidget(parent=self._root_widget,
                                        scale=0.4,
                                        color=(0.2, 0.2, 0.2),
                                        text='Use\n$c = client id\n$a = account id\n$n = name',
                                        size=(0, 0),
                                        position=(70, 75),
                                        h_align='left',
                                        v_align='center')
        self._add = bui.buttonwidget(parent=self._root_widget,
                                    size=(50, 30),
                                    label='Add',
                                    button_type='square',
                                    autoselect=True,
                                    position=(150, 50),
                                    on_activate_call=self._add_choice)
        bui.textwidget(edit=self._text_field, on_return_press_call=self._add.activate)
        self._remove = bui.buttonwidget(parent=self._root_widget,
                                       size=(50, 30),
                                       label='Remove',
                                       button_type='square',
                                       autoselect=True,
                                       position=(350, 50),
                                       on_activate_call=self._remove_custom_command)
        bui.containerwidget(edit=self._root_widget,
                           on_cancel_call=self._close)

    def _add_choice(self):
        newCommand = bui.textwidget(query=self._text_field)
        cfg = bui.app.config
        if any(i in newCommand for i in ('$c', '$a', '$n')):
            cfg['Custom Commands'].append(newCommand)
            cfg.apply_and_commit()
            bs.broadcastmessage('Added successfully', (0, 1, 0))
            bui.getsound('dingSmallHigh').play()
            self._close()
        else:
            bs.broadcastmessage('Use at least of these ($c, $a, $n)', (1, 0, 0))
            bui.getsound('error').play()

    def _remove_custom_command(self):
        uiscale = bui.app.ui_v1.uiscale
        commands = bui.app.config['Custom Commands']
        PopupMenuWindow(position=self._remove.get_screen_space_center(),
                        color=bui.app.config.get('PartyWindow Main Color', (0.5, 0.5, 0.5)),
                        scale=(2.4 if uiscale is bui.UIScale.SMALL else
                               1.5 if uiscale is bui.UIScale.MEDIUM else 1.0),
                        choices=commands,
                        current_choice=commands[0],
                        delegate=self)
        self._popup_type = 'removeCustomCommandSelect'

    def popup_menu_selected_choice(self, popup_window: PopupMenuWindow,
                                   choice: str) -> None:
        """Called when a choice is selected in the popup."""
        if self._popup_type == 'removeCustomCommandSelect':
            config = bui.app.config
            config['Custom Commands'].remove(choice)
            config.apply_and_commit()
            bs.broadcastmessage('Removed successfully', (0, 1, 0))
            bui.getsound('shieldDown').play()

    def popup_menu_closing(self, popup_window: PopupWindow) -> None:
        """Called when the popup is closing."""

    def _close(self):
        bui.containerwidget(edit=self._root_widget,
                           transition=('out_scale'))


class Manual_camera_window:
    def __init__(self):
        self._root_widget = bui.containerwidget(
            on_outside_click_call=None,
            size=(0, 0))
        button_size = (30, 30)
        self._title_text = bui.textwidget(parent=self._root_widget,
                                         scale=0.9,
                                         color=(1, 1, 1),
                                         text='Manual Camera Setup',
                                         size=(0, 0),
                                         position=(130, 153),
                                         h_align='center',
                                         v_align='center')
        self._xminus = bui.buttonwidget(parent=self._root_widget,
                                       size=button_size,
                                       label=babase.charstr(babase.SpecialChar.LEFT_ARROW),
                                       button_type='square',
                                       autoselect=True,
                                       position=(1, 60),
                                       on_activate_call=bui.Call(self._change_camera_position, 'x-'))
        self._xplus = bui.buttonwidget(parent=self._root_widget,
                                      size=button_size,
                                      label=babase.charstr(babase.SpecialChar.RIGHT_ARROW),
                                      button_type='square',
                                      autoselect=True,
                                      position=(60, 60),
                                      on_activate_call=bui.Call(self._change_camera_position, 'x'))
        self._yplus = bui.buttonwidget(parent=self._root_widget,
                                      size=button_size,
                                      label=babase.charstr(babase.SpecialChar.UP_ARROW),
                                      button_type='square',
                                      autoselect=True,
                                      position=(30, 100),
                                      on_activate_call=bui.Call(self._change_camera_position, 'y'))
        self._yminus = bui.buttonwidget(parent=self._root_widget,
                                       size=button_size,
                                       label=babase.charstr(babase.SpecialChar.DOWN_ARROW),
                                       button_type='square',
                                       autoselect=True,
                                       position=(30, 20),
                                       on_activate_call=bui.Call(self._change_camera_position, 'y-'))
        self.inwards = bui.buttonwidget(parent=self._root_widget,
                                       size=(100, 30),
                                       label='INWARDS',
                                       button_type='square',
                                       autoselect=True,
                                       position=(120, 90),
                                       on_activate_call=bui.Call(self._change_camera_position, 'z-'))
        self._outwards = bui.buttonwidget(parent=self._root_widget,
                                         size=(100, 30),
                                         label='OUTWARDS',
                                         button_type='square',
                                         autoselect=True,
                                         position=(120, 50),
                                         on_activate_call=bui.Call(self._change_camera_position, 'z'))
        self._step_text = bui.textwidget(parent=self._root_widget,
                                        scale=0.5,
                                        color=(1, 1, 1),
                                        text='Step:',
                                        size=(0, 0),
                                        position=(1, -20),
                                        h_align='center',
                                        v_align='center')
        self._text_field = bui.textwidget(
            parent=self._root_widget,
            editable=True,
            size=(100, 40),
            position=(26, -35),
            text='',
            maxwidth=120,
            flatness=1.0,
            autoselect=True,
            v_align='center',
            corner_scale=0.7)
        self._reset = bui.buttonwidget(parent=self._root_widget,
                                      size=(50, 30),
                                      label='Reset',
                                      button_type='square',
                                      autoselect=True,
                                      position=(120, -35),
                                      on_activate_call=bui.Call(self._change_camera_position, 'reset'))
        self._done = bui.buttonwidget(parent=self._root_widget,
                                     size=(50, 30),
                                     label='Done',
                                     button_type='square',
                                     autoselect=True,
                                     position=(180, -35),
                                     on_activate_call=self._close)
        bui.containerwidget(edit=self._root_widget,
                           cancel_button=self._done)

    def _close(self):
        bui.containerwidget(edit=self._root_widget,
                           transition=('out_scale'))

    def _change_camera_position(self, direction):
        activity = bs.get_foreground_host_activity()
        node = activity.globalsnode
        aoi = list(node.area_of_interest_bounds)
        center = [(aoi[0] + aoi[3]) / 2,
                  (aoi[1] + aoi[4]) / 2,
                  (aoi[2] + aoi[5]) / 2]
        size = (aoi[3] - aoi[0],
                aoi[4] - aoi[1],
                aoi[5] - aoi[2])

        try:
            increment = float(bui.textwidget(query=self._text_field))
        except:
            # babase.print_exception()
            increment = 1

        if direction == 'x':
            center[0] += increment
        elif direction == 'x-':
            center[0] -= increment
        elif direction == 'y':
            center[1] += increment
        elif direction == 'y-':
            center[1] -= increment
        elif direction == 'z':
            center[2] += increment
        elif direction == 'z-':
            center[2] -= increment
        elif direction == 'reset':
            node.area_of_interest_bounds = activity._map.get_def_bound_box(
                'area_of_interest_bounds')
            return

        aoi = (center[0] - size[0] / 2,
               center[1] - size[1] / 2,
               center[2] - size[2] / 2,
               center[0] + size[0] / 2,
               center[1] + size[1] / 2,
               center[2] + size[2] / 2)
        node.area_of_interest_bounds = tuple(aoi)


def __popup_menu_window_init__(self,
                               position: Tuple[float, float],
                               choices: Sequence[str],
                               current_choice: str,
                               delegate: Any = None,
                               width: float = 230.0,
                               maxwidth: float = None,
                               scale: float = 1.0,
                               color: Tuple[float, float, float] = (0.35, 0.55, 0.15),
                               choices_disabled: Sequence[str] = None,
                               choices_display: Sequence[bui.Lstr] = None):
    # FIXME: Clean up a bit.
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements
    if choices_disabled is None:
        choices_disabled = []
    if choices_display is None:
        choices_display = []

    # FIXME: For the moment we base our width on these strings so
    #  we need to flatten them.
    choices_display_fin: List[str] = []
    for choice_display in choices_display:
        choices_display_fin.append(choice_display.evaluate())

    if maxwidth is None:
        maxwidth = width * 1.5

    self._transitioning_out = False
    self._choices = list(choices)
    self._choices_display = list(choices_display_fin)
    self._current_choice = current_choice
    self._color = color
    self._choices_disabled = list(choices_disabled)
    self._done_building = False
    if not choices:
        raise TypeError('Must pass at least one choice')
    self._width = width
    self._scale = scale
    if len(choices) > 8:
        self._height = 280
        self._use_scroll = True
    else:
        self._height = 20 + len(choices) * 33
        self._use_scroll = False
    self._delegate = None  # don't want this stuff called just yet..

    # extend width to fit our longest string (or our max-width)
    for index, choice in enumerate(choices):
        if len(choices_display_fin) == len(choices):
            choice_display_name = choices_display_fin[index]
        else:
            choice_display_name = choice
        if self._use_scroll:
            self._width = max(
                self._width,
                min(
                    maxwidth,
                    _babase.get_string_width(choice_display_name,
                                         suppress_warning=True)) + 75)
        else:
            self._width = max(
                self._width,
                min(
                    maxwidth,
                    _babase.get_string_width(choice_display_name,
                                         suppress_warning=True)) + 60)

    # init parent class - this will rescale and reposition things as
    # needed and create our root widget
    PopupWindow.__init__(self,
                         position,
                         size=(self._width, self._height),
                         bg_color=self._color,
                         scale=self._scale)

    if self._use_scroll:
        self._scrollwidget = bui.scrollwidget(parent=self.root_widget,
                                             position=(20, 20),
                                             highlight=False,
                                             color=(0.35, 0.55, 0.15),
                                             size=(self._width - 40,
                                                   self._height - 40))
        self._columnwidget = bui.columnwidget(parent=self._scrollwidget,
                                             border=2,
                                             margin=0)
    else:
        self._offset_widget = bui.containerwidget(parent=self.root_widget,
                                                 position=(30, 15),
                                                 size=(self._width - 40,
                                                       self._height),
                                                 background=False)
        self._columnwidget = bui.columnwidget(parent=self._offset_widget,
                                             border=2,
                                             margin=0)
    for index, choice in enumerate(choices):
        if len(choices_display_fin) == len(choices):
            choice_display_name = choices_display_fin[index]
        else:
            choice_display_name = choice
        inactive = (choice in self._choices_disabled)
        wdg = bui.textwidget(parent=self._columnwidget,
                            size=(self._width - 40, 28),
                            on_select_call=bui.Call(self._select, index),
                            click_activate=True,
                            color=(0.5, 0.5, 0.5, 0.5) if inactive else
                            ((0.5, 1, 0.5,
                              1) if choice == self._current_choice else
                             (0.8, 0.8, 0.8, 1.0)),
                            padding=0,
                            maxwidth=maxwidth,
                            text=choice_display_name,
                            on_activate_call=self._activate,
                            v_align='center',
                            selectable=(not inactive))
        if choice == self._current_choice:
            bui.containerwidget(edit=self._columnwidget,
                               selected_child=wdg,
                               visible_child=wdg)

    # ok from now on our delegate can be called
    self._delegate = weakref.ref(delegate)
    self._done_building = True


original_connect_to_party = bs.connect_to_party
original_sign_in = babase.app.plus.sign_in_v1


def modify_connect_to_party(address: str, port: int = 43210, print_progress: bool = True) -> None:
    global _ip, _port
    _ip = address
    _port = port
    original_connect_to_party(_ip, _port, print_progress)


temptimer = None


def modify_sign_in(account_type: str) -> None:
    original_sign_in(account_type)
    if messenger.server_online:
        messenger.logged_in = False
        global temptimer
        temptimer = bs.AppTimer(2, messenger._cookie_login)


class PingThread(Thread):
    """Thread for sending out game pings."""

    def __init__(self, address: str, port: int):
        super().__init__()
        self._address = address
        self._port = port

    def run(self) -> None:
        sock: Optional[socket.socket] = None
        try:
            import socket
            from babase import get_ip_address_type
            socket_type = get_ip_address_type(self._address)
            sock = socket.socket(socket_type, socket.SOCK_DGRAM)
            sock.connect((self._address, self._port))

            starttime = time.time()

            # Send a few pings and wait a second for
            # a response.
            sock.settimeout(1)
            for _i in range(3):
                sock.send(b'\x0b')
                result: Optional[bytes]
                try:
                    # 11: BA_PACKET_SIMPLE_PING
                    result = sock.recv(10)
                except Exception:
                    result = None
                if result == b'\x0c':
                    # 12: BA_PACKET_SIMPLE_PONG
                    accessible = True
                    break
                time.sleep(1)
            global _ping
            _ping = int((time.time() - starttime) * 1000.0)
        except Exception:
            babase.print_exception('Error on gather ping', once=True)
        finally:
            try:
                if sock is not None:
                    sock.close()
            except Exception:
                babase.print_exception('Error on gather ping cleanup', once=True)


def _get_store_char_tex(self) -> str:
    bui.set_party_icon_always_visible(True)
    return ('storeCharacterXmas' if bui.app.plus.get_v1_account_misc_read_val(
        'xmas', False) else
        'storeCharacterEaster' if bui.app.plus.get_v1_account_misc_read_val(
        'easter', False) else 'storeCharacter')


# DEBUG
tex = None
coin = None
# DEBUG END
# ba_meta export plugin
class ByPato(babase.Plugin):
    def __init__(self):
        if _babase.env().get("build_number", 0) >= 20124:
            global messenger, listener, displayer, color_tracker
            initialize()
            messenger = PrivateChatHandler()
            listener = Thread(target=messenger_thread)
            listener.start()
            displayer = babase.AppTimer(0.4, msg_displayer, True)
            color_tracker = ColorTracker()
            bauiv1lib.party.PartyWindow = PartyWindow
            PopupMenuWindow.__init__ = __popup_menu_window_init__
            bs.connect_to_party = modify_connect_to_party
            babase.app.plus.sign_in_v1 = modify_sign_in
            MainMenuWindow._get_store_char_tex = _get_store_char_tex
            # DEBUG
            bs.apptimer(2, self.get_icon)
            # DEBUG END
        else:
            display_error("This Party Window only runs with BombSquad version higer than 1.6.0.")
    def get_icon(self):
        # DEBUG
        global tex
        global coin
        with bs.get_foreground_host_activity().context:
            tex = bs.gettexture("circleShadow")
            coin = bs.gettexture("coin")
        # DEBUG END
