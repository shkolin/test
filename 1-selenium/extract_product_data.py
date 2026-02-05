import re
import time
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from pprint import pprint
from typing import Any

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import ElementNotInteractableException
from selenium.common import TimeoutException
from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

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


def click_element_safely(driver: Firefox, xpath: str) -> None:
    try:
        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        try:
            element.click()
        except ElementNotInteractableException:
            driver.execute_script('arguments[0].click();', element)
    except TimeoutException:
        print('Not found element or not clickable')
    except Exception as e:
        print(f'Error: {e}')


def get_page_content() -> str:
    driver = webdriver.Firefox()
    driver.get(SITE_URL)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//div[@class='header-bottom-in']//input[@class='quick-search-input']")
        )
    )

    search_input = driver.find_element(
        By.XPATH, "//div[@class='header-bottom-in']//input[@class='quick-search-input']"
    )
    search_input.send_keys(SEARCH_QUERY)
    search_button = driver.find_element(
        By.XPATH, "//div[@class='header-bottom-in']//input[@class='search-button-first-form']"
    )
    search_button.click()

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "(//div[@class='tab-content-wrapper']//div[@class='br-pp-imadds'])[1]//a")
        )
    )

    click_element_safely(driver, "(//div[@class='tab-content-wrapper']//div[@class='br-pp-imadds'])[1]//a")

    time.sleep(3)
    page_source = driver.page_source
    driver.quit()
    return page_source


def main() -> None:
    html_doc = get_page_content()
    soup = BeautifulSoup(html_doc, 'lxml')
    char_section = soup.find('div', attrs={'data-section': 'characteristics'})

    product = ProductData()

    try:
        # //div[@data-section='top']/h1
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

    pprint(asdict(product), width=119)


if __name__ == '__main__':
    main()
