import os  
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
    "download.default_directory" : os.getcwd() + "\\CSVs"
    }

options.add_experimental_option("prefs", prefs)
options.add_argument("--headless")

# Downloads the top parse for a player on a specified boss and saves it as playerName.csv
def download_csv(player=None, boss=None):

    print('Establishing driver . . .')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    print(f'Navigating to {player.capitalize()}\'s WCL Page . . .')
    driver.get(f'https://classic.warcraftlogs.com/character/us/skyfury/{player.lower()}')

    WebDriverWait(driver, 35).until(EC.presence_of_element_located((By.LINK_TEXT, boss)))
    boss = driver.find_element(By.LINK_TEXT, boss)

    driver.execute_script("return arguments[0].scrollIntoView(true);", boss)
    driver.execute_script("window.scrollBy(0, -100);")
    
    print('Selecting boss . . .')
    boss.click()

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'character-table-link')))
    reports = driver.find_elements(By.CLASS_NAME, 'character-table-link')

    report_list = []
    for i in range(len(reports)):
        report_list.append(reports[i].text)

    # parses = pd.DataFrame({
    #     'parse':report_list[0::6],
    #     'kill_time': report_list[3::6]
    # })

    # parses = parses.sort_values('parse', ascending=False).reset_index(drop=True)
    # parse = parses['parse'][0]

    kill_time = report_list[3]

    min, sec = str(kill_time).split(':')
    kill_time = int(min)*60 + int(sec)

    print('Finding top parse . . .')
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.LINK_TEXT, report_list[0])))
    top_parse_report = driver.find_elements(By.LINK_TEXT, str(report_list[0]))[0]
    driver.execute_script("return arguments[0].scrollIntoView(true);", top_parse_report)
    driver.execute_script("window.scrollBy(0, -200);")
    top_parse_report.click()


    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.LINK_TEXT, player.capitalize())))
    top_parse = driver.find_element(By.LINK_TEXT, player.capitalize())
    driver.execute_script("return arguments[0].scrollIntoView(true);", top_parse)
    driver.execute_script("window.scrollBy(0, -100);")
    top_parse.click()

    print('Downloading CSV . . .')
    ignored_exceptions=(NoSuchElementException,StaleElementReferenceException,)
    time.sleep(5)
    csv_button = driver.find_elements(By.XPATH, '//button[normalize-space()="CSV"]')[0]
    driver.execute_script("return arguments[0].scrollIntoView(true);", csv_button)
    driver.execute_script("window.scrollBy(0, -100);")
    csv_button.click()

    time.sleep(3)
    print('Renaming CSV . . .')

    try:
        os.remove(os.getcwd() + f'\\CSVs\\{player.lower()}.csv')
    except:
        pass
    os.rename(os.getcwd() + f'\\CSVs\\Warcraft Logs - Combat Analysis for Warcraft.csv',
    os.getcwd() + f'\\CSVs\\{player.lower()}.csv')

    print('Adding kill time . . .')
    csv = pd.read_csv(f'CSVs\\{player}.csv')
    csv['kill_time'] = kill_time
    csv.to_csv(f'CSVs\\{player}.csv')
    driver.quit()

# Looks through top players of a particular class/spec and tries to find one who's kill time matches within tolerance to the target
def find_top_match(server=None, player_class=None, player_spec=None, boss=None, target_time=None, kill_time_tolerance=None):

    print('Establishing driver . . .')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    if server.lower() == 'all':
        server = 'zone/rankings/1017'
    else:
        server = 'server/rankings/5192/1017'
    
    p_class = str(player_class.title()).replace(' ','')
    p_spec = str(player_spec.title()).replace(' ','')

    print(f'https://classic.warcraftlogs.com/{server}#metric=dps&partition=2&class={p_class}&spec={p_spec}&boss={boss_ids[boss]}')
    driver.get(f'https://classic.warcraftlogs.com/{server}#metric=dps&partition=2&class={p_class}&spec={p_spec}&boss={boss_ids[boss]}')

    print(f'Navigating to top {player_spec.title()} {player_class.title()}s . . .')
    top_players = driver.find_elements(By.CLASS_NAME, 'main-table-player')
    top_players_times = driver.find_elements(By.CLASS_NAME, 'players-table-duration')
    
    top_players_list = []
    top_players_time_list = []
    for i in range(len(top_players)):
        top_players_list.append(top_players[i].text)
        top_players_time_list.append(top_players_times[i].get_attribute("innerText").split('\n')[0])
    
    df = pd.DataFrame({
        'player':top_players_list,
        'kill_time':top_players_time_list
    })

    print(target_time)
    found_match = False
    for i in range(len(df)):

        min, sec = str(df['kill_time'][i]).split(':')
        kill_time = int(min) * 60 + int(sec)

        if (target_time - kill_time_tolerance) < kill_time < (target_time + kill_time_tolerance):
            found_match = True
            player= df['player'][i]
    
    if found_match is False:
        print('Could not find a match within the specified tolerance')
        return

    for i in range(2):
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.LINK_TEXT, player.capitalize())))
        top_parse = driver.find_element(By.LINK_TEXT, player.capitalize())
        driver.execute_script("return arguments[0].scrollIntoView(true);", top_parse)
        driver.execute_script("window.scrollBy(0, -100);")
        top_parse.click()

    time.sleep(3)
    print('Downloading CSV . . .')
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//button[normalize-space()="CSV"]')))
    csv_button = driver.find_elements(By.XPATH, '//button[normalize-space()="CSV"]')[0]
    driver.execute_script("return arguments[0].scrollIntoView(true);", csv_button)
    driver.execute_script("window.scrollBy(0, -100);")
    csv_button.click()

    time.sleep(3)
    print('Renaming CSV . . .')

    try:
        os.remove(os.getcwd() + f'\\CSVs\\{player.lower()}.csv')
    except:
        pass
    os.rename(os.getcwd() + f'\\CSVs\\Warcraft Logs - Combat Analysis for Warcraft.csv',
    os.getcwd() + f'\\CSVs\\{player.lower()}.csv')

    print('Adding kill time . . .')
    csv = pd.read_csv(f'CSVs\\{player}.csv')
    csv['kill_time'] = kill_time
    csv.to_csv(f'CSVs\\{player}.csv')
    driver.quit()
    
    return player

