from bs4 import BeautifulSoup
import urllib
import pandas as pd
from copy import copy
import pickle
import os
from datetime import datetime, timedelta
import numpy as np
import time
from selenium import webdriver
# import unicodedata

# Macro for current working directory
CWD = os.getcwd()
# Macro to store pickles
PKL = '\\pkl storage\\'
# Libary with full names and acronyms
abb_to_name = {'ARI': 'Diamondbacks', 'ATL': 'Braves', 'BAL': 'Orioles', 'BOS': 'Red Sox', 'CHC': 'Cubs', 'CHW': 'White Sox', 'CIN': 'Reds', 'CLE': 'Guardians', 'COL': 'Rockies', 'DET': 'Tigers', 'HOU': 'Astros', 'KCR': 'Royals', 'LAA': 'Angels', 'LAD': 'Dodgers', 'MIA': 'Marlins', 'MIL': 'Brewers', 'MIN': 'Twins', 'NYM': 'Mets', 'NYY': 'Yankees', 'OAK': 'Athletics', 'PHI': 'Phillies', 'PIT': 'Pirates', 'SDP': 'Padres', 'SEA': 'Mariners', 'SFG': 'Giants', 'STL': 'Cardinals', 'TBR': 'Rays', 'TEX': 'Rangers', 'TOR': 'Blue Jays', 'WSN': 'Nationals'}
name_to_abb = {value: key for key, value in abb_to_name.items()}  

#FUNCTIONS TO RETRIEVE DATA FROM LEGACY FORMAT (REG)
def reg_url_to_soup(url):
    open_url = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(open_url,'lxml')
    return soup

# Helper function to extract a pd dataframe from inputted html table code in fan graphs 
# Input: table div in html
# Output: pd dataframe corresponding to table
def reg_extract_pd(table):
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

def reg_soup_to_pd(soup):
    table = soup.find('table', class_='rgMasterTable')
    data = reg_extract_pd(table)

    while(table.find('tr',class_='rgPager').find('div',class_='rgWrap rgArrPart2').find('a').has_attr('href')):
        new_url ='https://www.fangraphs.com/'+ table.find('tr',class_='rgPager').find('div',class_='rgWrap rgArrPart2').find('a').get('href')
        open_url = urllib.request.urlopen(new_url).read()
        soup = BeautifulSoup(open_url,'lxml')
        table = soup.find('table', class_='rgMasterTable')
        data = pd.concat([data,reg_extract_pd(table)], ignore_index=True)
    
    return data

#FUNCTIONS TO RETRIEVE DATA FROM NEW FORMAT (NEW)

# Function to convert from url to soup
def url_to_soup(url):
    driver = webdriver.Chrome()
    driver.get(url)
    time.sleep(3) 
    html = driver.page_source
    driver.quit()
    soup = BeautifulSoup(html, 'html.parser')
    return soup

# Helper function to extract a pd dataframe from inputted html table code in fan graphs 
# Input: table div in html
# Output: pd dataframe corresponding to table
def extract_pd(table):
    table_copy = copy(table)
    exts = table_copy.find_all('div',class_='th-tooltip undefined')
    for ext in exts:
        ext.extract()
    html_table = table_copy.prettify()
    df_list = pd.read_html(html_table)
    df = df_list[0]
    for col in ['#','-- Line Break --','-- Line Break --.1','-- Line Break --.2','-- Line Break --.3']:
        if col in df.columns:
            df = df.drop([col],axis =1)
    return df

# Helper function to retreive links to team depth charts
# Input: None
# Output: {team name: team link} (ex. {'Braves': 'fangraphs.com...'}) 
def team_links():
    url = 'https://www.fangraphs.com/depthcharts.aspx?position=Standings'
    
    soup = url_to_soup(url)
    table = soup.find('div',class_='depth-charts-aspx_table').find_all('a')
    output = {}
    for element in table:
        if element.text[:2] == 'AL':
            break    
        output[element.text] = 'https://www.fangraphs.com/' +element.get('href')
    with open(CWD+PKL+'team_links.pkl','wb') as f:
        pickle.dump(output,f)
    return output

# Access a team's schedule and basic matchup info 
# Note for use: team name first letter should be capitalized
# Input: team name(ex. Giants)
# Output: pandas table with team  with other information like date and starting pitchers
def access_team_schedule(team):
    url = 'https://www.fangraphs.com/teams/' + team + '/schedule'
    soup = url_to_soup(url)
    table = soup.find('div', class_='team-schedule-table')
    pandas_table = pd.read_html(str(table))[0]
    pandas_table = pandas_table.drop('Unnamed: 1', axis=1)
    return pandas_table

