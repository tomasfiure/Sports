import requests
from bs4 import BeautifulSoup
import urllib
import pandas as pd
from copy import copy
import unicodedata
import pickle
import os

# Libary with full names and acronyms
abb_to_name = {'ARI': 'Diamondbacks', 'ATL': 'Braves', 'BAL': 'Orioles', 'BOS': 'Red Sox', 'CHC': 'Cubs', 'CHW': 'White Sox', 'CIN': 'Reds', 'CLE': 'Guardians', 'COL': 'Rockies', 'DET': 'Tigers', 'HOU': 'Astros', 'KCR': 'Royals', 'LAA': 'Angels', 'LAD': 'Dodgers', 'MIA': 'Marlins', 'MIL': 'Brewers', 'MIN': 'Twins', 'NYM': 'Mets', 'NYY': 'Yankees', 'OAK': 'Athletics', 'PHI': 'Phillies', 'PIT': 'Pirates', 'SDP': 'Padres', 'SEA': 'Mariners', 'SFG': 'Giants', 'STL': 'Cardinals', 'TBR': 'Rays', 'TEX': 'Rangers', 'TOR': 'Blue Jays', 'WSN': 'Nationals'}
name_to_abb = {value: key for key, value in abb_to_name.items()}    
# Helper funtion to retreive links to team depth charts
def team_links():
    url = 'https://www.fangraphs.com/depthcharts.aspx?position=Standings'
    open_url = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(open_url,'lxml')
    table = soup.find('div',class_='depth-charts-aspx_table').find_all('a')
    output = {}
    for element in table:
        if element.text[:2] == 'AL':
            break
        output[element.text] = 'https://www.fangraphs.com/' +element.get('href')
    return output
#print(team_links())

# Access a team's schedule and basic matchup info 
def access_team_schedule(team):
    url = 'https://www.fangraphs.com/teams/' + team + '/schedule'
    open_url = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(open_url,'lxml')
    table = soup.find('div', class_='team-schedule-table')
    pandas_table = pd.read_html(str(table))[0]
    pandas_table = pandas_table.drop('Unnamed: 1', axis=1)
    return pandas_table
#print(access_team_schedule('Giants'))

# Access a team's depth chart
# Note for use: team name first letter should be capitalized
def access_team_depth_chart(team):
    url = team_links()[team]
    open_url = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(open_url,'lxml')
    #print(soup)
    first_filter = soup.find_all('table')[14]
    players = {}
    roster = first_filter.find_all('a')
    for player in roster:
        name = player.text
        if name[0].isupper() & name[1].isupper():
            players[remove_tildes(name[0]+'.'+name[1]+'.'+name[2:])] = 'https://www.fangraphs.com/' + player.get('href')     
        else:
            players[remove_tildes(name)] = 'https://www.fangraphs.com/' + player.get('href')     
    return players
#print(access_team_depth_chart('Reds'))

# Helper function to extract a pd dataframe from inputted html table code in fan graphs 
def extract_pd(table):
    table_copy = copy(table)
    ext = table_copy.find('tr',class_='rgPager')
    ext.extract()
    ext2 = table_copy.find('tfoot')
    ext2.extract()
    html_table = table_copy.prettify()
    df_list = pd.read_html(html_table)
    df = df_list[0]
    df = df.drop('#', axis=1)
    return df

# Function to import pitch value data for all MLB hitters
def pitch_values():
    gen_url = 'https://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&lg=all&qual=50&type=14&season=2023&month=0&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&startdate=&enddate='
    open_url = urllib.request.urlopen(gen_url).read()
    soup = BeautifulSoup(open_url,'lxml')
    table = soup.find('table', class_='rgMasterTable')
    data = extract_pd(table)

    while(table.find('tr',class_='rgPager').find('div',class_='rgWrap rgArrPart2').find('a').has_attr('href')):
        new_url ='https://www.fangraphs.com/'+ table.find('tr',class_='rgPager').find('div',class_='rgWrap rgArrPart2').find('a').get('href')
        open_url = urllib.request.urlopen(new_url).read()
        soup = BeautifulSoup(open_url,'lxml')
        table = soup.find('table', class_='rgMasterTable')
        data = pd.concat([data,extract_pd(table)], ignore_index=True)
    
    return data
#print(pitch_values())

# Funtion to return a hitter percentile vs. different pitch types
def hitter_pv_percentiles(hitter):
    data = pitch_values()
    total = len(data)
    print(hitter)
    for col in data.columns[3:]:
        sorted_data = data.sort_values(by=col).reset_index(drop=True)
        player = sorted_data[sorted_data['Name'] == hitter]
        index = player.index[0]
        print('Pitch Type:', col, 'Percentile:',(index/total)*100)
#hitter_pv_percentiles('Joc Pederson')
    
