#!/usr/bin/python
# coding: utf-8

import traceback
import requests
import httplib
import random

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


class COkcoin(object):
    def __init__(self, conf):
        self._username = conf.get('username')
        self._password = conf.get('password')
        self._password2 = conf.get('password2')
        self._otp_secret = conf.get('otp_secret')


    def _get_session(self):
        headers = {}
        headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.116 Safari/537.36'
        headers['Accept-Encoding'] = 'gzip,deflate'
        headers['Accept-Language'] = 'en-US,en;q=0.8'
        headers['Connection'] = 'keep-alive'
        headers['Referer'] = 'https://www.okcoin.com/'
        headers['Origin'] = 'https://www.okcoin.com/'

        session = requests.Session()
        session.headers = headers
        session.verify = False

        return session


    def _login(self, session):
        """login"""
        try:
            r = session.get('https://www.okcoin.com')
        except:
            return None

        data = {'loginName': self._username, 'password': self._password}

        try:
            r = session.post('https://www.okcoin.com/user/login/index.do?rand=%u' % random.randint(1, 100), data=data)
        except:
            traceback.print_exc()
            r = None

        return r


    def withdraw(self, coin, amount):
        """ 提币 """
        if not (self._username and self._password and self._password2 and self._otp_secret):
            return False

        if coin == 'btc':
            symbol = 0
            fee = '0.0001'
            dest = 'BTC提现地址一'
        elif coin == 'ltc':
            symbol = 1
            fee = '0.001'
            dest = 'LTC提现地址一'
        else:
            return False

        session = self._get_session()
        r = self._login(session)
        if not r:
            return None

        data = {'withdrawAddr': dest, 'withdrawAmount': amount, 'serviceChargeFee': fee, 'tradePwd': self._password2, 'totpCode': get_totp_token(self._otp_secret), 'phoneCode': 0, 'symbol': symbol}
        headers = {}
        headers['Referer'] = 'https://www.okcoin.com/account/withdrawBtc.do?symbol=%u' % symbol
        try:
            r = session.post('https://www.okcoin.com/account/withdrawBtcSubmit.do?random=%u' % random.randint(1, 100), data=data, headers=headers)
            ret = r.json()
            print ret
            if ret['errorNum'] == 0:
                r = True
            else:
                r = False
        except:
            r = False

        session.close()
        return r



if __name__ == '__main__':
    conf = {
        'username': '登录用户名',
        'password': '登录密码',
        'password2': '交易密码',
        'otp_secret': '双重认证密码',
    }
    m = COkcoin(conf)
    r = m.withdraw('btc', 2)
    print r
