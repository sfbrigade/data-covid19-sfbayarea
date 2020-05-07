
from selenium import webdriver
from bs4 import BeautifulSoup

browser = webdriver.Firefox()
browser.implicitly_wait(60)

NAPA_URL = "https://legacy.livestories.com/s/v2/coronavirus-report-for-napa-county-ca/9065d62d-f5a6-445f-b2a9-b7cf30b846dd/"

browser.get(NAPA_URL)

print(browser.find_element_by_tag_name("table").get_attribute('innerHTML'))

# html_source = browser.page_source
#
# soup = BeautifulSoup(html_source)
# print(soup.prettify())
