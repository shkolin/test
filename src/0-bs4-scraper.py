from dataclasses import asdict
from pprint import pprint
from typing import Any

import requests
from bs4 import BeautifulSoup

from load_django import ProductData
from load_django import clean_value
from load_django import save_product

URL = 'https://brain.com.ua/ukr/Mobilniy_telefon_Apple_iPhone_16_Pro_Max_256GB_Black_Titanium-p1145443.html'

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


def get_page_content(url: str) -> str:
    response = requests.get(url, headers=headers)
    return response.text


def get_char_value(tag: Any, section_name: str, char_name: str) -> str | None:
    if char_header := tag.find('h3', string=section_name):
        if color_label := char_header.parent.find('span', string=char_name):
            return color_label.parent.find_all('span')[1].text.strip()
    return None


def main() -> None:
    html_doc = get_page_content(URL)
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
