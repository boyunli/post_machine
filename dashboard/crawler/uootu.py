# encoding:utf-8
import os
from urllib.parse import urljoin

from selenium import webdriver
from lxml import etree
from django.utils import timezone

from postsite.models import WebSite, Product
from utils.request_pkg import get_ua

BASE_DIR = \
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class UooTu:

    def __init__(self, uid):
        '''
        uid: 有图号
        '''
        self.web = '有图相册',
        self.uid = uid
        self.host = 'https://www.uootu.com'
        self.dir_path = os.path.join(BASE_DIR, '{}'.format(uid))

    def _construct_url(self, total_page):
        return [urljoin(self.host, '{}/{}'.format(self.uid, page))
                for page in range(1, total_page+1)]

    def crawl_watch(self, is_linux=True, initial_pages=16):
        if is_linux:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('headless')
            chrome_options.add_argument('user-agent={}'.format(get_ua()))
            chrome_options.add_argument('window-size=1920x1080')
            driver = webdriver.Chrome(options=chrome_options)
        else:
            driver = webdriver.Chrome(executable_path="C:/Program Files (x86)/Google/Chrome/Application/chromedriver")

        try:
            web = WebSite.objects.get(web=self.web, uid=self.uid)
            urls = self._construct_url(web.total_page)
        except:
            urls = self._construct_url(initial_pages)
        for url in urls:
            driver.get(url)
            html = etree.HTML(driver.page_source)
            total_page = ''.join(html.xpath('//ul[@class="ivu-page"]//li[@class="ivu-page-next"]/preceding-sibling::li[1]/@title'))
            site = self._web_pipeline(total_page)

            hrefs = html.xpath('//div[@class="photos-container"]//div[@class="photos-item"]//a[@class="photos-item-link"]/@href')
            for href in hrefs:
                driver.get(href)
                html = etree.HTML(driver.page_source)
                content = '' .join(html.xpath('//div[@class="textOmit title-content"]/text()'))
                images = '**'.join(html.xpath('//div[@class="images-wrapper"]//img/@src'))
                self._ps_pipeline(site, href, content, images)

    def _web_pipeline(self, total_page):
        '''
        保存 WebSite
        '''
        web, created = WebSite.objects.get_or_create(
            web=self.web,
            uid=self.uid,
            defaults={'total_page': total_page}
        )
        if not created and total_page:
            web.total_page = total_page
            web.update_time = timezone.now()
            web.save()
        return web

    def _ps_pipeline(self, website, url, content, images):
        product, created = Product.objects.get_or_create(
            site=website,
            url=url,
            defaults = {
                'content': content,
                'images': images
            })
        if not created:
            product.content = content
            product.images = images
            product.save()



if __name__ == '__main__':
    number = 92097436
    UooTu(number).crawl_watch()