# Function to access a team's depth chart
# Input: team name(ex. Giants)
# Output: Team's depth chart, function has min PA paramater to filter depth chart
def access_team_depth_chart(team):
    if os.path.exists(CWD+PKL+'team_links.pkl'):
        with open(CWD+PKL+'team_links.pkl', 'rb') as file:
            team_link = pickle.load(file)
            link = team_link[team]
    else:
        link = team_links()[team]
    
    if link[-2] == '=':
        team_number = link[-1]
    else:
        team_number = link[-2:]
    min_PA = 100
    url = 'https://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&lg=all&qual='+str(min_PA)+'&type=8&season=2023&month=0&season1=2023&ind=0&team='+team_number+'&rost=&age=&filter=&players=&'
    #print(url)
    soup = url_to_soup(url)
    table = soup.find('div',class_='leaders-major_leaders-major__table__BLZyw').find('table')
    data = extract_pd(table)
    players=[]
    for player in data['Name']:
        players.append(player)
    return players

# Code to save depth charts
# team_depth_charts = {}
# for team in abb_to_name.keys():
#     team_depth_charts[team] = access_team_depth_chart(abb_to_name[team])
#     print(team_depth_charts[team])
# with open(CWD+PKL+'team_depth_charts.pkl','wb') as file:
#     pickle.dump(team_depth_charts,file)


# Function to import pitch value data for all MLB hitters
# Input: time range (overall, month or 2weeks) and date corresponding to date of mathcup generation
# Output: pd dataframe with corresponding data
def batter_pitch_values(spec,date):
    formatted_date = date[:4]+'-'+date[4:6]+'-'+date[6:]
    dt = datetime.strptime(formatted_date, '%Y-%m-%d')
    
    if spec == 'overall':
        min_PA = 100
        gen_url = f'https://www.fangraphs.com/leaders-legacy.aspx?pos=all&stats=bat&lg=all&qual={min_PA}&type=14&season=2023&month=0&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&page=1_50&startdate=2023-03-01&enddate={formatted_date}'
    elif spec == 'month':
        min_PA = 10
        month_dt = dt - timedelta(days=30)
        month_date_string = month_dt.strftime('%Y-%m-%d')
        gen_url = f'https://www.fangraphs.com/leaders-legacy.aspx?pos=all&stats=bat&lg=all&qual={min_PA}&type=14&season=2023&month=3&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&page=1_50&startdate={month_date_string}&enddate={formatted_date}'
    elif spec == '2weeks':
        min_PA = 10
        week2_dt = dt - timedelta(days=14)
        week2_date_string = week2_dt.strftime('%Y-%m-%d')
        gen_url = f'https://www.fangraphs.com/leaders-legacy.aspx?pos=all&stats=bat&lg=all&qual={min_PA}&type=14&season=2023&month=2&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&page=1_50&startdate={week2_date_string}&enddate={formatted_date}'
    
    soup = reg_url_to_soup(gen_url)    
    return reg_soup_to_pd(soup)

# Funtion to return a hitter percentile vs. different pitch types
# Input: time range (overall, month or 2weeks) and date corresponding to date of mathcup generation
# Output: pd dataframe with corresponding data
# def hitter_pv_percentiles(hitter):
#     data = batter_pitch_values()
#     total = len(data)
#     print(hitter)
#     for col in data.columns[3:]:
#         sorted_data = data.sort_values(by=col).reset_index(drop=True)
#         player = sorted_data[sorted_data['Name'] == hitter]
#         index = player.index[0]
#         print('Pitch Type:', col, 'Percentile:',(index/total)*100)
    
