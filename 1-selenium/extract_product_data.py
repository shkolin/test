import re
from dataclasses import dataclass
from dataclasses import field
from selenium import webdriver
from selenium.webdriver.common.by import By
from typing import Any

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


def main() -> None:
    driver = webdriver.Firefox()
    driver.get(SITE_URL)
    search_input = driver.find_element(
        By.XPATH, "//div[@class='header-bottom-in']//input[@class='quick-search-input']"
    )
    search_input.send_keys(SEARCH_QUERY)
    search_button = driver.find_element(
        By.XPATH, "//div[@class='header-bottom-in']//input[@class='search-button-first-form']"
    )
    search_button.click()
    driver.quit()


if __name__ == '__main__':
    main()
