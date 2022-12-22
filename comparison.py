import pandas as pd
import numpy as np
pd.options.mode.chained_assignment = None

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

    player = pd.merge(left=player, right=join_df, how='inner', on='name')

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

# Full comparison function
def run_comparison(player_name=None, player_time=None, compare_to_name=None, compare_to_time=None, normalize=False):

    player = pd.read_csv(f'{player_name}.csv')
    compare_to = pd.read_csv(f'{compare_to_name}.csv')

    clean_player = clean_df(player, player_time)
    clean_compare_to = clean_df(compare_to, compare_to_time)

    norm_player = normalize_players(clean_player, clean_compare_to)
    print(f'{player_name} DPS: ' + str(clean_player['dps'].sum()))
    print(f'{player_name} Normalized DPS: ' + str(norm_player['dps'].sum()))
    print(f'{compare_to_name} DPS: ' + str(clean_compare_to['dps'].sum()))

    if normalize:
        return compare_players(norm_player, clean_compare_to)
    else:
        return compare_players(clean_player, clean_compare_to)

# Example
# run_comparison(player_name='Longshot', player_time=134, compare_to_name='Perplexity', compare_to_time=119, normalize=True)