# Function to import pitch value data for all MLB hitters
# Input: time range (overall, month or 2weeks) and date corresponding to date of mathcup generation
# Output: pd dataframe with corrseponding data
def pitch_values_pitchers(spec,date):
    formatted_date = date[:4]+'-'+date[4:6]+'-'+date[6:]
    dt = datetime.strptime(formatted_date, '%Y-%m-%d')
    if spec == 'overall':
        min_IP = 20
        gen_url = f'https://www.fangraphs.com/leaders-legacy.aspx?pos=all&stats=pit&lg=all&qual={min_IP}&type=14&season=2023&month=0&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&page=1_50&startdate=2023-03-01&enddate={formatted_date}'
    elif spec == 'month':
        min_IP = 5
        month_dt = dt - timedelta(days=30)
        month_date_string = month_dt.strftime('%Y-%m-%d')
        gen_url = f'https://www.fangraphs.com/leaders-legacy.aspx?pos=all&stats=pit&lg=all&qual={min_IP}&type=14&season=2023&month=3&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&page=1_50&startdate={month_date_string}&enddate={formatted_date}'
    elif spec == '2weeks':
        min_IP = 1
        week2_dt = dt - timedelta(days=14)
        week2_date_string = week2_dt.strftime('%Y-%m-%d')
        gen_url = f'https://www.fangraphs.com/leaders-legacy.aspx?pos=all&stats=pit&lg=all&qual={min_IP}&type=14&season=2023&month=2&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&page=1_50&startdate={week2_date_string}&enddate={formatted_date}'
    
    soup = reg_url_to_soup(gen_url)
    return reg_soup_to_pd(soup)

# Used to make dict with names and abbreviations
# Input: date in YYYMMDD form
# Output: dictionary with pitcher full names and their abbreviations (saves in pickle for reuse)
def make_pitcher_names_dict(date):
    name_dict = {}
    for name in pitch_values_pitchers('overall',date)['Name']:
        if name[1] == '.':
            name_dict[name] = name
        else:
            first,last = name.split(" ")[0],name.split(" ")[1]
            name_dict[first[0]+'. '+last] = name
    with open(CWD+'\pitcher_names.pkl', 'wb') as file:
        pickle.dump(name_dict, file)
    return name_dict
        
# Function to import pitch type percentages for MLB pitchers 
# Input: time range (overall, month or 2weeks) and date corresponding to date of mathcup generation
# Output: pd dataframe with corrseponding data
def pitch_percentage_pitchers(spec,date):
    formatted_date = date[:4]+'-'+date[4:6]+'-'+date[6:]
    dt = datetime.strptime(formatted_date, '%Y-%m-%d')
    if spec == 'overall':
        min_IP = 20
        gen_url = f'https://www.fangraphs.com/leaders-legacy.aspx?pos=all&stats=pit&lg=all&qual={min_IP}&type=9&season=2023&month=0&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&page=1_50&startdate=2023-03-01&enddate={formatted_date}'
    elif spec == 'month':
        min_IP = 5
        month_dt = dt - timedelta(days=30)
        month_date_string = month_dt.strftime('%Y-%m-%d')
        gen_url = f'https://www.fangraphs.com/leaders-legacy.aspx?pos=all&stats=pit&lg=all&qual={min_IP}&type=9&season=2023&month=3&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&page=1_50&startdate={month_date_string}&enddate={formatted_date}'
    elif spec == '2weeks':
        min_IP = 1
        week2_dt = dt - timedelta(days=14)
        week2_date_string = week2_dt.strftime('%Y-%m-%d')
        gen_url = f'https://www.fangraphs.com/leaders-legacy.aspx?pos=all&stats=pit&lg=all&qual={min_IP}&type=9&season=2023&month=2&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&page=1_50&startdate={week2_date_string}&enddate={formatted_date}'
        
    # if spec == 'overall':
    #     gen_url = 'https://www.fangraphs.com/leaders-legacy.aspx?pos=all&stats=sta&lg=all&qual=20&type=9&season=2023&month=0&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&page=1_50&startdate=2023-03-01&enddate='+formatted_date
    # elif spec == 'month':
    #     month_dt = dt - timedelta(days=30)
    #     month_date_string = month_dt.strftime('%Y-%m-%d')
    #     gen_url = 'https://www.fangraphs.com/leaders-legacy.aspx?pos=all&stats=sta&lg=all&qual=5&type=9&season=2023&month=3&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&page=1_50&startdate='+month_date_string+'&enddate='+formatted_date
    # elif spec == '2weeks':
    #     week2_dt = dt - timedelta(days=30)
    #     week2_date_string = week2_dt.strftime('%Y-%m-%d')
    #     gen_url = 'https://www.fangraphs.com/leaders-legacy.aspx?pos=all&stats=sta&lg=all&qual=1&type=9&season=2023&month=2&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&page=1_50&startdate='+week2_date_string+'&enddate='+formatted_date

    soup = reg_url_to_soup(gen_url)
    return reg_soup_to_pd(soup)
   
