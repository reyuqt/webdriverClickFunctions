import os
import tempfile
import time
from typing import Union, Tuple, Optional, Callable, Dict
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
import selenium.webdriver.support.expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException,
    StaleElementReferenceException,
)

from webdriver_click_functions.mouse import click_image
from webdriver_click_functions.utils import get_logger
from webdriver_click_functions.screen import locate_image
from webdriver_click_functions.selenium.confirm import Clicked
from webdriver_click_functions.easing import linear

logger = get_logger("selenium_click")


# Custom Exceptions
class ElementNotFoundError(Exception):
    """Exception raised when a WebElement is not found within the specified timeout."""
    pass

def outline_element(driver: WebDriver, selector: Union[tuple[str, str], WebElement], border_color: str = 'red',
                    border_width: str = '2px'):
    """ adds a border to an element, I found this super useful when locating elements that were just text (think radio options),
    but this introduces possibly being detected by dom observations ( akamai cloudflare )"""
    if isinstance(selector, tuple):
        logger.debug(f'Resolving selector tuple: {selector}')
        element = driver.find_element(*selector)
    else:
        element = selector
    driver.execute_script(
        f"arguments[0].style.border='{border_width} solid {border_color}';", element
    )

def scroll_to_element(driver: WebDriver, selector: Union[tuple[str, str], WebElement]):
    """ @TODO handle elements that arent on screen yet """
    pass


def get_element(
        driver: WebDriver,
        selector: Union[Tuple[str, str], WebElement],
        timeout: int = 10
) -> WebElement:
    """
    Helper function to resolve a WebElement or locate it using a selector tuple.
    If a selector tuple is provided, WebDriverWait is used to find the element.

    Args:
        driver (WebDriver): The Selenium WebDriver instance.
        selector (Union[Tuple[str, str], WebElement]): A tuple of (By, locator) or an existing WebElement.
        timeout (int, optional): Maximum time to wait for the element. Defaults to 10 seconds.

    Returns:
        WebElement: The located WebElement.

    Raises:
        ValueError: If the selector type is neither a tuple nor a WebElement.
        ElementNotFoundError: Custom exception if the element is not found within the timeout.
        ElementNotInteractableError: Custom exception if the element is found but not interactable.
    """
    try:
        if isinstance(selector, tuple):
            logger.debug(f"Resolving selector tuple: {selector}")
            element = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable(selector)
            )
            logger.info(f"Element found using selector: {selector}")
            return element
        elif isinstance(selector, WebElement):
            logger.debug("Selector is already a WebElement.")
            # Optionally, you can verify if the element is still attached to the DOM
            if not selector.is_displayed():
                logger.warning("WebElement is not visible.")
                raise ElementNotInteractableException("WebElement is not visible.")
            return selector
        else:
            logger.error("Selector must be a tuple or a WebElement.")
            raise ValueError("Selector must be a tuple of (By, locator) or a WebElement instance.")

    except TimeoutException:
        logger.error(f"Timeout: Element with selector {selector} not found within {timeout} seconds.")
        raise ElementNotFoundError(f"Element with selector {selector} not found within {timeout} seconds.")

    except NoSuchElementException:
        logger.error(f"No such element: {selector}")
        raise ElementNotFoundError(f"No such element: {selector}")

    except ElementNotInteractableException as e:
        logger.error(f"Element not interactable: {selector}. Exception: {e}")
        raise ElementNotInteractableException(f"Element not interactable: {selector}. Exception: {e}")

    except StaleElementReferenceException as e:
        logger.error(f"Stale element reference: {selector}. Exception: {e}")
        raise ElementNotFoundError(f"Stale element reference: {selector}. Exception: {e}")

    except Exception as e:
        logger.exception(f"An unexpected error occurred while getting the element: {selector}. Exception: {e}")
        raise e





