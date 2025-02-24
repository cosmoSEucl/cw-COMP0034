import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
from selenium.webdriver.remote.webdriver import WebDriver

# Import your Dash app instance
from app import df


@pytest.fixture(scope="session")
def dash_duo(request):
    """
    Create a WebDriver instance for testing.

    This fixture initializes a Chrome WebDriver with a specific window size,
    navigates to the local Dash application, and ensures the page is loaded
    before yielding the driver for tests. The driver is automatically closed
    after all tests are complete.

    Args:
        request: pytest request object

    Yields:
        WebDriver: Configured Chrome WebDriver instance
    """
    options = webdriver.ChromeOptions()
    options.add_argument('--window-size=1920,1080')
    driver = webdriver.Chrome(options=options)
    driver.get("http://localhost:8050")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    yield driver
    driver.quit()


def test_h1_heading_text(dash_duo: WebDriver):
    """
    Test the main heading of the application.

    Verifies that the H1 heading on the page contains the expected text
    'Grant Funding Analysis'.

    Args:
        dash_duo (WebDriver): Selenium WebDriver instance

    Raises:
        AssertionError: If the heading text doesn't match expected value
        TimeoutException: If H1 element is not found within timeout period
    """
    h1 = WebDriverWait(dash_duo, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "h1"))
    )
    h1_text = h1.text
    assert h1_text == "Grant Funding Analysis", "H1 heading text is incorrect"


def test_wordcloud_updates_on_department_selection(dash_duo: WebDriver):
    """
    Test the wordcloud component's response to department selection.

    Verifies that the wordcloud visualization updates when a different
    department is selected from the dropdown menu.

    Args:
        dash_duo (WebDriver): Selenium WebDriver instance

    Raises:
        TimeoutException: If elements are not found within timeout period
        AssertionError: If wordcloud doesn't update after selection change
    """
    dropdown = WebDriverWait(dash_duo, 10).until(
        EC.presence_of_element_located(
            (By.ID, "wordcloud-department-selector"))
    )
    dash_duo.execute_script("arguments[0].scrollIntoView(true);", dropdown)
    time.sleep(1)

    initial_wordcloud = WebDriverWait(dash_duo, 10).until(
        EC.presence_of_element_located((By.ID, "wordcloud"))
    ).get_attribute('src')

    dropdown.click()
    time.sleep(1)

    housing_and_land_option = WebDriverWait(dash_duo, 10).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//div[contains(@class,'Select-menu-outer')]//div[text()='Housing and Land']")
            )
    )
    housing_and_land_option.click()
    time.sleep(2)

    updated_wordcloud = dash_duo.find_element(
        By.ID, "wordcloud").get_attribute(
            'src')
    assert initial_wordcloud != updated_wordcloud


def test_interactive_timeline_updates_on_department_change(
        dash_duo: WebDriver):
    """
    Test the interactive timeline's response to department changes.

    Verifies that the interactive timeline component updates when a different
    department is selected from the dropdown menu.

    Args:
        dash_duo (WebDriver): Selenium WebDriver instance

    Raises:
        TimeoutException: If elements are not found within timeout period
        AssertionError: If timeline doesn't update after selection change
    """
    dropdown = WebDriverWait(dash_duo, 10).until(
        EC.presence_of_element_located((By.ID, "department-selector"))
    )
    dash_duo.execute_script("arguments[0].scrollIntoView(true);", dropdown)
    time.sleep(1)

    initial_timeline = dash_duo.find_element(
        By.ID, "interactive-timeline").get_attribute(
            'innerHTML')

    dropdown.click()
    time.sleep(1)

    housing_and_land_option = WebDriverWait(dash_duo, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'Select-menu-outer')]//div[text()='Housing and Land']"))
    )
    housing_and_land_option.click()
    time.sleep(2)

    updated_timeline = dash_duo.find_element(By.ID, "interactive-timeline").get_attribute('innerHTML')
    assert initial_timeline != updated_timeline


def test_timeline_chart_updates_on_dropdown_change(dash_duo: WebDriver):
    """
    Test the timeline chart's response to aggregation period changes.

    Verifies that the timeline chart updates when the aggregation period
    is changed in the dropdown menu (e.g., to Quarterly).

    Args:
        dash_duo (WebDriver): Selenium WebDriver instance

    Raises:
        TimeoutException: If elements are not found within timeout period
        AssertionError: If chart doesn't update after selection change
    """
    dropdown = WebDriverWait(dash_duo, 10).until(
        EC.presence_of_element_located((By.ID, "timeline-aggregation"))
    )

    initial_timeline = dash_duo.find_element(
        By.ID, "timeline-chart").get_attribute(
            'innerHTML')

    dash_duo.execute_script("arguments[0].scrollIntoView(true);", dropdown)
    time.sleep(1)
    dropdown.click()
    time.sleep(1)

    quarterly_option = WebDriverWait(dash_duo, 10).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//div[contains(@class, 'Select-menu-outer')]//div[text()='Quarterly']"))
    )
    quarterly_option.click()
    time.sleep(2)

    updated_timeline = dash_duo.find_element(
        By.ID, "timeline-chart").get_attribute(
            'innerHTML')

    assert initial_timeline != updated_timeline


def test_department_pie_chart_updates_on_slider_change(
        dash_duo: WebDriver):
    """
    Test the department pie chart's response to year slider changes.

    Verifies that the pie chart updates when a different year is selected
    using the slider control.

    Args:
        dash_duo (WebDriver): Selenium WebDriver instance

    Raises:
        TimeoutException: If elements are not found within timeout period
        AssertionError: If pie chart doesn't update after slider change
    """
    slider = WebDriverWait(dash_duo, 10).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "#department-year-slider .rc-slider"))
    )

    initial_pie_chart = WebDriverWait(dash_duo, 10).until(
        EC.presence_of_element_located((By.ID, "department-pie-chart"))
    ).get_attribute('innerHTML')

    dash_duo.execute_script("arguments[0].scrollIntoView(true);", slider)
    time.sleep(1)

    slider_width = slider.size['width']
    min_year = df['Award_Date'].dt.year.min()
    max_year = df['Award_Date'].dt.year.max()
    target_year = 2015

    relative_position = (target_year - min_year) / (max_year - min_year)
    x_offset = int(slider_width * relative_position)

    actions = ActionChains(dash_duo)
    actions.move_to_element_with_offset(slider, x_offset, 0).click().perform()

    time.sleep(2)

    updated_pie_chart = dash_duo.find_element(
        By.ID, "department-pie-chart").get_attribute(
            'innerHTML')
    assert initial_pie_chart != updated_pie_chart


def test_pie_chart_hover_updates_card(dash_duo: WebDriver):
    """
    Test the pie chart's hover interaction and card updates.

    Verifies that hovering over a pie chart segment displays an information
    card with the correct department and count data.

    Args:
        dash_duo (WebDriver): Selenium WebDriver instance

    Raises:
        TimeoutException: If elements are not found within timeout period
        AssertionError: If card data is incorrect or missing
    """
    pie_segment_selector = "path.surface"
    pie_segment = WebDriverWait(dash_duo, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, pie_segment_selector))
    )

    actions = ActionChains(dash_duo)
    actions.move_to_element(pie_segment).pause(0.5).perform()

    card_element = WebDriverWait(dash_duo, 10).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "text.nums"))
    )

    card_element_inner_text = card_element.get_attribute("data-unformatted")

    assert "Department=" in card_element_inner_text, "Department is incorrect"
    assert "Count=" in card_element_inner_text, "Count is incorrect"

# End of test_app.py
# End of Coursework 1