# Function to get batter advanced stats based on pitcher handedness
# Input: hand ('R' for right, 'L' for left and 'N' for overall)
# Output: pandas table with data    
def batter_advanced_stats(hand):
    if hand == 'R':
        gen_url = 'https://www.fangraphs.com/leaders-legacy.aspx?pos=all&stats=bat&lg=all&qual=80&type=1&season=2023&month=14&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&pagenum=1&pageitems=2000000000startdate=&enddate='
        #gen_url = 'https://www.fangraphs.com/leaders/splits-leaderboards?splitArr=2&splitArrPitch=&position=B&autoPt=false&splitTeams=false&statType=player&statgroup=2&startDate=2023-03-01&endDate=2023-11-01&players=&filter=PA%7Cgt%7C80&groupBy=season&wxTemperature=&wxPressure=&wxAirDensity=&wxElevation=&wxWindSpeed=&sort=22,1&pageitems=2000000000&pg=0'
    elif hand == 'L':
        gen_url = 'https://www.fangraphs.com/leaders-legacy.aspx?pos=all&stats=bat&lg=all&qual=40&type=1&season=2023&month=13&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&pagenum=1&pageitems=2000000000startdate=2023-01-01&enddate=2023-12-31'
        #gen_url = 'https://www.fangraphs.com/leaders/splits-leaderboards?splitArr=1&splitArrPitch=&position=B&autoPt=false&splitTeams=false&statType=player&statgroup=2&startDate=2023-03-01&endDate=2023-11-01&players=&filter=PA%7Cgt%7C40&groupBy=season&wxTemperature=&wxPressure=&wxAirDensity=&wxElevation=&wxWindSpeed=&sort=22,1&pageitems=2000000000&pg=0'
    elif hand == 'N':
        gen_url = 'https://www.fangraphs.com/leaders-legacy.aspx?pos=all&stats=bat&lg=all&qual=100&type=8&season=2023&month=0&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&pagenum=1&pageitems=2000000000startdate=&enddate='
        #gen_url = 'https://www.fangraphs.com/leaders/splits-leaderboards?splitArr=&splitArrPitch=&position=B&autoPt=false&splitTeams=false&statType=player&statgroup=2&startDate=2023-03-01&endDate=2023-11-01&players=&filter=PA%7Cgt%7C100&groupBy=season&wxTemperature=&wxPressure=&wxAirDensity=&wxElevation=&wxWindSpeed=&sort=22,1&pageitems=2000000000&pg=0'

    soup = url_to_soup(gen_url)
    table = soup.find('div',class_='leaders-major_leaders-major__table__BLZyw').find('table')
    data = extract_pd(table)
    data['OPS'] = data['OBP'] + data['SLG']
    return data  

# Extra parameter to account for left/right matchups
# Holds names of batters and their OPS vs (R or L) / OPS overall
# Input: None
# Output: pandas table with names and corresponding data
def handedness_adjustment():
    # Parameter = multiplier of proportion of pa on each side times proportion difference in OPS
    normal = batter_advanced_stats('N')[['Name','PA','OPS']]
    left = batter_advanced_stats('L')[['Name','PA','OPS']]
    right = batter_advanced_stats('R')[['Name','PA','OPS']]
    [df.set_index('Name',inplace=True) for df in [normal,left,right]]
    multipliers = pd.DataFrame(index = normal.index)
    # multipliers.set_index(normal.index, inplace=True)
    # For later: ((left['PA']/normal['PA'])+1)
    multipliers['L'] =  (left['OPS']/normal['OPS'])
    multipliers['R'] = (right['OPS']/normal['OPS'])
    return multipliers

