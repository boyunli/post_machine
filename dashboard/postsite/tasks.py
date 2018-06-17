import logging

from celery.decorators import task
from django.db.models import Q

from .models import Product, Account, Record
from poster.toutiao import TouTiao
from poster.weibo import WeiBo

logger = logging.getLogger('tieba')

@task(name="post_toutiao", bind=True)
def post_toutiao(self):
    '''
    今日头条
    '''
    accounts = Account.objects.filter(tieba__site='今日头条')\
        .values('id', 'account', 'password', 'display_name')
    for account in accounts:
        product = Product.objects.filter(~Q(images=''), is_posted=0)[0]
        status, memo = TouTiao(account['account'], product)\
            .main(account['account'], account['password'], account['display_name'])
        Record.save_to_record(account['id'], product.id, status, memo)

@task(name="post_weibo", bind=True)
def post_weibo(self):
    '''
    微博
    '''
    accounts = Account.objects.filter(tieba__site='微博')\
        .values('id', 'account', 'password', 'display_name', 'domain')
    for account in accounts:
        product = Product.objects.filter(~Q(images=''), is_posted=0)[0]
        status, memo = WeiBo(account['account'], product)\
            .main(account['account'], account['password'],
                  account['display_name'], account['domain'])
        Record.save_to_record(account['id'], product.id, status, memo)
