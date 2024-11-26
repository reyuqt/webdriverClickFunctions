import time

from selenium import webdriver
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import os
from webdriver_click_functions.selenium_click import get_element, click_this_element, save_element


@pytest.fixture(scope="module")
def driver():
    driver = webdriver.Chrome()
    driver.get(f"file://{os.getcwd()}/test.html")
    yield driver
    driver.quit()


def test_get_element(driver):
    button = get_element(driver, (By.ID, 'test-button-1'))
    assert button is not None

def test_save_element(driver):
    selectors_to_test = [(By.ID, 'test-button-1')]
    for selector in selectors_to_test:
        element = driver.find_element(*selector)
        file_path = save_element(element, name='test-button-1')
        assert 'test-button-1' in file_path

def test_click_this_element(driver):
    selectors_to_test = [(By.ID, 'test-button-1')]
    for selector in selectors_to_test:
        clicked = click_this_element(driver, selector=selector,
                                     confidence=0.8,
                                     retries=3,
                                     x_reduction=0.2,
                                     y_reduction=0.2,
                                     duration_range=(1, 3),
                                     )
        last_clicked = driver.execute_script("return window.lastClickedElement;")

        assert clicked
        assert last_clicked == selector[1]