# MAIN FUNCTION
# From team and pitcher input, function gets metric for each player
# Input: team(ex. SFG), pitcher(ex. Justin Verlander), date(YYYYMMDD)
# Output: pandas table with names of team's batters and their corresponding metric
def matchup(team,pitcher,date):
    # Make empty output
    out = pd.DataFrame()
    # Account for different options in metric
    options = ['overall','month','2weeks']
    # Tables saved into pickle for reuse
    for option in options:
        # Pitcher Pitch percentages
        if os.path.exists(CWD+PKL+date+'pitcher_pitches_'+option+'.pkl'):
            with open(CWD+PKL+date+'pitcher_pitches_'+option+'.pkl', 'rb') as file:
                pitcher_pitches = pickle.load(file)
        else:
            pitcher_pitches = pitch_percentage_pitchers(option,date)
            with open(CWD+PKL+date+'pitcher_pitches_'+option+'.pkl', 'wb') as file:
                pickle.dump(pitcher_pitches, file)
                
        # Pitcher Pitch values
        if os.path.exists(CWD+PKL+date+'pitcher_values_'+option+'.pkl'):
            with open(CWD+PKL+date+'pitcher_values_'+option+'.pkl', 'rb') as file:
                pitcher_values = pickle.load(file)
        else:
            pitcher_values = pitch_values_pitchers(option,date)
            with open(CWD+PKL+date+'pitcher_values_'+option+'.pkl', 'wb') as file:
                pickle.dump(pitcher_values, file)
        
        pitcher_special_cases = ['Jose Quintana','Xzavion Curry','Pablo Lopez','Jose Berrios','Erasmo Ramirez']
        if pitcher == pitcher_special_cases[0]:
            pitcher = 'José Quintana'
        elif pitcher == pitcher_special_cases[2]:
            pitcher == 'Pablo López'
        elif pitcher == pitcher_special_cases[3]:
            pitcher = 'José Berríos'
        elif pitcher == pitcher_special_cases[4]:
            pitcher = 'Erasmo Ramírez'
            
        if pitcher == pitcher_special_cases[1] and option == 'overall':
            sp_url = 'https://www.fangraphs.com/leaders-legacy.aspx?pos=all&stats=sta&lg=all&qual=0&type=8&season=2023&month=0&season1=2023&ind=0&team=5&rost=0&age=0&filter=&players=0&startdate=20230101&enddate='+date
            soup = url_to_soup(sp_url)
            table = soup.find('div',class_='leaders-major_leaders-major__table__BLZyw').find('table')
            sp_data = extract_pd(table)
            pitches = sp_data[sp_data['Name'] == pitcher]
        else:
            #Get pitches disitribution table for specific pitcher
            pitches = pitcher_pitches[pitcher_pitches['Name'] == pitcher]

        # If one of the timeframes does not have the pitcher, skip
        # If pitcher not being taken into account message will print
        if pitches.empty:
            if option == 'overall':
                print(pitcher,"not eligible for",option)
        else:
            # Get pitch value per pitch table for specific pitcher (set up as pitch value per 100 pitches) 
            values = pitcher_values[pitcher_values['Name'] == pitcher]
            # Make dict with pitcher coefficients 
            # Here, pitcher coefficients made by multiplying pitch distribution by their corrsponding values per pitch
            pitcher_ratings = {}
            for col in values.columns[3:]:
                pitch = col[1:3]
                val = col[1:3] + '%'
                p = pitches.iloc[0, pitches.columns.get_loc(val)]
                # Some pitches are not thrown by some pitchers, so NaN value is assigned. This if aacounts for those NaNs
                if pd.isna(p):
                    pitcher_ratings[pitch] = 0
                else:
                    pitcher_ratings[pitch] = float(p[:-1]) * (0.01) * float(values.iloc[0, values.columns.get_loc(col)])
            
            # Get pitch values for batters
            if os.path.exists(CWD+PKL+date+'batter_values_'+option+'.pkl'):
                with open(CWD+PKL+date+'batter_values_'+option+'.pkl', 'rb') as file:
                    temp_table = pickle.load(file)
            else:
                temp_table = batter_pitch_values(option,date)
                with open(CWD+PKL+date+'batter_values_' + option+'.pkl', 'wb') as file:
                    pickle.dump(temp_table, file)
            
            # Get table for specific team
            batter_values = temp_table[(temp_table['Team']==team) | (temp_table['Team']=='2 Tms')]
            # Make dict with pitcher coefficients
            batter_ratings = {}
            # Iterate on team's players
            with open(CWD+PKL+'team_depth_charts.pkl','rb') as file:
                team_depth_chart = pickle.load(file)   
            for player in team_depth_chart[team]:
                # Get batter pitch values
                pla = batter_values[batter_values['Name']==player]
                if not pla.empty:
                    # Get dict with pitch types and coefficient
                    ratings = {}
                    # Here, batter coefficients made by multiplying opposing pitcher pitch distribution by their corrsponding values per pitch
                    for col in values.columns[3:]:
                        pitch = col[1:3]
                        val = col[1:3] + '%'
                        b = pitches.iloc[0, pitches.columns.get_loc(val)]
                        if pd.isna(b)|pd.isna(b):
                            ratings[pitch] = 0
                        else:
                            ratings[pitch] = float(b[:-1]) * (0.01) * float(pla.iloc[0, pla.columns.get_loc(col)])
                    batter_ratings[player] = ratings
                # Some players are not found, so display error message
                else:
                    if option == 'overall':
                        print(option,'player not found:', player)
            
    
            # Convert to ratings dicts to pandas tables
            pitcher_df = pd.DataFrame([pitcher_ratings]) 
            batters_df = pd.DataFrame(batter_ratings).T 
            # Subtract pitcher coeffficients from batters
            dat = batters_df.sub(pitcher_df.iloc[0],axis = 'columns')            
            # Make output dataframe with coefficients
            out[option] = dat.sum(axis=1)
            out['Pitcher'] = pitcher

    return out

