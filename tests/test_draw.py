import time

import pyautogui

from debug_scripts.paint import move_mouse, visualize_path_on_screenshot
import sys
from webdriver_click_functions.mouse import generate_cubic_bezier_curve, get_bezier_path
from webdriver_click_functions.easing import EASING_FUNCTIONS
import random

def test_draw(driver, button_box, input_box):
    # Example: Generate a spiral path
    for name, func in EASING_FUNCTIONS.items():
        pyautogui.moveTo(1000, 1000)
        start = pyautogui.position()
        target = button_box.center()
        control1, control2 = get_bezier_path(start, target)
        path = generate_cubic_bezier_curve(start, control1, control2, target, steps=100, easing_func=func)
        pyautogui.moveTo(target[0], target[1])
        time.sleep(0.1)
        visualize_path_on_screenshot(path, save_path=f'{name}.png')


