from django.contrib import admin

from products.models import Attribute
from products.models import AttributeGroup
from products.models import AttributeValue
from products.models import Product
from products.models import ProductImage

admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(AttributeGroup)
admin.site.register(Attribute)
admin.site.register(AttributeValue)