# Function to get days team vs. pitcher matchups
# Input: date(YYYY/MM/DD)
# Output: list of dicts with games, classified as home/away and pitcher/team per matchup
def day_matchups(date): # Date format: YYYY/MM/DD
    today = datetime.today().date()
    url = 'https://www.espn.com/mlb/scoreboard/_/date/'+date
    open_url = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(open_url,'lxml')
    remove_susp = soup.find_all('section',class_='Card gameModules')[-1]
    sections = remove_susp.find_all('section', class_='Scoreboard bg-clr-white flex flex-auto justify-between')
    games = []
    for section in sections:
        home = {'Team':section.find_all('a')[3].text,'Pitcher':None}
        away = {'Team':section.find_all('a')[1].text,'Pitcher':None}
        if datetime.strptime(date, '%Y%m%d').date() < today:
            temp = section.find('div',class_='Scoreboard__Callouts flex items-center mv4 flex-column').find_all('a')
            if len(temp)>2:
                game_url = 'https://www.espn.com' + temp[1].get('href')
                open_game_url = urllib.request.urlopen(game_url).read()
                soup2 = BeautifulSoup(open_game_url,'lxml')
                temp = soup2.find_all('div',class_='ResponsiveTable ResponsiveTable--fixed-left')
                away['Pitcher'] = temp[3].find_all('a')[0].text
                home['Pitcher'] = temp[4].find_all('a')[0].text
        else:
            temp = section.find('div',class_='Scoreboard__Column ph4 mv4 Scoreboard__Column--3').find_all('span',class_='Athlete__PlayerName')
            home['Pitcher'], away['Pitcher'] = temp[1].text, temp[0].text
        games.append({'home':home,"away":away})
    return games
#print(day_matchups('20230822'))

# Function to make dictionary with pitchers and their handedness
# Input: None
# Output: None (function saves dict as pickle)
def make_pitcher_handedness_pickle():
    temp_dict = {}
    L_filename = "Splits Leaderboard Data as SP as LHP.csv"
    L_table = pd.read_csv(L_filename)
    for i in L_table['Name']:
        temp_dict[i] = 'L'
        
    R_filename = "Splits Leaderboard Data as SP as RHP.csv"
    R_table = pd.read_csv(R_filename)
    for i in R_table['Name']:
        temp_dict[i] = 'R'
    with open(CWD+PKL+'pitcher_handedness.pkl', 'wb') as file:
        pickle.dump(temp_dict, file)


# Function to get rankings of a day
# Input: date YYYYMMDD
# Output: pandas table with day's coefficients
def day_rankings(date):
    # Import day matchups
    games = day_matchups(date)
    #print('games:',games)
    # Initialize output
    output = pd.DataFrame()
    # Import pitcher names dict
    if os.path.exists(CWD+PKL+'pitcher_names.pkl'):
        with open(CWD+PKL+'pitcher_names.pkl', 'rb') as file:
            name_dict = pickle.load(file)
    else:
        name_dict = make_pitcher_names_dict(date)
    # Iterate on games
    for game in games:
        print("in:",game)
        # Get team names and opposing pitchers
        t1,t2 = name_to_abb[game['home']['Team']], name_to_abb[game['away']['Team']]
        p1,p2 = name_dict[game['home']['Pitcher']] if game['home']['Pitcher'] in name_dict else 'not found', name_dict[game['away']['Pitcher']] if game['away']['Pitcher'] in name_dict else 'not found'
        # Dict will act as filter for pitchers, so matchup returned for wualified pitchers
        # Get individual game matchups and concatenate all together
        if p2 != 'not found':
            t1_p2 = matchup(t1,p2,date)
            t1_p2['Team'] = t1
            output = pd.concat([output,t1_p2])
        if p1 != 'not found':
            t2_p1 = matchup(t2,p1,date)
            t2_p1['Team'] = t2
            output = pd.concat([output,t2_p1])
            
    output.reset_index(inplace=True)
    output.rename(columns={'index': 'Name'}, inplace=True)
    return output

