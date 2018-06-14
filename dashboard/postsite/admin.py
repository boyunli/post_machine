from django.contrib import admin

from .models import WebSite, Product, Record

@admin.register(WebSite)
class WebSiteAdmin(admin.ModelAdmin):
    list_display = ('web', 'uid', 'total_page', 'update_time')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('website', 'url', 'is_posted', 'update_time')

admin.site.register(Record)
