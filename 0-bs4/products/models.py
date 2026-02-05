import uuid
from django.db import models


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField()
    color = models.CharField()
    ssd = models.CharField()
    manufacturer = models.CharField()
    price = models.IntegerField()
    promo_price = models.IntegerField(null=True)
    code = models.CharField()
    num_reviews = models.IntegerField()
    screen_diagonal = models.FloatField()
    resolution = models.CharField()

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'products'


class ProductImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    url = models.CharField()

    def __str__(self):
        return self.url

    class Meta:
        db_table = 'product_images'


class CharacteristicGroup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField()

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'characteristic_groups'


class Characteristic(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(CharacteristicGroup, related_name='characteristics', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='characteristics', on_delete=models.CASCADE)
    name = models.CharField()
    value = models.CharField()

    def __str(self):
        return '%s: %s' % (self.name, self.value)

    class Meta:
        db_table = 'characteristics'