# Function to extract box scores for batters
# Input: date(YYYYMMDD)
# Output: pandas table with data
def hitter_box_scores(date):
    date_format = date[:4] + '-' + date[4:6] + '-' + date[6:]
    url = 'https://www.fangraphs.com/leaders-legacy.aspx?pos=all&stats=bat&lg=all&qual=0&type=0&season=2023&month=1000&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&page=1_50&startdate='+date_format+'&enddate='+date_format
    soup = url_to_soup(url)
    table = soup.find('div',class_='leaders-major_leaders-major__table__BLZyw').find('table')
    data = extract_pd(table)    
    return data

# EXAMPLE
# Function to extract advanced stats for batters, up to specified date
# Input: date(YYYYMMDD)
# Output: pandas table with data
def hitter_full_advanced_stats(date):
    input_date = datetime.strptime(date, '%Y%m%d')
    output_date = input_date - timedelta(days=1)
    date_format = output_date.strftime('%Y-%m-%d')
    url = 'https://www.fangraphs.com/leaders/major-league?pos=all&stats=bat&lg=all&qual=100&type=1&season=2023&month=1000&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&page=1_50&pageitems=2000000000&startdate=2023-03-01&enddate='+date_format

    driver = webdriver.Chrome()
    driver.get(url)
    time.sleep(1) 
    html = driver.page_source
    driver.quit()
 
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('div',class_='leaders-major_leaders-major__table__BLZyw').find('table')
    data = extract_pd(table)
    return data

# Function to get betting outcomes in pndas table as opposed to standard box scores
# Input: date(YYYYMMDD)
# Output: pandas table with data, columns specified in function and can be changed
def hitter_fantasy(date):
    data = hitter_box_scores(date)
    data.drop(columns = ['SF','SH','GDP','AVG'],axis=1,inplace=True)
    fantasy_formula = lambda row: 3*row['1B'] + 5*row['2B'] + 8*row['3B'] + 10*row['HR'] + 2*row['R'] + 2*row['RBI'] + 2*row['BB'] + 5*row['SB']+2*row['HBP']
    H_R_RBI_formula = lambda row: row['H'] + row['R'] + row['RBI'] 

    data['Fantasy Score'] = data.apply(fantasy_formula, axis=1)
    data['H+R+RBI'] = data.apply(H_R_RBI_formula, axis=1)
    # output[['H','1B','2B','3B']] = data[['H','1B','2B','3B']]
    data['TB'] = data['1B'] + 2*data['2B'] + 3*data['3B']
    # output[['IBB','BB']] = data[['IBB','BB']]
    data['TBB'] = data['BB'] + data['IBB']
    #print(data.head())
    return data

#hitter_fantasy('20230717').to_csv('C://Users/tomas/OneDrive/Desktop/Sports/MLB/Results/test.csv')

def pitcher_stats(date):
    date_format = date[:4] + '-' + date[4:6] + '-' + date[6:]
    url = 'https://www.fangraphs.com/leaders.aspx?pos=all&stats=sta&lg=all&qual=20&type=1&season=2023&month=0&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&page=1_50&startdate=2023-01-01&enddate='+date_format
    soup = url_to_soup(url)

    table = soup.find('div',class_='leaders-major_leaders-major__table__BLZyw').find('table')
    data = extract_pd(table)

    return data

