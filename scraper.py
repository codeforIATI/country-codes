import os
import csv

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import StaleElementReferenceException

# hack to override sqlite database filename
# see: https://help.morph.io/t/using-python-3-with-morph-scraperwiki-fork/148
os.environ['SCRAPERWIKI_DATABASE_NAME'] = 'sqlite:///data.sqlite'
import scraperwiki


def setup_browser():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    browser = webdriver.Chrome(options=chrome_options)
    return browser


def load_page(browser, url):
    print('Waiting for page to load ... ' + url)
    browser.delete_all_cookies()
    browser.get('chrome://newtab')
    browser.get(url)


def find_elements(browser, css):
    WebDriverWait(browser, 10).until(
        expected_conditions.presence_of_element_located((By.CSS_SELECTOR, css))
    )
    return browser.find_elements(By.CSS_SELECTOR, css)


languages = ['fr']
base_url = 'https://www.iso.org/obp/ui/'

browser = setup_browser()
url = base_url + '#iso:pub:PUB500001:en'

load_page(browser, url)
for x in range(10):
    try:
        exceptionally_reserved_code_elements_css = 'table[class="grs-grid"] td[class="grs-status4"]'
        exceptionally_reserved = find_elements(
            browser,
            exceptionally_reserved_code_elements_css)
        countries = [{
            'code': cell.text,
            'name_en': cell.get_attribute('title').rstrip('*'),
            'href': '#' + cell.find_element(By.TAG_NAME, 'a').get_attribute('href').split('#')[1],
            'active': False,
        } for cell in exceptionally_reserved]
        break
    except StaleElementReferenceException:
        print("Retrying ...")
else:
    raise Exception("Giving up")

for x in range(10):
    try:
        officially_assigned_code_elements_css = 'table[class="grs-grid"] td[class="grs-status1"]'
        officially_assigned = find_elements(
            browser,
            officially_assigned_code_elements_css)
        countries += [{
            'code': cell.text,
            'name_en': cell.get_attribute('title').rstrip('*'),
            'href': '#' + cell.find_element(By.TAG_NAME, 'a').get_attribute('href').split('#')[1],
            'active': True,
        } for cell in officially_assigned]
        break
    except StaleElementReferenceException:
        print("Retrying ...")
else:
    raise Exception("Giving up")

for country in countries:
    el = 'div[class="core-view-summary"] div[class="core-view-line"] div[class="core-view-field-value"]'
    for language in languages:
        url = base_url + language + '/' + country['href']
        load_page(browser, url)
        for x in range(10):
            try:
                values = find_elements(browser, el)
                country['name_' + language] = values[2].text.rstrip('*')
                country['code_3_digit'] = values[4].text
                break
            except StaleElementReferenceException:
                print("Retrying ...")
        else:
            raise Exception("Giving up")

os.makedirs("output", exist_ok=True)
with open(os.path.join("output", "country_codes.csv"), 'w') as csv_f:
    csvwriter = csv.DictWriter(csv_f, fieldnames=countries[0].keys())
    csvwriter.writeheader()
    for country in countries:
        csvwriter.writerow(country)
        if os.environ.get("GITHUB_PAGES", False) is False:
            scraperwiki.sqlite.save(['code'], country, 'data')
print("Done.")
