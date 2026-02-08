import os
import re
import sys
from dataclasses import dataclass
from dataclasses import field


@dataclass
class ProductData:
    title: str | None = None
    color: str | None = None
    ssd: str | None = None
    manufacturer: str | None = None
    price: int | None = None
    promo_price: int | None = None
    images: list = field(default_factory=list)
    code: str | None = None
    num_reviews: int = 0
    screen_diagonal: float = 0.0
    resolution: str | None = None
    characteristics: dict = field(default_factory=dict)


def __init_django_project() -> None:
    import django

    sys.path.append(os.path.join(os.path.dirname(__file__)))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
    django.setup()


def __get_or_create_product(data: ProductData):
    from products.models import Product

    product, created = Product.objects.get_or_create(
        defaults={
            'title': data.title,
            'color': data.color,
            'ssd': data.ssd,
            'manufacturer': data.manufacturer,
            'price': data.price,
            'promo_price': data.promo_price,
            'code': data.code,
            'num_reviews': data.num_reviews,
            'screen_diagonal': data.screen_diagonal,
            'resolution': data.resolution,
        },
    )
    return product


def __save_images(product, image_urls: list) -> None:
    from products.models import ProductImage

    product.images.all().delete()
    ProductImage.objects.bulk_create([ProductImage(product=product, url=url) for url in image_urls])


def __save_characteristics(product, characteristics: dict) -> None:
    from products.models import Characteristic
    from products.models import CharacteristicGroup

    product.characteristics.all().delete()

    char_objects = []
    for group_name, chars in characteristics.items():
        group, _ = CharacteristicGroup.objects.get_or_create(name=group_name)
        for char_name, char_value in chars.items():
            char_objects.append(Characteristic(group=group, product=product, name=char_name, value=char_value))

    Characteristic.objects.bulk_create(char_objects)


def clean_value(value: str) -> str:
    value = value.replace('\xa0', ' ')
    value = re.sub(r'\s+', ' ', value)
    value = re.sub(r'\s*,\s*', ', ', value)
    return value.strip()


def save_product(data: ProductData) -> None:
    __init_django_project()

    from django.db import DatabaseError
    from django.db import IntegrityError
    from django.db import transaction

    try:
        with transaction.atomic():
            product = __get_or_create_product(data)
            __save_images(product, data.images)
            __save_characteristics(product, data.characteristics)
    except (IntegrityError, DatabaseError) as e:
        print(f'Failed to save product: {e}\n')


__all__ = [
    'clean_value',
    'save_product',
    'ProductData',
]
