from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

class WebAlbum(models.Model):
    '''
    相册站点
    '''
    web = models.CharField(_('网站'), max_length=20)
    uid = models.CharField(_('账号'), max_length=50)
    total_page = models.IntegerField(_('当前总页数'))
    update_time = models.DateTimeField(_('更新时间'), default=timezone.now)

    def __str__(self):
        return '%s' % (self.web)

    class Meta:
        unique_together = (('web', 'uid'), )
        verbose_name = verbose_name_plural = _('相册')
        db_table = 'postsite_album'


class Product(models.Model):
    '''
    存放爬取到的相册商品数据
    '''
    album = models.ForeignKey(WebAlbum, verbose_name=_('相册'),
                              on_delete=models.CASCADE)
    url = models.CharField(_('商品地址'), max_length=200, unique=True)
    content = models.TextField(_('描述'))
    images = models.TextField(_('图片'))
    is_posted = models.IntegerField(_('是否发过帖'), default=0)
    category = models.CharField(_('类别'), max_length=10, default='手表')
    create_time = models.DateTimeField(_('创建时间'), default=timezone.now)
    update_time = models.DateTimeField(_('更新时间'), default=timezone.now)

    def __str__(self):
        return '%s:%s:%s' % (self.album, self.url, self.is_posted)

    class Meta:
        verbose_name = verbose_name_plural = _('商品')
        db_table = 'postsite_product'

    def update_status(self, is_posted):
        self.is_posted = is_posted
        self.update_time = timezone.now()
        self.save()


class Tieba(models.Model):
    '''
    贴吧
    '''
    site = models.CharField(_('站点'), max_length=30, unique=True)

    def __str__(self):
        return '%s' % (self.site)

    class Meta:
        verbose_name = verbose_name_plural = _('贴吧')
        db_table = 'postsite_tieba'


class Account(models.Model):
    '''
    发帖账号
    '''
    VALID_CHOICES = (
        (0, '无效'),
        (1, '有效'),
    )
    tieba = models.ForeignKey(Tieba, verbose_name=_('Tieba'),
                              on_delete=models.CASCADE)
    account = models.CharField(_('账号'), max_length=30)
    password = models.CharField(_('密码'), max_length=20)
    display_name = models.CharField(_('用户名'), max_length=30)
    domain = models.CharField(_('新浪域名'), max_length=30, null=True)
    mobile = models.CharField(_('手机号'), max_length=11)
    category = models.CharField(_('类别'), max_length=10, default='手表')
    is_valid = models.IntegerField(_('是否有效'), choices=VALID_CHOICES, default=1)
    create_time = models.DateTimeField(_('创建时间'), default=timezone.now)
    update_time = models.DateTimeField(_('更新时间'), default=timezone.now)

    def __str__(self):
        return '%s : %s' % (self.tieba, self.display_name)

    class Meta:
        unique_together = (('tieba', 'account'),)
        verbose_name = verbose_name_plural = _('发帖账号')
        db_table = 'postsite_account'


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

    account = models.ForeignKey(Account, verbose_name=_('Account'),
                              on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, verbose_name=_('Product'),
                              on_delete=models.CASCADE)
    status = models.IntegerField(_('状态'), choices=POSTED_STATUS_CHOICES, default=0)
    memo = models.CharField(_('备注'),  max_length=200)
    published_times = models.IntegerField(_('发帖次数'), default=DEFAULT_STATUS)
    update_time = models.DateTimeField(_('更新时间'), default=timezone.now)

    def __str__(self):
        return '%s;%s;%s' \
            % (self.account, self.product, self.published_times)

    class Meta:
        unique_together = (('product', 'account'),)
        verbose_name = verbose_name_plural = _('发帖纪录')
        db_table = 'postsite_record'

    @staticmethod
    def save_to_record(account_id, product_id, status, memo):
        update_time = timezone.now()
        account = Account.objects.get(id=account_id)
        product = Product.objects.get(id=product_id)
        material, created = Record.objects\
            .get_or_create(
                product=product,
                account=account,
                defaults = {
                    'status': status,
                    'memo': memo,
                    'published_times': 1,
                    'update_time': update_time,
            })
        if not created:
            material.status = status
            material.memo = memo
            material.update_time = update_time
            published_times = Record.objects.filter(account=account, product=product)\
            .values('published_times')[0]['published_times']
            material.published_times =  published_times + 1
            material.save()