# Cleans a WarcraftLogs dataframe, turning outputs like 1.1k into 1100, etc. so that it is able to be manipulated via python
def clean_df(player, kill_time=None):
    """Cleans a WarcraftLogs dataframe, turning outputs like 1.1k into 1100, etc. so that it is able to be manipulated via python

    Args:
        player (df): Player DATAFRAME
        kill_time (int): Kill time (in seconds)

    Returns:
        df: Returns the cleaned DATAFRAME
    """

    df = player.copy()
    df['dmg_perc'] = ''
    df['kill_time'] = kill_time

    df = df.rename(columns={
        'Name': 'name',
        'Amount': 'amount',
        'Casts': 'casts',
        'Avg Cast': 'avg_cast',
        'Hits': 'hits',
        'Avg Hit': 'avg_hit',
        'Crit %': 'crit_perc',
        'Uptime %': 'uptime_perc',
        'DPS': 'dps'
        })

    for i in range(len(df)):
        df['amount'][i] = int(df['amount'][i].split('$')[0])

        if 'k' in df['avg_cast'][i]:
            df['avg_cast'][i] = float(df['avg_cast'][i].split('k')[0]) * 1000

        if '%' in df['crit_perc'][i]:
            df['crit_perc'][i] = float(df['crit_perc'][i].split('%')[0]) / 100
        
        if '%' in df['uptime_perc'][i]:
            df['uptime_perc'][i] = float(df['uptime_perc'][i].split('%')[0]) / 100

        if 'miss_perc' in df.columns and '%' in df['miss_perc'][i]:
            df['miss_perc'][i] = float(df['miss_perc'][i].split('%')[0]) / 100
        
        if ',' in df['dps'][i]:
            df['dps'][i] = float(df['dps'][i].split(',')[0] + df['dps'][i].split(',')[1])
        else:
            df['dps'][i] = float(df['dps'][i])
        
        if '(' in str(df['hits'][i]):
            if df['name'][i] == 'Corruption':
                df['hits'][i] = int(str(df['hits'][i]).split('(')[0])
            else:
                df['hits'][i] = int(str(df['hits'][i]).split('(')[1].split(')')[0])


    df.drop_duplicates(subset=['amount'], keep='first', inplace=True)

    if kill_time is not None:
        df['dps'] = df['amount'] / kill_time
        df['dps'] = df['amount'] / kill_time

    df = df.replace('-', 0)

    df['casts'] = df['casts'].astype(int)
    df['avg_cast'] = df['avg_cast'].astype(float)

    df['hits'] = df['hits'].astype(int)
    df['avg_hit'] = df['amount'] / df['hits']

    total_dmg = df['amount'].sum()
    df['dmg_perc'] = df['amount'] / total_dmg

    df = df.replace(0, np.NaN).reset_index(drop=True)

    sum_df = df[['name', 'amount', 'casts', 'hits', 'dps']].groupby('name').sum(numeric_only=True).reset_index()
    mean_df = df[['name', 'dmg_perc', 'avg_cast', 'avg_hit', 'crit_perc', 'uptime_perc', 'kill_time']].groupby('name').mean(numeric_only=True).reset_index()

    df = pd.merge(sum_df, mean_df, how='inner', on='name')

    df = df[['name', 'amount', 'dmg_perc', 'casts', 'avg_cast', 'hits', 'avg_hit', 'crit_perc', 'uptime_perc', 'dps', 'kill_time']]

    return df

