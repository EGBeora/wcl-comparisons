import os  
from os import listdir
from os.path import isfile, join
import time
import numpy as np
import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from dictionaries import *

pd.options.mode.chained_assignment = None

options = Options()

prefs = {
    "download.default_directory" : os.getcwd() + "\\CSVs\\deaths"
    }

options.add_experimental_option("prefs", prefs)
# options.add_argument("--headless")

def style(df):
    def color_negative_red(value):
        """
        Colors elements in a dateframe
        green if positive and red if
        negative. Does not color NaN
        values.
        """

        if value <= 25:
            color = 'grey'
        if value <= 16:
            color = 'limegreen'
        if value <= 14:
            color = 'royalblue'
        if value <= 10:
            color = 'darkorchid'
        if value <= 5:
            color = 'orange'
        if value <= 2:
            color = 'violet'

        return 'color: %s' % color

    subset = ['player_rank', 'death_time_rank', 'htps_rank', 'dtps_rank']

    return df.style.applymap(color_negative_red, subset=subset)

def download_wipes(report_link=None, boss=None):

    dir = os.getcwd()
    deaths_path = f'\\CSVs\\deaths\\'
    deaths = [f for f in listdir(dir + deaths_path) if isfile(join(dir + deaths_path, f))]
    for file in deaths:
        os.remove(os.getcwd() + f'\\CSVs\\deaths\\' + file)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get(report_link)

    fight = driver.find_element(By.ID, f'fight-details-{boss_ids[boss]}-3')
    wipes = fight.find_element(By.CLASS_NAME, f'fight-grid-{boss_ids[boss]}-3-wipes-all')
    wipe_links = wipes.find_elements(By.TAG_NAME, 'a')

    fight_id_list = []
    for i in range(len(wipe_links)):
        fight_id_list.append(wipe_links[i].get_attribute('onmousedown').split(',')[0].split('return changeFightByIDAndIndex(')[1])

    fight_id_list

    count=1
    for id in fight_id_list:
        print(id)
        fight = driver.get(f'https://classic.warcraftlogs.com/reports/jzq4ZfmLRxtDgXnK#fight={id}&type=deaths')
        time.sleep(1)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'dt-button')))
        csv = driver.find_element(By.CLASS_NAME, 'dt-button')
        time.sleep(1)
        driver.execute_script("return arguments[0].scrollIntoView(true);", csv)
        driver.execute_script("window.scrollBy(0, -400);")
        time.sleep(1)
        csv.click()

        time.sleep(2)

        try:
            os.remove(os.getcwd() + f'\\CSVs\\deaths\\{boss.lower()}{count}.csv')
        except:
            pass
        time.sleep(1)

        os.rename(os.getcwd() + f'\\CSVs\\deaths\\Warcraft Logs - Combat Analysis for Warcraft.csv',
        os.getcwd() + f'\\CSVs\\deaths\\{boss.lower()}{count}.csv')
        count += 1

def analyze_wipes(report_link=None, boss=None):

    print('Downloading Wipes . . .')
    download_wipes(report_link=report_link, boss=boss)

    print('Analyzing Wipes . . .')
    dir = os.getcwd()
    deaths_path = f'\\CSVs\\deaths\\'
    
    # damage_taken = [f for f in listdir(dmg_path) if isfile(join(dmg_path, f))]
    deaths = [f for f in listdir(dir + deaths_path) if isfile(join(dir + deaths_path, f))]

    # df = pd.concat([pd.read_csv(dir + deaths_path + file) for file in deaths]).reset_index(drop=True)

    df = pd.DataFrame()
    count = 0
    for file in deaths:
        df = pd.concat([df, pd.read_csv(dir + deaths_path + file).drop_duplicates(subset=['Name'], keep='first')])

    df = df.rename(columns={
        'Time': 'death_time',
        'Name': 'name',
        'Dmg Taken': 'dmg_taken',
        'Healing Rcvd': 'healing_recieved'
        })

    df = df[['name', 'death_time', 'dmg_taken', 'healing_recieved']].reset_index(drop=True)

    for i in range(len(df)):
        min, sec = str(df['death_time'][i]).split(':')
        df['death_time'][i] = int(min)*60 + int(sec)

    df = df.replace({',':'', 'None':0}, regex=True)

    df['dmg_taken'] = df['dmg_taken'].astype(int)
    df['healing_recieved'] = df['healing_recieved'].astype(int)

    df = df.groupby('name').sum(numeric_only=True).reset_index()

    df['dtps'] = round(df['dmg_taken'] / df['death_time'])
    df['htps'] = round(df['healing_recieved'] / df['death_time'])

    df = df.sort_values('dtps', ascending=True).reset_index(drop=True)
    df.index = df.index.set_names(['dtps_rank'])
    df = df.reset_index()

    df = df.sort_values('htps', ascending=True).reset_index(drop=True)
    df.index = df.index.set_names(['htps_rank'])
    df = df.reset_index()

    df = df.sort_values('death_time', ascending=False).reset_index(drop=True)
    df.index = df.index.set_names(['death_time_rank'])
    df = df.reset_index()

    df['dtps_rank'] += 1
    df['htps_rank'] += 1
    df['death_time_rank'] += 1

    df.insert(0, 'player_rank', round((df['dtps_rank'] + df['htps_rank'] + df['death_time_rank']) / 3, 1))

    first_column = df.pop('name')
    df.insert(0, 'name', first_column)

    return style(df.sort_values('player_rank', ascending=True).reset_index(drop=True))