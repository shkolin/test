import time
from contextlib import contextmanager
from dataclasses import asdict
from pprint import pprint
from typing import Generator

from selenium import webdriver
from selenium.common import ElementNotInteractableException
from selenium.common import NoSuchElementException
from selenium.common import TimeoutException
from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from load_django import ProductData
from load_django import clean_value
from load_django import save_product

SITE_URL = 'https://brain.com.ua/ukr/'
SEARCH_QUERY = 'Apple iPhone 15 128GB Black'


def get_char_value(tag: WebElement, section_name: str, char_name: str) -> str | None:
    if char_header := tag.find_element(By.XPATH, f'//h3[text()="{section_name}"]'):
        if color_label := char_header.find_element(By.XPATH, f'./following-sibling::div//span[text()="{char_name}"]'):
            parent_div = color_label.find_element(By.XPATH, './..')
            spans = parent_div.find_elements(By.TAG_NAME, 'span')
            if value := spans[1].get_attribute('textContent'):
                return value.strip()
    return None


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


@contextmanager
def get_page_content() -> Generator[WebDriver]:
    driver = webdriver.Firefox()
    driver.get(SITE_URL)
    try:
        search_input = driver.find_element(
            By.XPATH, "//div[@class='header-bottom-in']//input[@class='quick-search-input']"
        )
        search_input.send_keys(SEARCH_QUERY)
        search_button = driver.find_element(
            By.XPATH, "//div[@class='header-bottom-in']//input[@class='search-button-first-form']"
        )
        search_button.click()

        WebDriverWait(driver, 3).until(
            lambda d: d.find_element(
                By.XPATH, "(//div[@class='tab-content-wrapper']//div[@class='br-pp-imadds'])[1]//a"
            )
        )

        click_element_safely(driver, "(//div[@class='tab-content-wrapper']//div[@class='br-pp-imadds'])[1]//a")

        time.sleep(3)

        yield driver
    finally:
        driver.quit()


def main() -> None:
    product = ProductData()
    with get_page_content() as browser:
        try:
            char_section: WebElement | None = browser.find_element(By.XPATH, "//div[@data-section='characteristics']")
        except NoSuchElementException:
            char_section = None

        try:
            if title := browser.find_element(By.XPATH, "//div[@data-section='top']/h1").get_attribute('textContent'):
                product.title = title.strip()
        except NoSuchElementException:
            pass

        try:
            if char_section:
                if color := get_char_value(char_section, 'Фізичні характеристики', 'Колір'):
                    product.color = color.strip()
        except NoSuchElementException:
            pass

        try:
            if char_section:
                if ssd := get_char_value(char_section, "Функції пам'яті", "Вбудована пам'ять"):
                    product.ssd = ssd.strip()
        except NoSuchElementException:
            pass

        try:
            if char_section:
                if manufacturer := get_char_value(char_section, 'Інші', 'Виробник'):
                    product.manufacturer = manufacturer.strip()
        except NoSuchElementException:
            pass

        try:
            if price := browser.find_element(
                By.XPATH, "//div[@class='br-pr-price main-price-block']//div[@class='price-wrapper']/span"
            ).get_attribute('textContent'):
                product.price = int(price.strip().replace(' ', ''))
        except NoSuchElementException:
            pass

        try:
            images = browser.find_elements(By.XPATH, "//div[@class='product-block-bottom']//img")
            product.images = [img.get_attribute('src') for img in images]
        except NoSuchElementException:
            pass

        try:
            if code := browser.find_element(
                By.XPATH, "//div[@data-section='top']//div[@id='product_code']//span[@class='br-pr-code-val']"
            ).get_attribute('textContent'):
                product.code = code.strip()
        except NoSuchElementException:
            pass

        try:
            if num_reviews := browser.find_element(
                By.XPATH, "//div[@id='fast-navigation-block-static']//a[@class='scroll-to-element reviews-count']/span"
            ).get_attribute('textContent'):
                product.num_reviews = int(num_reviews.strip())
        except NoSuchElementException:
            pass

        try:
            if char_section:
                if screen_diagonal := get_char_value(char_section, 'Дисплей', 'Діагональ екрану'):
                    product.screen_diagonal = float(screen_diagonal.strip().replace('"', ''))
        except NoSuchElementException:
            pass

        try:
            if char_section:
                if resolution := get_char_value(char_section, 'Дисплей', 'Роздільна здатність екрану'):
                    product.resolution = resolution.strip().replace(' ', '')
        except NoSuchElementException:
            pass

        if char_section:
            try:
                for item in char_section.find_elements(By.XPATH, "//div[@class='br-pr-chr-item']"):
                    if title := item.find_element(By.TAG_NAME, 'h3').get_attribute('textContent'):
                        product.characteristics[title.strip()] = {}
                        chars = item.find_element(By.TAG_NAME, 'div').find_elements(By.TAG_NAME, 'div')
                        for char in chars:
                            char_name, char_value = char.find_elements(By.TAG_NAME, 'span')
                            attr_name = char_name.get_attribute('textContent')
                            attr_value = char_value.get_attribute('textContent')
                            if attr_name and attr_value:
                                product.characteristics[title.strip()][attr_name.strip()] = clean_value(
                                    attr_value.strip()
                                )
            except NoSuchElementException:
                pass

    save_product(product)

    pprint(asdict(product), width=119)


if __name__ == '__main__':
    main()