# Normalizes the gear to see what player 1's DPS would look like if his abilities hit as hard as player 2"
def normalize_players(player=None, compare_to=None):
    """Normalizes the gear of a player (player 1) to that of the gear of another player (player 2) 
    by replacing the "avg_hit" damage of player 1 with that of player 2 and then refactoring total damage, dps, etc.
    to see what player 1's DPS would look like if his abilities hit as hard as player 2

    Args:
        player (df): Player DATAFRAME that you want to learn about
        compare_to (df): DATAFRAME of the player you'd like to compare to

    Returns:
        df: Returns a normalized DATAFRAME
    """

    for i in range(len(player)):
        if '(Melee, Bite)' in player['name'][i]:
            player['name'][i] = 'Pet'
    for i in range(len(compare_to)):
        if '(Melee, Bite)' in compare_to['name'][i]:
            compare_to['name'][i] = 'Pet'

    join_df = compare_to[['name', 'avg_hit']]

    player = pd.merge(left=player, right=join_df, how='outer', on='name')

    player['avg_hit_x'] = player['avg_hit_y']
    player = player.rename(columns={'avg_hit_x':'avg_hit'})
    player.drop(columns=['avg_hit_y'], inplace=True)

    player['amount'] = player['hits'] * player['avg_hit']
    player['dps'] = player['amount'] / player['kill_time']

    total_dmg = player['amount'].sum()
    player['dmg_perc'] = player['amount'] / total_dmg

    return player

# Subtracts the compare_to dataframe's values from player values and returns the resulting dataframe
def compare_players(player=None, compare_to=None):
    """Subtracts the compare_to dataframe's values from player values and returns the resulting DATAFRAME

    Args:
        player (df): Player DATAFRAME that you want to learn about
        compare_to (df): DATAFRAME of the player you'd like to compare to

    Returns:
        df: Returns a comparison DATAFRAME
    """

    df1 = player.drop(columns=['kill_time'])
    df2 = compare_to

    cols = df1.columns

    for i in range(len(df1)):
            if '(Melee, Bite)' in df1['name'][i]:
                df1['name'][i] = 'Pet'
    for i in range(len(df2)):
            if '(Melee, Bite)' in df2['name'][i]:
                df2['name'][i] = 'Pet'

    df1['index'] = range(len(df1))

    df1 = df1.set_index('name')
    df2 = df2.set_index('name')

    df = df1.sub(df2, fill_value=0).reset_index()

    df = df.sort_values('index', ascending=True).reset_index(drop=True).drop(columns='index')

    return df[cols]

# Styles DF with red/green theme so you can easily see +/- values
def style(df):
    def color_negative_red(value):
        """
        Colors elements in a dateframe
        green if positive and red if
        negative. Does not color NaN
        values.
        """

        if value < 0:
            color = 'orangered'
        elif value > 0:
            color = 'limegreen'
        else:
            color = 'grey'

        return 'color: %s' % color

    subset = ['casts', 'hits', 'uptime_perc', 'dps']

    return df.style.applymap(color_negative_red, subset=subset)

# Full comparison function
def run_comparison(server=None, player_class=None, player_spec=None, player_name=None, compare_to_name=None, boss=None, kill_time_tolerance=None, normalize=False):

    download_csv(player=player_name, boss=boss)
    player = pd.read_csv(f'CSVs\\{player_name}.csv')

    if compare_to_name is None:
        compare_to_name = find_top_match(server=server, player_class=player_class, player_spec=player_spec, boss=boss, target_time=player['kill_time'][0], kill_time_tolerance=kill_time_tolerance)
    else:
        download_csv(player=compare_to_name, boss=boss)
    compare_to = pd.read_csv(f'CSVs\\{compare_to_name}.csv')

    os.remove(f'CSVs\\{player_name}.csv')
    os.remove(f'CSVs\\{compare_to_name}.csv')

    clean_player = clean_df(player, player['kill_time'][0])
    clean_compare_to = clean_df(compare_to, compare_to['kill_time'][0])

    norm_player = normalize_players(clean_player, clean_compare_to)
    print(f'{player_name} DPS: ' + str(clean_player['dps'].sum()))
    print(f'{player_name} Normalized DPS: ' + str(norm_player['dps'].sum()))
    print(f'{compare_to_name} DPS: ' + str(clean_compare_to['dps'].sum()))

    if normalize:
        df =  compare_players(norm_player, clean_compare_to)
    else:
        df =  compare_players(clean_player, clean_compare_to)
    
    return style(df)


# Example
# run_comparison(player_name='Longshot', player_time=134, compare_to_name='Perplexity', compare_to_time=119, normalize=True)
