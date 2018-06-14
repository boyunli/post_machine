#coding:utf-8

import os
import random
import json

import requests
from selenium import webdriver
from fake_useragent import UserAgent
from fake_useragent.errors import FakeUserAgentError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def _crawl_proxy_ip():
    resp = requests.get('http://ubuntu.pydream.com:8000/?types=0&count=5&country=国内')
    socks = json.loads(resp.text)
    sock = random.choice(socks)
    return (sock[0], sock[1])

def get_chrome_options(host=None, origin=None, referer=None, proxy=False):
    options = webdriver.ChromeOptions()
    prefs = {"profile.managed_default_content_settings.images":2}
    options.add_argument('headless')
    options.add_argument('lang=zh_CN.UTF-8')
    options.add_argument('user-agent={}'.format(get_ua()))
    options.add_argument('--start-maximized')
    if host:
        options.add_argument('host={}'.format(host))
    if referer:
        options.add_argument('referer={}'.format(referer))
    if origin:
        options.add_argument('origin={}'.format(origin))
    # 设置不加载图片
    options.add_experimental_option("prefs", prefs)
    if proxy:
        host, port = _crawl_proxy_ip()
        options.add_argument('--proxy-server={}:{}'.format(host, port))
    return options

def phantomjs_args():
    host, port = _crawl_proxy_ip()
    return [
        "--load-images=no",
        "--disk-cache=yes",
        "--ignore-ssl-errors=true",
        "--proxy-type=http",
        "--proxy=%(host)s:%(port)s" % {
                    "host": host,
                    "port": port
                }
    ]

def get_ua():
    ua = ''
    try:
        ua = UserAgent().random
    except FakeUserAgentError:
        file = os.path.join(BASE_DIR, 'user_agent.txt')
        with open(file, 'r') as f:
            uas = f.readlines()
            ua = random.choice(uas).strip()
    print('UserAgent: {}'.format(ua))
    return ua

def rotate_headers(referer=None, origin=None, host=None):
    ua = get_ua()
    headers = {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, sdch, br",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
    }
    if referer:
        headers['Referer'] = referer
    elif origin:
        headers['Origin'] = origin
    elif host:
        headers['Host'] = host
    return headers

def set_proxies():
    host, port = _crawl_proxy_ip()
    config = {
        "http": "http://{host}:{port}".format(host=host, port=port),
    }
    return host, config

def delete_no_use_proxy_ip(ip):
    requests.get('http://127.0.0.1:8000/delete?ip={ip}'.format(ip=ip))