#print(pitcher_stats('20230801'))
# Function to generate coefficients for a date
# Input: date(YYYYMMDD), boolean to save or not
# Output: prints table and saves it as file, depending on input option
def generate_coefficients(date,save):
    # Get batter stats
    # adv_stats = hitter_full_advanced_stats(date)
    # adv_stats.drop(columns=['ISO','Spd','BABIP','UBR','BB/K'],inplace=True)
    # adv_stats.set_index('Name',inplace=True)
    # # Get pitcher stats
    # pitcher_data = pitcher_stats(date)
    # pitcher_data.drop(columns=['K/9','BB/9','K/BB','ERA-','FIP-','xFIP-','E-F','SIERA'],inplace=True)
    # pitcher_data.set_index('Name',inplace=True)
    # # Filter for pitchers playing today
    # if os.path.exists(CWD+PKL+'pitcher_names.pkl'):
    #     with open(CWD+PKL+'pitcher_names.pkl', 'rb') as file:
    #         name_dict = pickle.load(file)
    # else:
    #     name_dict = make_pitcher_names_dict(date)
    # matchups = day_matchups(date)
    # pitchers = []
    # for game in matchups:
    #     if game['away']['Pitcher'] in name_dict.keys():
    #         pitchers.append(name_dict[game['away']['Pitcher']])
    #     if game['home']['Pitcher'] in name_dict.keys():    
    #         pitchers.append(name_dict[game['home']['Pitcher']])
    # pitcher_data = pitcher_data[pitcher_data.index.isin(pitchers)]
    # pitcher_data.index.name = 'Pitcher'
    day_rank = day_rankings(date)
    day_rank.set_index('Name',inplace=True)
    output = day_rank
    
    # common_indices = day_rank.index.intersection(adv_stats.index)
    # output = pd.concat([day_rank.loc[common_indices],adv_stats.loc[common_indices]],axis=1)
    
    # output = output.merge(pitcher_data, left_on='Pitcher', right_index=True)
    # output = output.rename(columns={'Team_x': 'Team', 'BB%_x': 'HBB%','K%_x': 'HK%','BB%_y': 'PBB%','K%_y': 'PK%','AVG_y':'BAA','AVG_x':'AVG'})    
    # output.drop(output.columns[[5,19,30]], axis=1,inplace=True)
    print(output)
    if save:
        output.to_csv(CWD+'/Toto Metric/V2/test/Coefficients_'+date+'_V2.csv', index=True)
        print('file saved:',CWD+'/Toto Metric/V2/test/Coefficients_'+date+'_V2.csv')
generate_coefficients('20230823',save=False)

def generate_date_range(start_date_str, end_date_str):
    date_format = "%Y%m%d"
    start_date = datetime.strptime(start_date_str, date_format)
    end_date = datetime.strptime(end_date_str, date_format)
    
    date_list = []
    current_date = start_date
    
    while current_date <= end_date:
        date_list.append(current_date.strftime(date_format))
        current_date += timedelta(days=1)
    
    return date_list

def generate_many_coefficients(date1,date2,save):
    dates = generate_date_range(date1,date2)
    for date in dates:
        generate_coefficients(date, save)
#generate_many_coefficients('20230728','20230731',save=True)

# Helper functions for probability generation
def probability_to_american(probability):
    if probability < 0.5:
        american_odds = (1 / probability - 1) * 100
    else:
        american_odds = (-1) * (probability / (1 - probability)) * 100
    return american_odds

def predict_probabilities(row,model):
        row_for_prediction = row[['overall','AVG','OBP','OPS','wRC','wRAA','wOBA']]
        entry_for_prediction = np.array([row_for_prediction.values])
        #entry_for_prediction = np.array([tuple(row_for_prediction)], dtype=[(col, '<f8') for col in row_for_prediction.index])
        predicted_probabilities = model.predict_proba(entry_for_prediction)
        return predicted_probabilities[0]
    
# Generate probabilities
def generate_prob(date):
    filename = CWD+'/Toto Metric/V2/Coefficients_'+date+'_V2.csv'
    data = pd.read_csv(filename,index_col='Name')
    data = data[data['overall']>2]
    full_data=data[['Team','overall','OPS','AVG','OBP']]
    data = data[['overall','AVG','OBP','OPS','wRC','wRAA','wOBA']]
    data.dropna(inplace=True)
    full_data.dropna(inplace=True)
    
    #models={}
    options = [('HRRBI',1.5),('HRRBI',2.5),('TB',1.5),('HR',0.5)]
    for (OU_type,OU_number) in options:
        with open(f'Models/log_reg_model_{OU_type}{OU_number}_coef_2_MR.pkl', 'rb') as model_file:
            model = pickle.load(model_file)
            full_data[OU_type + str(OU_number)+"U"],full_data[OU_type + str(OU_number)+"O"] = zip(*data.apply(predict_probabilities,args=(model,), axis=1))
    
    #full_data['H+R+RBI 1.5U'], full_data['H+R+RBI 1.5O'] = zip(*data.apply(predict_probabilities, axis=1))
    # full_data['HRRBI 1.5O Line'] = full_data['HRRBI1.5O'].apply(probability_to_american)
    # full_data['HRRBI 1.5U Line'] = full_data['HRRBI1.5U'].apply(probability_to_american)
    full_data.to_csv(f'{CWD}/Toto Metric/Predictions/predictions_{date}_all_MR.csv')
    print(full_data)

#generate_prob('20230817')
    
    