#!/usr/bin/python
# coding: utf-8

import traceback
import requests
import httplib
import hmac, base64, struct, hashlib, time


def get_hotp_token(secret, intervals_no):
    key = base64.b32decode(secret, True)
    msg = struct.pack(">Q", intervals_no)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    o = ord(h[19]) & 15
    h = (struct.unpack(">I", h[o:o+4])[0] & 0x7fffffff) % 1000000
    return h


def get_totp_token(secret):
    return '%06u' % get_hotp_token(secret, intervals_no=int(time.time())//30)


class CHuobi(object):
    def __init__(self, conf):
        self._username = conf['username']
        self._password = conf['password']
        self._password2 = conf['password2']
        self._otp_secret = conf['otp_secret']
        self._withdraw_btc_addr = conf['withdraw_btc_addr']
        self._withdraw_ltc_addr = conf['withdraw_ltc_addr']


    def _get_session(self):
        headers = {}
        headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.116 Safari/537.36'
        headers['Referer'] = 'https://www.huobi.com/'
        headers['Origin'] = 'https://www.huobi.com'
        headers['Accept-Encoding'] = 'gzip,deflate'
        headers['Accept-Language'] = 'en-US,en;q=0.8'
        headers['Connection'] = 'keep-alive'

        session = requests.Session()
        session.headers = headers
        session.verify = False

        return session


    def _login(self, session):
        """login"""
        try:
            r = session.get('https://www.huobi.com')
        except:
            return False

        data = {'email': self._username, 'password': self._password}

        try:
            r = session.post('https://www.huobi.com/account/login.php', data=data)
            ret = True
        except:
            traceback.print_exc()
            ret = False

        return ret


    def withdraw(self, coin, amount):
        """ 提币 """
        if not (self._username and self._password and self._password2 and self._otp_secret):
            return False

        if coin not in ('btc', 'ltc'):
            return False

        session = self._get_session()
        r = self._login(session)
        if not r:
            return None

        data = {'amt': amount, 'pwd': self._password2}

        if coin == 'btc':
            data['my_channel_id'] = self._withdraw_btc_addr
            data['btc_fast_track'] = 1
            data['fee_type'] = 0
            action = 'btc_withdraw'
        else:
            data['my_channel_id'] = self._withdraw_ltc_addr
            action = 'ltc_withdraw'
        
        headers = {}
        headers['Referer'] = 'https://www.huobi.com/withdraw/index.php?a=%s' % action

        data['google_code'] = get_totp_token(self._otp_secret)

        try:
            r = session.post('https://www.huobi.com/withdraw/index.php?a=process_withdraw', data=data, headers=headers)
            print r.text.encode('GBK', errors='ignore')
            r = True
        except:
            traceback.print_exc()
            r = False

        session.close()
        return r


if __name__ == '__main__':
    conf = {
        'username': '登录用户名',
        'password': '登录密码',
        'password2': '交易密码',
        'otp_secret': '双重认证密码',
        'withdraw_btc_addr': 111111,
        'withdraw_ltc_addr': 222222
    }
    m = CHuobi(conf)
    r = m.withdraw('btc', 10.0001)
    print r
