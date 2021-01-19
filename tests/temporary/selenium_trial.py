#%%-----------------------------------------------------------------------------
# Modules - requires install of Firefox webdrivers
# ------------------------------------------------------------------------------
import time
from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as dwait
from selenium.webdriver.support import expected_conditions as ec

# ------------------------------------------------------------------------------
# User-Facing Functions
# ------------------------------------------------------------------------------
def find_gym_times(username, password, target_time):

    # Login to dalplex
    driver = login_dalplex(username, password)

    # Click on gym buttom and sleep for 2 seconds
    gym_xpath  = '/html/body/div[6]/div[2]/div[2]/div/div[2]/div/div/div/'
    gym_xpath += 'div[25]/div/div[2]/div[1]/h4'
    gym_button = get_xelem(driver, gym_xpath)
    driver.execute_script("arguments[0].click()", gym_button)
    time.sleep(2)

    # Find scheduling cards
    cards_xpath = '//div[@class="caption program-schedule-card-caption"]'
    cards = driver.find_elements_by_xpath(cards_xpath)

    # Available times
    times, spots = parse_schedule_cards(cards)

    # TODO - continue here
    # Find closest availale time
    # deltas = [datetime.timedtarget_time - avail_time for avail_time in times]
    # deltas

    return(cards)


# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------
def get_xelem(driver, xpath, t = 10):
    ''' Returns element from x_path, waiting until it is present'''
    source = (By.XPATH, xpath)
    element = dwait(driver, t).until(ec.presence_of_element_located(source))
    return element


def login_dalplex(username, password):
    ''' Logs in to dalplex and returns firefox drivers '''

    # Specify xpaths to website objects
    lgl_xpath = '//*[@id="loginLink"]'
    usr_xpath = '//*[@id="txtUsername"]'
    psw_xpath = '//*[@id="txtPassword"]'
    lgb_xpath = '//*[@id="btnLogin"]'

    # Go to DalSports website
    driver = webdriver.Firefox()
    driver.get('https://www.dalsports.dal.ca/')

    # Click on "login" button, and sleep for 2 seconds
    lgn_button = get_xelem(driver, lgl_xpath)
    driver.execute_script("arguments[0].click()", lgn_button)
    time.sleep(2)
    
    # Insert username 
    usr_box = get_xelem(driver, usr_xpath)
    usr_box.send_keys(username)

    # Insert password
    psw_box = get_xelem(driver, psw_xpath)
    psw_box.send_keys(password)

    # Login and sleep for 10 seconds
    lgb_button = get_xelem(driver, lgb_xpath)
    driver.execute_script("arguments[0].click()", lgb_button)
    time.sleep(10)

    # Go to programs page
    programs_url  = 'https://www.dalsports.dal.ca/Program/GetProducts?'
    programs_url += 'classification=f22e8568-5cb8-464f-93f6-b390759240de'
    driver.get(programs_url)

    return driver


def parse_schedule_cards(cards):
    ''' Returns available times when given scheduling cards '''

    clean = lambda str_in : str_in.replace('\n','').replace('\t','')
    times, spots = [], []

    for card in cards:    
        # Initialize HTML parser
        html = card.get_attribute('innerHTML')
        soup = BeautifulSoup(html, 'html.parser')
        
        # Make sure there are available spots; continue to next card if not
        spots_txt = list(soup.small.span.small)[0]

        if spots_txt == 'No Spots Available':
            continue
        else:
            spots += [int(spots_txt.replace(' spot(s) available', ''))]

        # Get datetime of card
        date_txt = clean(list(soup.span )[0])
        time_txt = clean(list(soup.small)[0]).split(' to ')[0]
        times += [datetime.strptime(date_txt+time_txt, '%A, %B %d, %Y%I:%M %p')]

    return(times, spots)


# ------------------------------------------------------------------------------
# Example
# ------------------------------------------------------------------------------
username = 'lr495010'
password = 'Lala362636'
find_gym_times(username, password, None)

# %%
