import os
os.environ.update({"DJANGO_SETTINGS_MODULE": "dashboard.settings"})
import django
django.setup()


import json
import time
import shutil
import random

import requests
from selenium import webdriver

from postsite.models import Product
from utils.request_pkg import get_chrome_options, rotate_headers
from utils.comm import SUCCEED_STATUS, FAILED_STATUS

BASE_DIR = \
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TouTiao:
    def __init__(self, account):
        self.dir_path = os.path.join(BASE_DIR, 'static/toutiao/{}'.format(account))
        if not os.path.exists(self.dir_path):os.makedirs(self.dir_path)
        self.cookies_file = os.path.join(self.dir_path, 'cookies.txt')
        self.product = Product.objects.filter(is_posted=0)[0]
        self.session = requests.Session()

    def main(self, account, password, display_name):
        self._load_cookies()
        self._post()

    def _post(self):
        referer = 'https://www.toutiao.com/c/user/99025955606/?publish=1%27'
        host = 'www.toutiao.com'
        url = 'https://www.toutiao.com/c/ugc/content/publish/'
        origin = 'https://www.toutiao.com'
        headers = rotate_headers(referer=referer, host=host, origin=origin)
        headers['X-CSRFToken'] = self.session.cookies['csrftoken']

        uris = self._upload_image()
        uris = ','.join(uris)
        data = {
            'content': self.product.content,
            'image_uris': uris,
        }
        resp = self.session.post(url, verify=False, headers=headers, data=data)
        if resp.status_code == 200:
            print('\033[94m 今日头条: {} 发帖成功 \033[0m'.format(self.product.content))
            self.product.update_status(is_posted=1)
            return SUCCEED_STATUS, 'Succeed!'
        else:
            print('\033[94m 今日头条: {} 发帖失败 \033[0m'.format(self.product.content))
            return FAILED_STATUS, 'Failed!'

    def _upload_image(self):
        referer = 'https://www.toutiao.com/c/user/99025955606/?publish=1%27'   #### 这里需要找到不同用户的 ID
        host = 'www.toutiao.com'
        url = 'https://www.toutiao.com/c/ugc/image/upload/'
        headers = rotate_headers(referer=referer, host=host)
        uris = []

        image_dir = self._download_images()
        images = os.listdir(image_dir)
        images.append(self._random_wechat())
        for image in images:
            image_name = os.path.basename(image)
            image_path = os.path.join(image_dir, image)
            files = {
                'file': (image_name, open(image_path, 'rb'), 'image/jpeg'),
            }
            resp = self.session.post(url, verify=False, files=files, headers=headers)
            resp_content = resp.content.decode('utf-8')
            if 'success' in resp_content:
                print('{} 图片上传成功'.format(image_name))
                uri = json.loads(resp_content)['data']['web_uri']
                print('图片地址为:{}'.format(uri))
                uris.append(uri)
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

    def _login(self, account, password, dispaly_name, is_linux=True):
        login_url = "https://sso.toutiao.com/login/"
        if is_linux:
            chrome_options = get_chrome_options()
            driver = webdriver.Chrome(options=chrome_options)
        else:
            driver = webdriver.Chrome(executable_path="C:/Program Files (x86)/Google/Chrome/Application/chromedriver")
        driver.get(login_url)
        # 账号登录
        driver.find_element_by_xpath('//li[@class="sns  mail-login"]').click()
        driver.find_element_by_xpath('//input[@id="account"]').send_keys(account)
        driver.find_element_by_xpath('//input[@id="password"]').send_keys(password)
        vcode = input("请输入图片验证码：")
        driver.find_element_by_xpath('//input[@id="captcha"]').send_keys(vcode)
        driver.find_element_by_xpath('//input[@type="submit" and @name="submitBtn"]').click()

        # 点击以后会出现三种情况：1、继续输入验证码；2、进行手机登录， 3、成功登录
        if '请输入图片验证码' in driver.page_source:
            # 这里会要求不停重复输入，暂时没找到原因
            pass
        elif '为保证安全，请使用手机验证码登录' in driver.page_source:
            driver.find_element_by_xpath('//input[@id="mobile"]').send_keys(account)
            driver.find_element_by_xpath('//input[@id="code"]/following-sibling::span').click()
            ncode = input("请输入短信验证码：")
            driver.find_element_by_xpath('//input[@id="code"]').send_keys(ncode)
            driver.find_element_by_xpath('//input[@type="submit" and @name="submitBtn"]').click()


        cookies = driver.get_cookies()
        login_cookies = {item["name"] : item["value"] for item in cookies}
        if self._check_login(dispaly_name, driver=driver):
            with open(self.cookies_file, "w") as f:
                json.dump(login_cookies, f)
            self.session.cookies.update(login_cookies)
            print('{} 登录成功！'.format(dispaly_name))
        else:
            print('{} 登录失败！'.format(dispaly_name))

    def _check_login(self, username, driver):
       '''
       验证是否成功登录
       '''
       try:
           login = driver.find_element_by_xpath('//div[@id="rightModule"]')
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
    account = '16620046225'
    password = 'bao1808lL'
    dispaly_name = '奢表小主'
    # account = '18520293917'
    # password = 'cg19881004'
    # dispaly_name = '手机用户69894429459'
    TouTiao(account).main(account, password, dispaly_name)
