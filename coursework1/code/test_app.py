# test_app.py

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time

# Import your Dash app instance
from app import app
from app import df  # Import df to access in tests

@pytest.fixture(scope="session")
def dash_duo(request):
    driver = webdriver.Chrome()
    app_instance = app  # Access the Dash app instance from your module
    driver.get("http://localhost:8050")  # Adjust port if necessary
    yield driver
    driver.quit()

def test_app_title(dash_duo):
    assert dash_duo.title == "Grant Funding Analysis"

def test_initial_total_metrics(dash_duo):
    total_value = dash_duo.find_element(By.ID, "total-value")
    total_number = dash_duo.find_element(By.ID, "total-number")
    assert total_value.text != ""
    assert total_number.text != ""

def test_department_pie_chart_updates_on_slider_change(dash_duo):
    slider = dash_duo.find_element(By.CSS_SELECTOR, "#department-year-slider .rc-slider-handle")
    initial_pie_chart = dash_duo.find_element(By.ID, "department-pie-chart").get_attribute('innerHTML')
    dash_duo.execute_script("arguments[0].setAttribute('value', arguments[1])", slider, 2015)
    time.sleep(1)
    updated_pie_chart = dash_duo.find_element(By.ID, "department-pie-chart").get_attribute('innerHTML')
    assert initial_pie_chart != updated_pie_chart

def test_timeline_chart_updates_on_dropdown_change(dash_duo):
    dropdown = dash_duo.find_element(By.ID, "timeline-aggregation")
    initial_timeline = dash_duo.find_element(By.ID, "timeline-chart").get_attribute('innerHTML')
    dropdown.send_keys("Monthly")
    time.sleep(1)
    updated_timeline = dash_duo.find_element(By.ID, "timeline-chart").get_attribute('innerHTML')
    assert initial_timeline != updated_timeline

def test_wordcloud_updates_on_department_selection(dash_duo):
    dropdown = dash_duo.find_element(By.ID, "wordcloud-department-selector")
    initial_wordcloud = dash_duo.find_element(By.ID, "wordcloud").get_attribute('src')
    dropdown.send_keys("Communities and Intelligence")
    time.sleep(1)
    updated_wordcloud = dash_duo.find_element(By.ID, "wordcloud").get_attribute('src')
    assert initial_wordcloud != updated_wordcloud

def test_interactive_timeline_updates_on_department_change(dash_duo):
    dropdown = dash_duo.find_element(By.ID, "department-selector")
    initial_timeline = dash_duo.find_element(By.ID, "interactive-timeline").get_attribute('innerHTML')
    dropdown.send_keys("Education and Youth")
    time.sleep(1)
    updated_timeline = dash_duo.find_element(By.ID, "interactive-timeline").get_attribute('innerHTML')
    assert initial_timeline != updated_timeline

def test_top_grants_sunburst_updates_on_slider_change(dash_duo):
    slider = dash_duo.find_element(By.CSS_SELECTOR, "#top-n-slider .rc-slider-handle")
    initial_sunburst = dash_duo.find_element(By.ID, "top-grants-sunburst").get_attribute('innerHTML')
    dash_duo.execute_script("arguments[0].setAttribute('value', arguments[1])", slider, 15)
    time.sleep(1)
    updated_sunburst = dash_duo.find_element(By.ID, "top-grants-sunburst").get_attribute('innerHTML')
    assert initial_sunburst != updated_sunburst

def test_table_search_filters_data(dash_duo):
    search_input = dash_duo.find_element(By.ID, "table-search")
    search_input.send_keys('Education')
    time.sleep(1)
    table = dash_duo.find_element(By.ID, "department-table")
    assert 'Education' in table.text

def test_default_department_selector_value(dash_duo):
    dropdown = dash_duo.find_element(By.ID, "department-selector")
    selected_value = dropdown.get_attribute('value')
    assert selected_value == df['Funding_Org:Department'].iloc[0]

def test_table_row_count_after_search(dash_duo):
    search_input = dash_duo.find_element(By.ID, "table-search")
    search_input.send_keys('Education')
    time.sleep(1)
    table = dash_duo.find_element(By.ID, "department-table")
    table_rows = table.find_elements(By.TAG_NAME, 'tr')
    assert len(table_rows) >= 2
