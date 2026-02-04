from django.db import models


class Product(models.Model):
    id = models.UUIDField()
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


class Image(models.Model):
    id = models.UUIDField()
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE)
    url = models.CharField()

    def __str__(self):
        return self.url
