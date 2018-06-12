from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

class WebSite(models.Model):
    web = models.CharField(_('网站'), max_length=20)
    uid = models.CharField(_('账号'), max_length=50)
    total_page = models.IntegerField(_('当前总页数'))
    update_time = models.DateTimeField(_('更新时间'), default=timezone.now)

    def __str__(self):
        return '%s' % (self.web)

    class Meta:
        unique_together = (('web', 'uid'), )
        verbose_name = verbose_name_plural = _('站点')
        db_table = 'postsite_web'


class Product(models.Model):
    '''
    存放爬取到的相册商品数据
    '''
    url = models.CharField(_('商品地址'), max_length=200, unique=True)
    content = models.CharField(_('描述'), max_length=800)
    images = models.CharField(_('图片'), max_length=800)
    is_posted = models.IntegerField(_('是否发过帖'), default=0)
    create_time = models.DateTimeField(_('创建时间'), default=timezone.now)
    update_time = models.DateTimeField(_('更新时间'), default=timezone.now)

    def __str__(self):
        return '%s:%s' % (self.url, self.is_posted)

    class Meta:
        verbose_name = verbose_name_plural = _('商品')
        db_table = 'postsite_product'


class Record(models.Model):
    '''
    发帖纪录
    '''
    DEFAULT_STATUS = 0
    SUCCEED_STATUS = 1
    FAILED_STATUS = 2
    POSTED_STATUS_CHOICES = (
        (DEFAULT_STATUS, _('正在发帖中...')),
        (SUCCEED_STATUS, _('发帖成功!')),
        (FAILED_STATUS, _('发帖失败!')),
    )

    product = models.ForeignKey(Product, verbose_name=_('Product'),
                              on_delete=models.CASCADE)
    site = models.CharField(_('发帖平台'), max_length=80)
    wechat = models.CharField(_('微信'), max_length=20)
    status = models.IntegerField(_('状态'), choices=POSTED_STATUS_CHOICES, default=0)
    memo = models.CharField(_('备注'),  max_length=200)
    published_times = models.IntegerField(_('发帖次数'), default=DEFAULT_STATUS)
    update_time = models.DateTimeField(_('更新时间'), default=timezone.now)

    def __str__(self):
        return '%s;%s;%s' \
            % (self.product, self.wechat, self.published_times)

    class Meta:
        unique_together = (('product', 'site'),)
        verbose_name = verbose_name_plural = _('发帖纪录')
        db_table = 'postsite_record'

    @classmethod
    def update_status(cls, product_id, site, status, memo):
        product = Product.objects.get(id=product_id)
        material = cls.objects.get(product=product, site=site)
        material.status = status
        material.memo = memo
        material.update_time = timezone.now()
        material.save()

    @staticmethod
    def save_to_materials(titles, wechat, product_id):
        for title in titles:
            update_time = timezone.now()
            product = Product.objects.get(id=product_id)
            material, created = Record.objects\
                .get_or_create(product=product, defaults = {
                    'wechat': wechat,
                    'published_times': 1,
                    'update_time': update_time,
                })
            if not created:
                material.wechat = wechat
                material.update_time = update_time
                published_times = Record.objects.filter(title=title)\
                .values('published_times')[0]['published_times']
                material.published_times =  published_times + 1
                material.save()
