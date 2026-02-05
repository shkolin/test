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
        browser.close()


def main() -> None:
    pass


if __name__ == '__main__':
    main()
