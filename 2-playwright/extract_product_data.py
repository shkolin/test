import re
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from pprint import pprint
from typing import Any

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

SITE_URL = 'https://brain.com.ua/ukr/'
SEARCH_QUERY = 'Apple iPhone 15 128GB Black'


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


def get_page_content() -> str:
    with sync_playwright() as p:
        browser = p.firefox.launch()
        page = browser.new_page()
        page.goto(SITE_URL)

        search_input = page.wait_for_selector('div.header-bottom-in input.quick-search-input', timeout=10000)

        if search_input:
            search_input.fill(SEARCH_QUERY)

        page.click('div.header-bottom-in input.search-button-first-form')

        page.wait_for_selector(
            "(//div[@class='tab-content-wrapper']//div[@class='br-pp-imadds'])[1]//a",
            timeout=10000,
        )

        first_product = page.locator("(//div[@class='tab-content-wrapper']//div[@class='br-pp-imadds'])[1]//a").first
        first_product.scroll_into_view_if_needed()
        first_product.click()

        page.wait_for_selector("div[data-section='characteristics']", timeout=10000)

        page_source = page.content()
        browser.close()
        return page_source


def main() -> None:
    html_doc = get_page_content()
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
        images = soup.find('div', class_='product-block-bottom').find_all('img')
        product.images = [img.get('src') for img in images]
    except AttributeError:
        pass

    try:
        product.code = (
            soup.find('div', attrs={'data-section': 'top'})
            .find('div', id='product_code')
            .find('span', class_='br-pr-code-val')
            .text.strip()
        )
    except AttributeError:
        pass

    try:
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
        )
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

    pprint(asdict(product), width=119)


if __name__ == '__main__':
    main()
