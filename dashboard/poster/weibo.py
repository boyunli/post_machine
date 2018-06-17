import os
os.environ.update({"DJANGO_SETTINGS_MODULE": "dashboard.settings"})
import django
django.setup()


import json
import time
import shutil
import random
import base64
from urllib import parse

import requests
from selenium import webdriver
from django.db.models import Q

from postsite.models import Product
from utils.request_pkg import get_chrome_options, rotate_headers
from utils.comm import SUCCEED_STATUS, FAILED_STATUS

BASE_DIR = \
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class WeiBo:
    def __init__(self, account, product):
        self.dir_path = os.path.join(BASE_DIR, 'static/weibo/{}'.format(account))
        if not os.path.exists(self.dir_path):os.makedirs(self.dir_path)
        self.cookies_file = os.path.join(self.dir_path, 'cookies.txt')
        self.session = requests.Session()
        self.product = product

    def main(self, account, password, display_name, domain):
        self._load_cookies()
        return self._post(account, password, display_name, domain)

    def _post(self, account, password, display_name, domain):
        # referer = 'https://weibo.com/5127234756/profile?profile_ftype=1&is_ori=1'
        referer = 'https://weibo.com/{d}/home?wvr=5&lf=reg'.format(d=domain)
        host = 'weibo.com'
        origin = 'https://weibo.com'
        timestamp = int(time.time()*1000)
        url = 'https://weibo.com/p/aj/v6/mblog/add?ajwvr=6&domain={d}&__rnd={t}'\
            .format(t=timestamp, d='100505')

        headers = rotate_headers(referer=referer, host=host, origin=origin)

        uri = self._upload_image(domain, display_name)
        uris = '|'.join(uri)
        data = {
            'title': '有什么新鲜事想告诉大家?',
            'location': 'page_100505_home',
            'text': self.product.content,
            'style_type': '1',
            'pic_id': uris,
            'tid': '',
            'pdetail': '1005055127234756',
            'mid': '',
            'isReEdit': 'false',
            'gif_ids': '',
            'rank': '0',
            'rankid': '',
            'pub_source': 'page_2',
            'longtext': '1',
            'topic_id': '1022:',
            'updata_img_num': len(uri),
            'pub_type': 'dialog',
            '_t': '0'
        }
        resp = self.session.post(url, verify=False, headers=headers, data=data)
        try:
            text = json.loads(resp.text)
        except json.decoder.JSONDecodeError:
            self._login(account, password, display_name)
            uri = self._upload_image(domain, display_name)
            uris = '|'.join(uri)
            data['pic_id'] = uris
            data['updata_img_num'] = len(uri)
            resp = self.session.post(url, verify=False, headers=headers, data=data)
            text = json.loads(resp.text)
        if text['code'] == "100000":
            print('\033[94m 微博: {} 发帖成功 \033[0m'.format(display_name))
            self.product.update_status(is_posted=1)
            return SUCCEED_STATUS, 'Succeed!'
        else:
            print('\033[94m 微博: {} 发帖失败 \033[0m'.format(display_name))
            return FAILED_STATUS, text['msg']

    def _upload_image(self, domain, display_name):
        referer = 'https://weibo.com/{d}/home?wvr=5&lf=reg'.format(d=domain)
        host = 'picupload.weibo.com'
        timestamp = int(time.time()*100000)

        cb = 'https://weibo.com/aj/static/upimgback.html?_wv=5&callback=STK_ijax_{t}'.format(t=timestamp)
        if 'liling' in domain:
            url_ = 'weibo.com/{}'.format(domain)
            nick = '@{}'.format(display_name)
        else:
            url_ = 0
            nick = 0
        url = 'https://picupload.weibo.com/interface/pic_upload.php?cb={cb}&mime=image%2Fjpeg&data=base64&url={url_}&markpos=1&logo=1&nick={nick}&marks=0&app=miniblog&s=rdxt&pri=null&file_source=1'\
            .format(cb=cb, url_=url_, nick=nick)
        headers = rotate_headers(referer=referer, host=host)
        uris = []

        image_dir = self._download_images()
        images = os.listdir(image_dir)
        images.append(self._random_wechat())
        for image in images:
            image_name = os.path.basename(image)
            image_path = os.path.join(image_dir, image)
            with open(image_path, 'rb') as f:
                b64_image = base64.b64encode(f.read())
            resp = self.session.post(url, verify=False, headers=headers,
                                     data={'b64_data':b64_image}, allow_redirects=False)
            location = resp.headers.get('Location')
            if location:
                try:
                    img_name = parse.parse_qs(parse.urlparse(location).query)['pid'][0]
                except:
                    print('{} 图片上传失败'.format(image_name))
                    continue
                print('{}上传成功，图片地址为:{}'\
                      .format(image_name, 'https://wx2.sinaimg.cn/square/'+ img_name + '.jpg'))
                uris.append(img_name)
            else:
                continue
        return uris

    def _download_images(self):
        images = self.product.images
        images = images.split('**')
        if len(images) > 8:
            images = images[:8]
        timestamp = int(time.time())
        download_dir = os.path.join(self.dir_path, 'images/{}'.format(timestamp))
        if not os.path.exists(download_dir):os.makedirs(download_dir)
        for url in images:
            time.sleep(1)
            image_f = os.path.join(download_dir,
                                  '{}.jpeg'.format(int(time.time())))
            res = self.session.get(url, stream=True)
            if res .status_code == 200:
                with open(image_f, 'wb') as ff:
                    res.raw.decode_content = True
                    shutil.copyfileobj(res.raw, ff)
            else:
                continue
        return download_dir

    def _random_wechat(self):
        images_dir = os.path.join(self.dir_path, 'wechat')
        files = os.listdir(images_dir)
        files = [ os.path.join(images_dir, file_) for file_ in files]
        index = random.randint(0, len(files)-1)
        return files[index]

    def _login(self, account, password, display_name, is_linux=True):
        login_url = "https://weibo.com/"
        if is_linux:
            chrome_options = get_chrome_options()
            driver = webdriver.Chrome(options=chrome_options)
        else:
            driver = webdriver.Chrome(executable_path="C:/Program Files (x86)/Google/Chrome/Application/chromedriver")
        driver.get(login_url)
        # 账号登录
        time.sleep(15)
        driver.find_element_by_xpath('//input[@id="loginname"]').send_keys(account)
        driver.find_element_by_xpath('//input[@type="password" and @class="W_input"]').send_keys(password)
        driver.find_element_by_xpath('//a[@class="W_btn_a btn_32px" and @action-type="btn_submit"]').click()

        cookies = driver.get_cookies()
        login_cookies = {item["name"] : item["value"] for item in cookies}
        if self._check_login(display_name, driver=driver):
            with open(self.cookies_file, "w") as f:
                json.dump(login_cookies, f)
            self.session.cookies.update(login_cookies)
            print('{} 登录成功！'.format(display_name))
        else:
            print('{} 登录失败！'.format(display_name))

    def _check_login(self, username, driver):
       '''
       验证是否成功登录
       '''
       try:
           login = driver.find_element_by_xpath('//a[@class="name S_txt1"]')
           time.sleep(2)
           if username in login.text:
               return True
           else:
               return False
       except:
           return False

    def _load_cookies(self):
        """从文本中获得cookie
        """
        with open(self.cookies_file) as f:
            cookies = json.load(f)
            self.session.cookies.update(cookies)




if __name__ == '__main__':
    # account = '18520613361'
    # password = 'lilingvae00'
    # display_name = '奢表小主'
    # domain = 'lilingvae00'
    account = '13250329052'
    password = 'cg19881004+'
    display_name = '瑞士复刻手表'
    domain = 'watch1905'
    product = Product.objects.filter(~Q(images=''), is_posted=0)[0]
    WeiBo(account, product).main(account, password, display_name, domain)
