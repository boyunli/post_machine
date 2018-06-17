from django.contrib import admin

from .models import Product, Account, Record, Tieba

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('album', 'url', 'is_posted', 'update_time')

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('tieba', 'display_name', 'update_time')

@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    list_display = ('account', 'product', 'status',
                    'published_times', 'update_time')

admin.site.register(Tieba)
