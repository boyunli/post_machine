# encoding:utf-8
import os
os.environ.update({"DJANGO_SETTINGS_MODULE": "dashboard.settings"})
import django
django.setup()

import time
from urllib.parse import urljoin

from selenium import webdriver
from lxml import etree
from django.utils import timezone

from postsite.models import WebAlbum, Product
from utils.request_pkg import get_ua

BASE_DIR = \
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class UooTu:

    def __init__(self, uid):
        '''
        uid: 有图号
        '''
        self.web = '有图相册'
        self.uid = uid
        self.host = 'https://www.uootu.com'
        self.dir_path = os.path.join(BASE_DIR, '{}'.format(uid))

    def _construct_url(self, total_page):
        return [urljoin(self.host, '{}/{}'.format(self.uid, page))
                for page in range(1, total_page+1)]

    def crawl_watch(self, category, is_linux=True, initial_pages=16):
        if is_linux:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('headless')
            chrome_options.add_argument('user-agent={}'.format(get_ua()))
            chrome_options.add_argument('window-size=1920x1080')
            driver = webdriver.Chrome(options=chrome_options)
        else:
            driver = webdriver.Chrome(executable_path="C:/Program Files (x86)/Google/Chrome/Application/chromedriver")

        try:
            web = WebAlbum.objects.get(web=self.web, uid=self.uid)
            total_page = web.total_page if web.total_page else initial_pages
            urls = self._construct_url(total_page)
        except:
            urls = self._construct_url(initial_pages)
        for url in urls:
            driver.get(url)
            time.sleep(3)
            html = etree.HTML(driver.page_source)
            total_page = ''.join(html.xpath('//ul[@class="ivu-page"]//li[@class="ivu-page-next"]/preceding-sibling::li[1]/@title'))
            total_page = int(total_page) if total_page else 0
            album = self._album_pipeline(total_page)

            hrefs = html.xpath('//div[@class="photos-container"]//div[@class="photos-item"]//a[@class="photos-item-link"]/@href')
            for href in hrefs:
                try:
                    driver.get(href)
                    time.sleep(5)
                    html = etree.HTML(driver.page_source)
                    content = '' .join(html.xpath('//div[@class="textOmit title-content"]/text()'))
                    print('\033[96m 爬取商品；{} \033[0m'.format(content))
                    srcs = html.xpath('//div[@class="images-wrapper"]//img/@src')
                    images = '**'.join([src.replace('-zMin', '') for src in srcs if 'http://cdn' in src])
                    self._ps_pipeline(album, href, content, images, category)
                except:
                    continue

    def _album_pipeline(self, total_page):
        '''
        保存 WebAlbum
        '''
        web, created = WebAlbum.objects.get_or_create(
            web=self.web,
            uid=self.uid,
            defaults={'total_page': total_page}
        )
        if not created and total_page:
            web.total_page = total_page
            web.update_time = timezone.now()
            web.save()
        return web

    def _ps_pipeline(self, album, url, content, images, category):
        product, created = Product.objects.get_or_create(
            album=album,
            url=url,
            defaults = {
                'content': content,
                'images': images,
                'category': category
            })
        if not created:
            product.content = content
            product.images = images
            product.category = category
            product.save()



if __name__ == '__main__':
    # numbers = [(92097436, '手表'), (45458392, '包包')]
    items = [(45458392, '包包')]
    for item in items:
        number, category = item
        UooTu(number).crawl_watch(category)