# Function to import pitch value data for all MLB hitters
def pitch_values_pitchers():
    gen_url = 'https://www.fangraphs.com/leaders.aspx?pos=all&stats=sta&lg=all&qual=30&type=14&season=2023&month=0&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&startdate=2023-01-01&enddate=2023-12-31'
    open_url = urllib.request.urlopen(gen_url).read()
    soup = BeautifulSoup(open_url,'lxml')
    table = soup.find('table', class_='rgMasterTable')
    data = extract_pd(table)

    while(table.find('tr',class_='rgPager').find('div',class_='rgWrap rgArrPart2').find('a').has_attr('href')):
        new_url ='https://www.fangraphs.com/'+ table.find('tr',class_='rgPager').find('div',class_='rgWrap rgArrPart2').find('a').get('href')
        open_url = urllib.request.urlopen(new_url).read()
        soup = BeautifulSoup(open_url,'lxml')
        table = soup.find('table', class_='rgMasterTable')
        data = pd.concat([data,extract_pd(table)], ignore_index=True)
    
    return data
# print(pitch_values_pitchers())

# Used to make dict with names and abbreviations
def make_pitcher_names_dict():
    name_dict = {}
    for name in pitch_values_pitchers()['Name']:
        if name[1] == '.':
            name_dict[name] = name
        else:
            first,last = name.split(" ")[0],name.split(" ")[1]
            name_dict[first[0]+'. '+last] = name
    with open('pitcher_names.pkl', 'wb') as file:
        pickle.dump(name_dict, file)
    return name_dict
        
#make_pitcher_names_dict()
# Function to import pitch type percentages for MLB pitchers 
def pitch_percentage_pitchers():
    gen_url = 'https://www.fangraphs.com/leaders.aspx?pos=all&stats=sta&lg=all&qual=30&type=9&season=2023&month=0&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&startdate=2023-01-01&enddate=2023-12-31'
    open_url = urllib.request.urlopen(gen_url).read()
    soup = BeautifulSoup(open_url,'lxml')
    table = soup.find('table', class_='rgMasterTable')
    data = extract_pd(table)

    while(table.find('tr',class_='rgPager').find('div',class_='rgWrap rgArrPart2').find('a').has_attr('href')):
        new_url ='https://www.fangraphs.com/'+ table.find('tr',class_='rgPager').find('div',class_='rgWrap rgArrPart2').find('a').get('href')
        open_url = urllib.request.urlopen(new_url).read()
        soup = BeautifulSoup(open_url,'lxml')
        table = soup.find('table', class_='rgMasterTable')
        data = pd.concat([data,extract_pd(table)], ignore_index=True)
    
    return data

def remove_tildes(input_string):
    # Normalize the input string to decomposed form (NFD)
    normalized_string = unicodedata.normalize('NFD', input_string)

    # Remove combining characters (diacritical marks) like tildes
    cleaned_string = ''.join(char for char in normalized_string if not unicodedata.combining(char))

    return cleaned_string

# Helper function to cut depth chart absed on at bats
def cut_depth_chart(data,team,ab):
    team_number = team_links()[team][63:]
    url = 'https://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&lg=all&qual=0&type=8&season=2023&month=0&season1=2023&ind=0&team='+team_number+'&rost=0&age=0&filter=&players=0&startdate=2023-01-01&enddate=2023-12-31&sort=3,d'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    team_table = soup.find('table',class_='rgMasterTable').find('tbody').find_all('tr')
    table_dict = {}
    for row in team_table:
        table_dict[row.find('a').text] = row.find('td',class_='grid_line_regular rgSorted').text
    to_remove = []
    for player in data.keys():     
        if player in table_dict:
            if int(table_dict[player])<ab:
                to_remove.append(player)
    for i in to_remove:
        data.pop(i)
    return data        
#print(cut_depth_chart(access_team_depth_chart(abb_to_name['CIN']),abb_to_name['CIN']))

