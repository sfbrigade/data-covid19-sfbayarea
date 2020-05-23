#!/usr/bin/env python3
import requests
import urllib.request
from bs4 import BeautifulSoup
import json
import pandas as pd
from typing import List, Dict
from datetime import datetime, timedelta, timezone
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import re
import os


def get_notes() -> str:
    """Scrape notes and disclaimers from dashboards."""
    notes = ""
    driver = webdriver.Firefox()
    driver.implicitly_wait(30)
    url = 'https://public.tableau.com/profile/ca.open.data#!/vizhome/COVID-19PublicDashboard/Covid-19Public'
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    for p_tag in soup.find_all('p'):
        notes += p_tag.get_text().strip()
    return notes

if __name__ == '__main__':
    print(get_notes())
