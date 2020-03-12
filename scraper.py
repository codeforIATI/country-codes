from os import environ
import time

from splinter import Browser
from selenium.webdriver.chrome.options import Options

# hack to override sqlite database filename
# see: https://help.morph.io/t/using-python-3-with-morph-scraperwiki-fork/148
environ['SCRAPERWIKI_DATABASE_NAME'] = 'sqlite:///data.sqlite'
import scraperwiki


def wait_for_page_to_load(browser, url, css):
    browser.visit('chrome://newtab')
    print('Waiting for page to load ... ' + url)
    browser.visit(url)
    timeout = 60
    rate = 1
    timer = 0
    while True:
        if timer >= timeout:
            raise Exception('Timed out.')
        if browser.is_element_present_by_css(css):
            break
        print('Waiting for page to load ... ' + url)
        time.sleep(rate)
        timer += rate
    print('Page has loaded!')
    return browser.find_by_css(css).first


def setup_browser():
    chrome_options = Options()
    browser = Browser('chrome', headless=True, options=chrome_options)
    return browser


languages = ['fr']
base_url = 'https://www.iso.org/obp/ui/'
table_css = 'table[class="grs-grid"]'

browser = setup_browser()
url = base_url + '#iso:pub:PUB500001:en'
table = wait_for_page_to_load(browser, url, table_css)

officially_assigned_code_elements_css = 'td[class="grs-status1"]'
officially_assigned = table.find_by_css(
    officially_assigned_code_elements_css)

exceptionally_reserved_code_elements_css = 'td[class="grs-status4"]'
exceptionally_reserved = table.find_by_css(
    exceptionally_reserved_code_elements_css)

countries = [{
    'code': cell.text,
    'name_en': cell['title'].rstrip('*'),
    'href': '#' + cell.find_by_tag('a')['href'].split('#')[1],
    'active': False,
} for cell in exceptionally_reserved]

countries += [{
    'code': cell.text,
    'name_en': cell['title'].rstrip('*'),
    'href': '#' + cell.find_by_tag('a')['href'].split('#')[1],
    'active': True,
} for cell in officially_assigned]

for country in countries:
    el = 'div[class="core-view-summary"]'
    for language in languages:
        url = base_url + language + '/' + country['href']
        table = wait_for_page_to_load(browser, url, el)
        values = table.find_by_css(
            'div[class="core-view-line"] div[class="core-view-field-value"]')
        country['name_' + language] = values[2].text.rstrip('*')
        country['code_3_digit'] = values[4].text

for country in countries:
    scraperwiki.sqlite.save(['code'], country, 'data')