def save_element(element: WebElement, name: Optional[str] = None) -> str:
    """
    Save a screenshot of a WebElement.

    Parameters:
    element (WebElement): The web element to capture.
    name (Optional[str]): The name of the file to save the screenshot. If not provided, a temporary file will be used.

    Returns:
    str: The full path of the saved screenshot.

    Raises:
    Exception: If the screenshot could not be saved.
    """
    # If a name is provided, save the screenshot with the specific name
    if name is not None:
        filepath = os.path.join(os.getcwd(), f'{name}.png')
        saved = element.screenshot(filepath)
        time.sleep(0.5)  # Allow rendering to stabilize
        if saved:
            logger.info("Saved element to filepath: %s", filepath)
            return filepath

    # Use a temporary file to save the screenshot if no name is provided
    with tempfile.NamedTemporaryFile(suffix=".png", dir='.', delete=False, delete_on_close=False) as temp_file:
        temp_file_path = temp_file.name
        element.screenshot(temp_file_path)
        time.sleep(0.5)  # Allow rendering to stabilize
        logger.info("Saved element as temporary image: %s", temp_file_path)
        # Check if the screenshot was successfully saved
        if not os.path.exists(temp_file_path) or not os.path.getsize(temp_file_path):
            logger.error("Failed to save element screenshot at %s", temp_file_path)
            raise Exception(f"Failed to save element screenshot: {temp_file_path}")

        return temp_file_path


def click_this_element(
        driver: Optional[WebDriver],
        selector: Union[tuple[str, str], WebElement],
        confidence: float = 0.8,
        retries: int = 3,
        x_reduction: float = 0.2,
        y_reduction: float = 0.2,
        duration_range: Tuple[float, float] = (1, 3),
        steps_range: Tuple[int, int] = (150, 300),
        perform_test: Optional[Callable] = Clicked.default,
        test_kwargs: Optional[Dict] = None,
        easing_func: Callable[[float], float] = linear
) -> bool:
    """
    Locate an element, save it as a temporary image, and click it using our utility function.
    """
    try:
        element = get_element(driver, selector)
        logger.info(f"Located Selenium element: {selector}")

        file_path = save_element(element, 'element_1')

        success = click_image(
            image_path=file_path,
            confidence=confidence,
            retries=retries,
            x_reduction=x_reduction,
            y_reduction=y_reduction,
            duration_range=duration_range,
            steps_range=steps_range,
            easing_func=easing_func
        )

        os.remove(file_path)
        logger.info(f"Temporary image file '{file_path}' deleted.")
        if perform_test is None:
            return success
        else:
            test_kwargs = test_kwargs or {}
            return perform_test(driver, element, **test_kwargs)

    except Exception as e:
        logger.exception(f"Error in clicking element '{selector}': {e}")
        return False


def click_inside_this_element(driver: Optional[WebDriver],
                              selector_outer: Union[tuple[str, str], WebElement],
                              selector_inner: Union[tuple[str, str], WebElement],
                              confidence: float = 0.8,
                              retries: int = 3,
                              x_reduction: float = 0.2,
                              y_reduction: float = 0.2,
                              duration_range: Tuple[float, float] = (1, 3),
                              steps_range: Tuple[int, int] = (150, 300),
                              perform_test: Optional[Callable] = Clicked.default,
                              test_kwargs: Optional[Dict] = None,
                              easing_func: Callable[[float], float] = linear
                              ):
    """
    Locate an outer_element, then locate an element inside of outer_element and click it using our mouse function.
    @TODO I think this could be 1 function with click_this_element, but I haven't decided how I would structure both together.
    """
    try:
        outer_element = get_element(driver, selector_outer)
        inner_element = get_element(driver, selector_inner)
        logger.info(f"Located Outer Selenium element: {selector_outer}")
        if outer_element.find_element(*selector_inner) is None:
            logger.critical(f'{selector_inner} not found inside {selector_outer}')
            return False
        outer_element_file_path = save_element(outer_element, 'element_1')
        outer_element_location = locate_image(outer_element_file_path)
        inner_element_file_path = save_element(inner_element, 'element_2')

        success = click_image(
            image_path=inner_element_file_path,
            region=outer_element_location,
            confidence=confidence,
            retries=retries,
            x_reduction=x_reduction,
            y_reduction=y_reduction,
            duration_range=duration_range,
            steps_range=steps_range,
            easing_func=easing_func
        )

        os.remove(outer_element_file_path)
        logger.info(f"Temporary image file '{outer_element_file_path}' deleted.")
        os.remove(inner_element_file_path)
        logger.info(f"Temporary image file '{inner_element_file_path}' deleted.")
        if perform_test is None:
            return success
        else:
            test_kwargs = test_kwargs or {}
            return perform_test(driver, inner_element, **test_kwargs)

    except Exception as e:
        logger.exception(f"Error in clicking element '{selector_inner}' inside '{selector_outer}': {e}")
        return False
