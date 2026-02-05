import re
import requests
from bs4 import BeautifulSoup
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from pprint import pprint
from typing import Any

URL = 'https://brain.com.ua/ukr/Mobilniy_telefon_Apple_iPhone_16_Pro_Max_256GB_Black_Titanium-p1145443.html'

# parsed_url_result = urlparse(URL)
# match_pid_results = re.search('p(\\d+)\\.html', parsed_url_result.path)
# product_id = int(match_pid_results.group(1)) if match_pid_results else None
# language = parsed_url_result.path.split('/')[1]
headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Referer': 'https://www.google.com/',
    'Connection': 'keep-alive',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'Upgrade-Insecure-Requests': '1',
    'DNT': '1',  # Do Not Track
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'TE': 'Trailers',  # Transfer Encoding
}


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


def get_page(url: str) -> str:
    response = requests.get(url, headers=headers)
    return response.text


def get_char_value(tag: Any, section_name: str, char_name: str) -> str | None:
    if char_header := tag.find('h3', string=section_name):
        if color_label := char_header.parent.find('span', string=char_name):
            return color_label.parent.find_all('span')[1].text.strip()
    return None


def clean_value(value: str) -> str:
    value = value.replace('\xa0', ' ')
    value = re.sub(r'\s+', ' ', value)
    value = re.sub(r'\s*,\s*', ', ', value)
    return value.strip()


def init_django_project() -> None:
    import django
    import os
    import sys

    sys.path.append(os.path.join(os.path.dirname(__file__), 'www'))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
    django.setup()


def save_product(data: ProductData) -> None:
    init_django_project()
    from django.db import DatabaseError
    from django.db import transaction
    from products.models import Characteristic
    from products.models import CharacteristicGroup
    from products.models import Product
    from products.models import ProductImage

    try:
        with transaction.atomic():
            product, _ = Product.objects.update_or_create(
                **{
                    'title': data.title,
                    'color': data.code,
                    'ssd': data.ssd,
                    'manufacturer': data.manufacturer,
                    'price': data.price,
                    'promo_price': data.promo_price,
                    'code': data.code,
                    'num_reviews': data.num_reviews,
                    'screen_diagonal': data.screen_diagonal,
                    'resolution': data.resolution,
                }
            )

            product.images.all().delete()

            ProductImage.objects.bulk_create(
                [
                    ProductImage(
                        product=product,
                        url=image_url,
                    )
                    for image_url in data.images
                ]
            )

            for group_name, characteristics in data.characteristics.items():
                group, _ = CharacteristicGroup.objects.get_or_create(name=group_name)
                for char_name, char_value in characteristics.items():
                    Characteristic.objects.get_or_create(
                        group=group,
                        product=product,
                        name=char_name,
                        value=char_value,
                    )
    except DatabaseError as e:
        print(f'Failed to save product: {e}\n')


def main() -> None:
    html_doc = get_page(URL)
    soup = BeautifulSoup(html_doc, 'lxml')
    char_section = soup.find('div', attrs={'data-section': 'characteristics'})

    product = ProductData()

    try:
        product.title = soup.find('div', attrs={'data-section': 'top'}).find('h1').text.strip()
    except AttributeError:
        pass

    try:
        product.color = get_char_value(char_section, 'Фізичні характеристики', 'Колір')
    except AttributeError:
        pass

    try:
        product.ssd = get_char_value(char_section, "Функції пам'яті", "Вбудована пам'ять")
    except AttributeError:
        pass

    try:
        product.manufacturer = get_char_value(char_section, 'Інші', 'Виробник')
    except AttributeError:
        pass

    try:
        # //div[@class='br-pr-price main-price-block']//div[@class='price-wrapper']/span
        product.price = int(
            soup.find('div', class_='br-pr-price main-price-block')
            .find('div', class_='price-wrapper')
            .find('span')
            .text.strip()
            .replace(' ', '')
        )
    except AttributeError:
        pass

    try:
        # //div[@class='product-block-bottom']//img
        images = soup.find('div', class_='product-block-bottom').find_all('img')
        product.images = [img.get('src') for img in images]  # TODO: select only large size
    except AttributeError:
        pass

    try:
        # //div[@data-section='top']//div[@id='product_code']//span[@class='br-pr-code-val']
        product.code = (
            soup.find('div', attrs={'data-section': 'top'})
            .find('div', id='product_code')
            .find('span', class_='br-pr-code-val')
            .text.strip()
        )
    except AttributeError:
        pass

    try:
        # //div[@id='fast-navigation-block-static']//a[@class='scroll-to-element reviews-count']/span
        product.num_reviews = int(
            soup.find('div', id='fast-navigation-block-static')
            .find('a', class_='scroll-to-element reviews-count')
            .find('span')
            .text.strip()
        )
    except AttributeError:
        pass

    try:
        product.screen_diagonal = float(
            str(get_char_value(char_section, 'Дисплей', 'Діагональ екрану')).replace('"', '')
        )
    except AttributeError:
        pass

    try:
        product.resolution = str(get_char_value(char_section, 'Дисплей', 'Роздільна здатність екрану')).replace(
            ' ', ''
        )  # TODO: maybe separate to list integers: [int, int]
    except AttributeError:
        pass

    try:
        for item in char_section.find_all('div', class_='br-pr-chr-item'):
            title = item.find('h3').text.strip()
            product.characteristics[title] = {}
            chars = item.find('div').find_all('div')
            for char in chars:
                char_name, char_value = char.find_all('span')
                product.characteristics[title][char_name.text.strip()] = clean_value(char_value.text)
    except AttributeError:
        pass

    save_product(product)

    pprint(asdict(product), width=119)


if __name__ == '__main__':
    main()
