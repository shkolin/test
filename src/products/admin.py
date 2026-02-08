from django.contrib import admin

from products.models import Characteristic
from products.models import CharacteristicGroup
from products.models import Product
from products.models import ProductImage

admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(CharacteristicGroup)
admin.site.register(Characteristic)
