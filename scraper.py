from os import environ
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

# hack to override sqlite database filename
# see: https://help.morph.io/t/using-python-3-with-morph-scraperwiki-fork/148
environ['SCRAPERWIKI_DATABASE_NAME'] = 'sqlite:///data.sqlite'
import scraperwiki


def wait_for_page_to_load(browser, url, css):
    browser.get('chrome://newtab')
    print('Waiting for page to load ... ' + url)
    browser.get(url)

    timeout = 60
    rate = 1

    timer = 0
    while True:
        if timer >= timeout:
            raise Exception('Timed out.')
        try:
            element = browser.find_element_by_css_selector(css)
            break
        except NoSuchElementException:
            print('Waiting for page to load ... ' + url)
            time.sleep(rate)
        timer += rate
    print('Page has loaded!')
    return element


def setup_browser():
    # path to chromedriver
    chromedriver_path = '/usr/local/bin/chromedriver'
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    browser = webdriver.Chrome(
        executable_path=chromedriver_path,
        chrome_options=chrome_options)
    return browser


languages = ['fr']
base_url = 'https://www.iso.org/obp/ui/'
table_css = 'table[class="grs-grid"]'

browser = setup_browser()
url = base_url + '#iso:pub:PUB500001:en'
table = wait_for_page_to_load(browser, url, table_css)

officially_assigned_code_elements_css = 'td[class="grs-status1"]'
officially_assigned = table.find_elements_by_css_selector(
    officially_assigned_code_elements_css)

exceptionally_reserved_code_elements_css = 'td[class="grs-status4"]'
exceptionally_reserved = table.find_elements_by_css_selector(
    exceptionally_reserved_code_elements_css)

countries = [{
    'code': cell.text,
    'name_en': cell.get_attribute('title'),
    'href': '#' + cell.find_element_by_tag_name('a').get_attribute('href').split('#')[1],
    'active': False,
} for cell in exceptionally_reserved]

countries += [{
    'code': cell.text,
    'name_en': cell.get_attribute('title'),
    'href': '#' + cell.find_element_by_tag_name('a').get_attribute('href').split('#')[1],
    'active': True,
} for cell in officially_assigned]

for country in countries:
    scraperwiki.sqlite.save(['code'], country, 'data')

for country in countries:
    el = 'div[class="core-view-summary"]'
    for language in languages:
        url = base_url + language + '/' + country['href']
        table = wait_for_page_to_load(browser, url, el)
        values = table.find_elements_by_css_selector(
            'div[class="core-view-line"] div[class="core-view-field-value"]')
        country['name_' + language] = values[2].text
    scraperwiki.sqlite.save(['code'], country, 'data')
