from django.contrib import admin

from .models import Supplier, Inventory, Transaction

admin.site.site_header = 'Spentech Dashboard'
admin.site.register(Supplier)
admin.site.register(Inventory)
admin.site.register(Transaction)
