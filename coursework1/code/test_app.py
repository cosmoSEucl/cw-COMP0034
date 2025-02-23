import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time
from selenium.webdriver.remote.webdriver import WebDriver

# Import your Dash app instance
from app import app, df

@pytest.fixture(scope="session")
def dash_duo(request):
    options = webdriver.ChromeOptions()
    options.add_argument('--window-size=1920,1080')  # Set larger window size
    driver = webdriver.Chrome(options=options)
    driver.get("http://localhost:8050")
    # Wait for the page to load completely
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    yield driver
    driver.quit()

def test_h1_heading_text(dash_duo: WebDriver):
    """
    GIVEN the app is running
    WHEN the home page is available
    THEN the H1 heading should have the text "Grant Funding Analysis"
    """
    # Wait for the H1 heading to be available on the page, timeout if this does not happen within 10 seconds
    h1 = WebDriverWait(dash_duo, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "h1"))
    )

    # Find the text content of the H1 heading element
    h1_text = h1.text

    # Assertion checks that the heading has the expected text
    assert h1_text == "Grant Funding Analysis", "H1 heading text is incorrect"

def test_wordcloud_updates_on_department_selection(dash_duo: WebDriver):
    # Wait for dropdown and scroll into view
    dropdown = WebDriverWait(dash_duo, 10).until(
        EC.presence_of_element_located((By.ID, "wordcloud-department-selector"))
    )
    dash_duo.execute_script("arguments[0].scrollIntoView(true);", dropdown)
    time.sleep(1)

    # Get initial wordcloud
    initial_wordcloud = WebDriverWait(dash_duo, 10).until(
        EC.presence_of_element_located((By.ID, "wordcloud"))
    ).get_attribute('src')

    # Click to open the dropdown
    dropdown.click()
    time.sleep(1)  # Wait for dropdown to open

    # Select "Housing and Land" from the dropdown options
    housing_and_land_option = WebDriverWait(dash_duo, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'Select-menu-outer')]//div[text()='Housing and Land']"))
    )
    housing_and_land_option.click()
    time.sleep(2)  # Wait for wordcloud to update

    updated_wordcloud = dash_duo.find_element(By.ID, "wordcloud").get_attribute('src')
    assert initial_wordcloud != updated_wordcloud


def test_interactive_timeline_updates_on_department_change(dash_duo: WebDriver):
    # Wait for dropdown and scroll into view
    dropdown = WebDriverWait(dash_duo, 10).until(
        EC.presence_of_element_located((By.ID, "department-selector"))
    )
    dash_duo.execute_script("arguments[0].scrollIntoView(true);", dropdown)
    time.sleep(1)

    # Get initial timeline state
    initial_timeline = dash_duo.find_element(By.ID, "interactive-timeline").get_attribute('innerHTML')

    # Click to open the dropdown
    dropdown.click()
    time.sleep(1)  # Wait for dropdown to open

    # Select "Housing and Land" from the dropdown options
    housing_and_land_option = WebDriverWait(dash_duo, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'Select-menu-outer')]//div[text()='Housing and Land']"))
    )
    housing_and_land_option.click()
    time.sleep(2)  # Wait for timeline to update

    updated_timeline = dash_duo.find_element(By.ID, "interactive-timeline").get_attribute('innerHTML')
    assert initial_timeline != updated_timeline


def test_timeline_chart_updates_on_dropdown_change(dash_duo: WebDriver):
    # First wait for the dropdown to be present and visible
    dropdown = WebDriverWait(dash_duo, 10).until(
        EC.presence_of_element_located((By.ID, "timeline-aggregation"))
    )

    # Get initial timeline state before any changes
    initial_timeline = dash_duo.find_element(By.ID, "timeline-chart").get_attribute('innerHTML')

    # Scroll the dropdown into view to ensure it's clickable
    dash_duo.execute_script("arguments[0].scrollIntoView(true);", dropdown)
    time.sleep(1)  # Wait for scroll to complete

    # Click to open the dropdown
    dropdown.click()
    time.sleep(1)  # Wait for dropdown to open

    # Dash creates a portal div for dropdown options, select "Quarterly" option
    quarterly_option = WebDriverWait(dash_duo, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'Select-menu-outer')]//div[text()='Quarterly']"))
    )
    quarterly_option.click()
    time.sleep(2)  # Wait for chart to update

    # Get the updated timeline state
    updated_timeline = dash_duo.find_element(By.ID, "timeline-chart").get_attribute('innerHTML')

    # Verify the chart has changed
    assert initial_timeline != updated_timeline

def test_department_pie_chart_updates_on_slider_change(dash_duo: WebDriver):
    # Wait for the slider to be present and visible
    slider = WebDriverWait(dash_duo, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#department-year-slider .rc-slider"))
    )

    # Get initial chart state
    initial_pie_chart = WebDriverWait(dash_duo, 10).until(
        EC.presence_of_element_located((By.ID, "department-pie-chart"))
    ).get_attribute('innerHTML')

    # Scroll the slider into view
    dash_duo.execute_script("arguments[0].scrollIntoView(true);", slider)
    time.sleep(1)

    # Calculate the approximate x-offset for the year 2015
    slider_width = slider.size['width']
    min_year = df['Award_Date'].dt.year.min()
    max_year = df['Award_Date'].dt.year.max()
    target_year = 2015

    # Calculate the relative position of the target year on the slider
    relative_position = (target_year - min_year) / (max_year - min_year)
    x_offset = int(slider_width * relative_position)

    # Move the mouse to the slider and click at the calculated offset
    actions = ActionChains(dash_duo)
    actions.move_to_element_with_offset(slider, x_offset, 0).click().perform()

    time.sleep(2)  # Wait for chart to update

    # Get updated chart
    updated_pie_chart = dash_duo.find_element(By.ID, "department-pie-chart").get_attribute('innerHTML')
    assert initial_pie_chart != updated_pie_chart