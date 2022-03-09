## All the external libraries
import re
import csv
from getpass import getpass
from time import sleep
import random
import datetime as dt
from datetime import datetime
import signal

from contextlib import contextmanager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
#from msedge.selenium_tools import Edge, EdgeOptions
from selenium.webdriver import Chrome


####### All the functions #######

## Get random time offset
def get_rand_offset(t=4):
    r = random.randint(0, t)
    r += random.random()
    return r

##create a handler to not scrap a page for more than a certain time
def signal_handler(signum, frame):
    raise Exception("Timed out!")


#### Get the browser
## Return <class 'selenium.webdriver.chrome.webdriver.WebDriver'>
## Opens an empty browser
def get_driver():
    if driver == None:
        return webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    else:
        return driver

## Go to address
def visit_site(site="https://www.google.com"):
    driver.get(site)

    
## Add tweets to file
def write_to_file(fname, data):
    f = open(fname, "a+")
    strDummy=''
    for tupl in data:
        strDummy=strDummy+str(tupl)+'\n'
    f.write(strDummy)
    f.close()

## Get n tweets
def get_ntweets(num_tweets=100):
    data = []
    tweet_ids = set()
    last_position = driver.execute_script("return window.pageYOffset;")
    scrolling = True

    while scrolling:
        page_cards = []
        while len(page_cards) < 1:
            page_cards = driver.find_elements_by_xpath('//article[@data-testid="tweet"]')

        min_tweets = -1*min(len(page_cards), 15)

        for card in page_cards[min_tweets:]:
            tweet = get_tweet_data(card)
            if tweet:
                tweet_id = ''.join(tweet)
                if tweet_id not in tweet_ids:
                    tweet_ids.add(tweet_id)
                    if len(data) == num_tweets:
                        scrolling = False
                        break
                    data.append(tweet)

        scroll_attempt = 0
        while True:
            # check scroll position
            driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            sleep(1+get_rand_offset(2))
            curr_position = driver.execute_script("return window.pageYOffset;")
            if last_position == curr_position:
                scroll_attempt += 1

                # end of scroll region
                if scroll_attempt >= 3:
                    scrolling = False
                    break
                else:
                    sleep(1+get_rand_offset(2)) # attempt another scroll
            else:
                last_position = curr_position
                break
    return data
    
##get the date for the next day
def nextDay(date):
    end_date = date + dt.timedelta(days=1)
    return end_date

## Get specific day tweets
def get_specific_date_tweets(search_term, date, num_tweets, filename):
    #'https://twitter.com/search?f=live&q=(%23Covid19)%20lang%3Aen%20until%3A2020-05-02%20since%3A2020-05-01&src=typed_query')
    url_to_visit = 'https://twitter.com/search?f=live&q=(%23'+search_term+')%20lang%3Aen%20until%3A'+(nextDay(date)).strftime('%Y-%m-%d')+'%20since%3A'+date.strftime('%Y-%m-%d')+'&src=typed_query'
    print(url_to_visit)
    visit_site(site=url_to_visit)
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(60)   # Sixty seconds
    try:
        tweets = get_ntweets(num_tweets=num_tweets)
    except Exception:
        tweets=False
        print("Timed out!")
    if(tweets):
        write_to_file(fname=filename, data=tweets)
    pass

    

## Description
## Takes
## Returns
def get_tweet_data(card):
    """Extract data from tweet card"""
    username = card.find_element_by_xpath('.//span').text
    try:
        handle = card.find_element_by_xpath('.//span[contains(text(), "@")]').text
    except NoSuchElementException:
        return
    
    try:
        postdate = card.find_element_by_xpath('.//time').get_attribute('datetime')
    except NoSuchElementException:
        return
    
    comment = card.find_element_by_xpath('.//div[2]/div[2]/div[1]').text
    responding = card.find_element_by_xpath('.//div[2]/div[2]/div[2]').text
    text = comment + responding
    reply_cnt = card.find_element_by_xpath('.//div[@data-testid="reply"]').text
    retweet_cnt = card.find_element_by_xpath('.//div[@data-testid="retweet"]').text
    like_cnt = card.find_element_by_xpath('.//div[@data-testid="like"]').text
    
    # get a string of all emojis contained in the tweet
    """Emojis are stored as images... so I convert the filename, which is stored as unicode, into 
    the emoji character."""
    emoji_tags = card.find_elements_by_xpath('.//img[contains(@src, "emoji")]')
    emoji_list = []
    for tag in emoji_tags:
        filename = tag.get_attribute('src')
        try:
            emoji = chr(int(re.search(r'svg\/([a-z0-9]+)\.svg', filename).group(1), base=16))
        except AttributeError:
            continue
        if emoji:
            emoji_list.append(emoji)
    emojis = ' '.join(emoji_list)
    
    tweet = (username, handle, postdate, text, emojis, reply_cnt, retweet_cnt, like_cnt)
    return tweet   

driver = None
driver = get_driver()
visit_site(site="https://twitter.com/i/flow/login")
twitter_cookies = driver.get_cookies()
driver.refresh()

##get tweets for a looping date
startdate='01-01-2022'
enddate='01-03-2022'
start_date = datetime.strptime(startdate,"%m-%d-%Y")
end_date = datetime.strptime(enddate, "%m-%d-%Y")
date=start_date
while(date<end_date):
    get_specific_date_tweets('covid19',date,10, 'covid19.txt')
    date = date + dt.timedelta(days=1)
    