def matchup(team, pitcher):
    # Get pandas table
    # Tables saved into pickle for reuse
    
    # Pitcher Pitch percentages
    if os.path.exists('pitcher_pitches.pkl'):
        with open('pitcher_pitches.pkl', 'rb') as file:
            pitcher_pitches = pickle.load(file)
    else:
        pitcher_pitches = pitch_percentage_pitchers()
        with open('pitcher_pitches.pkl', 'wb') as file:
            pickle.dump(pitcher_pitches, file)
            
    # Pitcher Pitch values
    if os.path.exists('pitcher_values.pkl'):
        with open('pitcher_values.pkl', 'rb') as file:
            pitcher_values = pickle.load(file)
    else:
        pitcher_values = pitch_values_pitchers()
        with open('pitcher_values.pkl', 'wb') as file:
            pickle.dump(pitcher_values, file)
    
    # Get tables for specific pitcher
    pitches = pitcher_pitches[pitcher_pitches['Name'] == pitcher]
    values = pitcher_values[pitcher_values['Name'] == pitcher]
    # Make dict with pitcher coefficients (black box for ratings)
    pitcher_ratings = {}
    for col in values.columns[3:]:
        pitch = col[1:3]
        val = col[1:3] + '%'
        p = pitches.iloc[0, pitches.columns.get_loc(val)]
        if pd.isna(p):
            pitcher_ratings[pitch] = 0
        else:
            pitcher_ratings[pitch] = float(p[:-1]) * (0.01) * float(values.iloc[0, values.columns.get_loc(col)])
    
    # Get Pandas table
    # Pitcher Pitch values
    if os.path.exists('batter_values.pkl'):
        with open('batter_values.pkl', 'rb') as file:
            temp_table = pickle.load(file)
    else:
        temp_table = pitch_values()
        with open('batter_values.pkl', 'wb') as file:
            pickle.dump(temp_table, file)
    
    # Get table for specific team
    batter_values = temp_table[temp_table['Team']==team]
    # Make dict with pitcher coefficients
    batter_ratings = {}
    # Iterate on team's players
    for player in cut_depth_chart(access_team_depth_chart(abb_to_name[team]),abb_to_name[team],90).keys():
        
        # Get batter pitch values
        pla = batter_values[batter_values['Name']==player]
        if not pla.empty:
            # Get dict with pitch types and coefficient
            ratings = {}
            for col in values.columns[3:]:
                pitch = col[1:3]
                val = col[1:3] + '%'
                b = pitches.iloc[0, pitches.columns.get_loc(val)]
                if pd.isna(b)|pd.isna(b):
                    ratings[pitch] = 0
                else:
                    ratings[pitch] = float(b[:-1]) * (0.01) * float(pla.iloc[0, pla.columns.get_loc(col)])
            batter_ratings[player] = ratings
        else:
            print('player not found:', player)
    # Convert to df
    pitcher_df = pd.DataFrame([pitcher_ratings]) 
    batters_df = pd.DataFrame(batter_ratings).T 
    # Subtract pitcher coeffficients from batters
    dat = batters_df.sub(pitcher_df.iloc[0],axis = 'columns')
    # Make output datafrmae with coefficients
    output = dat.sum(axis=1)
    output = pd.DataFrame({'Coefficient': output})
    output = output.sort_values(by='Coefficient')
    return output
#print(matchup('ATL','Justin Verlander'))
#print(matchup('CIN','Ross Stripling'))

def day_matchups(date): # Date format: YYYY/MM/DD
    url = 'https://www.espn.com/mlb/scoreboard/_/date/'+date
    open_url = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(open_url,'lxml')
    sections = soup.find_all('section', class_='Scoreboard bg-clr-white flex flex-auto justify-between')
    games = []
    for section in sections:
        home = {'Team':section.find_all('a')[3].text,'Pitcher':None}
        away = {'Team':section.find_all('a')[1].text,'Pitcher':None}
        temp = section.find('div',class_='Scoreboard__Column ph4 mv4 Scoreboard__Column--3').find_all('span',class_='Athlete__PlayerName')
        home['Pitcher'], away['Pitcher'] = temp[1].text, temp[0].text
        games.append({'home':home,"away":away})
    return games

# Function to get rankings of a day
def day_rankings(date):
    # Import day matchups
    games = day_matchups(date)
    # Initialize output
    output = pd.DataFrame()
    # Import pitcher names dict
    if os.path.exists('batter_values.pkl'):
        with open('pitcher_names.pkl', 'rb') as file:
            name_dict = pickle.load(file)
    else:
        name_dict = make_pitcher_names_dict()
    # Iterate on games
    for game in games:
        # Get team names and opposing pitchers
        t1,t2 = name_to_abb[game['home']['Team']], name_to_abb[game['away']['Team']]
        p1,p2 = name_dict[game['home']['Pitcher']] if game['home']['Pitcher'] in name_dict else 'not found', name_dict[game['away']['Pitcher']] if game['away']['Pitcher'] in name_dict else 'not found'
        # Dict will act as filter for pitchers, so matchup returned for wualified pitchers
        # Get individual game matchups and concatenate all together
        if p2 != 'not found':
            t1_p2 = matchup(t1,p2)
            t1_p2['Team'] = t1
            output = pd.concat([output,t1_p2])
        if p1 != 'not found':
            t2_p1 = matchup(t2,p1)
            t2_p1['Team'] = t2
            output = pd.concat([output,t2_p1])
    output = output.sort_values(by='Coefficient')
    return output

# output = day_rankings('20230719')
# print(output)
# output.to_csv('my_dataframe.csv', index=True)   
    