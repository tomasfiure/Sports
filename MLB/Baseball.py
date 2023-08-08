from bs4 import BeautifulSoup
import urllib
import pandas as pd
from copy import copy
import unicodedata
import pickle
import os
from datetime import datetime, timedelta

# Macro for current working directory
CWD = os.getcwd()
print('r'+CWD)
# Macro to store pickles
PKL = '\\pkl storage\\'
# Libary with full names and acronyms
abb_to_name = {'ARI': 'Diamondbacks', 'ATL': 'Braves', 'BAL': 'Orioles', 'BOS': 'Red Sox', 'CHC': 'Cubs', 'CHW': 'White Sox', 'CIN': 'Reds', 'CLE': 'Guardians', 'COL': 'Rockies', 'DET': 'Tigers', 'HOU': 'Astros', 'KCR': 'Royals', 'LAA': 'Angels', 'LAD': 'Dodgers', 'MIA': 'Marlins', 'MIL': 'Brewers', 'MIN': 'Twins', 'NYM': 'Mets', 'NYY': 'Yankees', 'OAK': 'Athletics', 'PHI': 'Phillies', 'PIT': 'Pirates', 'SDP': 'Padres', 'SEA': 'Mariners', 'SFG': 'Giants', 'STL': 'Cardinals', 'TBR': 'Rays', 'TEX': 'Rangers', 'TOR': 'Blue Jays', 'WSN': 'Nationals'}
name_to_abb = {value: key for key, value in abb_to_name.items()}  
  
# Helper funtion to retreive links to team depth charts
# Input: None
# Output: {team name: team link} (ex. {'Braves': 'fangraphs.com...'}) 
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

# Access a team's schedule and basic matchup info 
# Note for use: team name first letter should be capitalized
# Input: team name(ex. Giants)
# Output: pandas table with team  with other information like date and starting pitchers
def access_team_schedule(team):
    url = 'https://www.fangraphs.com/teams/' + team + '/schedule'
    open_url = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(open_url,'lxml')
    table = soup.find('div', class_='team-schedule-table')
    pandas_table = pd.read_html(str(table))[0]
    pandas_table = pandas_table.drop('Unnamed: 1', axis=1)
    return pandas_table

# Function to access a team's depth chart
# Input: team name(ex. Giants)
# Output: Team's depth chart, function has min PA paramater to filter depth chart
def access_team_depth_chart(team):
    link = team_links()[team]
    if link[-2] == '=':
        team_number = link[-1]
    else:
        team_number = link[-2:]
    min_PA = 100
    url = 'https://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&lg=all&qual='+str(min_PA)+'&type=8&season=2023&month=0&season1=2023&ind=0&team='+team_number+'&rost=&age=&filter=&players=&'
    #print(url)
    open_url = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(open_url,'lxml')
    table = soup.find('table', class_='rgMasterTable')
    data = extract_pd(table)
    players=[]
    for player in data['Name']:
        players.append(player)
    return players

# Helper function to extract a pd dataframe from inputted html table code in fan graphs 
# Input: table div in html
# Output: pd dataframe corresponding to table
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
# Input: time range (overall, month or 2weeks) and date corresponding to date of mathcup generation
# Output: pd dataframe with corresponding data
def pitch_values(spec,date):
    formatted_date = date[:4]+'-'+date[4:6]+'-'+date[6:]
    dt = datetime.strptime(formatted_date, '%Y-%m-%d')
    if spec == 'overall':
        gen_url = 'https://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&lg=all&qual=100&type=14&season=2023&month=0&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&startdate=2023-03-01&enddate='+formatted_date
    elif spec == 'month':
        month_dt = dt - timedelta(days=30)
        month_date_string = month_dt.strftime('%Y-%m-%d')
        gen_url = 'https://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&lg=all&qual=10&type=14&season=2023&month=3&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&startdate='+month_date_string+'&enddate='+formatted_date
    elif spec == '2weeks':
        week2_dt = dt - timedelta(days=14)
        week2_date_string = week2_dt.strftime('%Y-%m-%d')
        gen_url = 'https://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&lg=all&qual=10&type=14&season=2023&month=2&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&startdate='+week2_date_string+'&enddate='+formatted_date
        
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

# Funtion to return a hitter percentile vs. different pitch types
# Input: time range (overall, month or 2weeks) and date corresponding to date of mathcup generation
# Output: pd dataframe with corresponding data
def hitter_pv_percentiles(hitter):
    data = pitch_values()
    total = len(data)
    print(hitter)
    for col in data.columns[3:]:
        sorted_data = data.sort_values(by=col).reset_index(drop=True)
        player = sorted_data[sorted_data['Name'] == hitter]
        index = player.index[0]
        print('Pitch Type:', col, 'Percentile:',(index/total)*100)
    
# Function to import pitch value data for all MLB hitters
# Input: time range (overall, month or 2weeks) and date corresponding to date of mathcup generation
# Output: pd dataframe with corrseponding data
def pitch_values_pitchers(spec,date):
    formatted_date = date[:4]+'-'+date[4:6]+'-'+date[6:]
    dt = datetime.strptime(formatted_date, '%Y-%m-%d')
    if spec == 'overall':
        gen_url = 'https://www.fangraphs.com/leaders.aspx?pos=all&stats=pit&lg=all&qual=20&type=14&season=2023&month=0&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&startdate=2023-03-01&enddate='+formatted_date
    elif spec == 'month':
        month_dt = dt - timedelta(days=30)
        month_date_string = month_dt.strftime('%Y-%m-%d')
        gen_url = 'https://www.fangraphs.com/leaders.aspx?pos=all&stats=pit&lg=all&qual=5&type=14&season=2023&month=3&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&startdate='+month_date_string+'&enddate='+formatted_date
        #gen_url = 'https://www.fangraphs.com/leaders.aspx?pos=all&stats=pit&lg=all&qual=30&type=14&season=2023&month=0&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&startdate=2023-03-01&enddate='+formatted_date
    elif spec == '2weeks':
        week2_dt = dt - timedelta(days=14)
        week2_date_string = week2_dt.strftime('%Y-%m-%d')
        gen_url = 'https://www.fangraphs.com/leaders.aspx?pos=all&stats=pit&lg=all&qual=1&type=14&season=2023&month=2&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&startdate='+week2_date_string+'&enddate='+formatted_date
        #gen_url = 'https://www.fangraphs.com/leaders.aspx?pos=all&stats=pit&lg=all&qual=30&type=14&season=2023&month=0&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&startdate=2023-03-01&enddate='+formatted_date
    
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
        gen_url = 'https://www.fangraphs.com/leaders.aspx?pos=all&stats=sta&lg=all&qual=20&type=9&season=2023&month=0&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&startdate=2023-03-01&enddate='+formatted_date
    elif spec == 'month':
        month_dt = dt - timedelta(days=30)
        month_date_string = month_dt.strftime('%Y-%m-%d')
        gen_url = 'https://www.fangraphs.com/leaders.aspx?pos=all&stats=pit&lg=all&qual=5&type=9&season=2023&month=3&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&startdate='+month_date_string+'&enddate='+formatted_date
        #gen_url = 'https://www.fangraphs.com/leaders.aspx?pos=all&stats=sta&lg=all&qual=30&type=9&season=2023&month=0&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&startdate=2023-03-01&enddate='+formatted_date
    elif spec == '2weeks':
        week2_dt = dt - timedelta(days=30)
        week2_date_string = week2_dt.strftime('%Y-%m-%d')
        gen_url = 'https://www.fangraphs.com/leaders.aspx?pos=all&stats=sta&lg=all&qual=1&type=9&season=2023&month=2&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&startdate='+week2_date_string+'&enddate='+formatted_date
        #gen_url = 'https://www.fangraphs.com/leaders.aspx?pos=all&stats=sta&lg=all&qual=30&type=9&season=2023&month=0&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&startdate=2023-03-01&enddate='+formatted_date
    
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

# Function to remove tildes from names for processing
# Input: name
# Output: name without special characters
def remove_tildes(input_string):
    # Normalize the input string to decomposed form (NFD)
    normalized_string = unicodedata.normalize('NFD', input_string)
    # Remove combining characters (diacritical marks) like tildes
    cleaned_string = ''.join(char for char in normalized_string if not unicodedata.combining(char))
    return cleaned_string
   
# Function to get batter advanced stats based on pitcher handedness
# Input: hand ('R' for right, 'L' for left and 'N' for overall)
# Output: pandas table with data    
def batter_advanced_stats(hand):
    if hand == 'R':
        gen_url = 'https://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&lg=all&qual=80&type=1&season=2023&month=14&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&startdate=&enddate='
        #gen_url = 'https://www.fangraphs.com/leaders/splits-leaderboards?splitArr=2&splitArrPitch=&position=B&autoPt=false&splitTeams=false&statType=player&statgroup=2&startDate=2023-03-01&endDate=2023-11-01&players=&filter=PA%7Cgt%7C80&groupBy=season&wxTemperature=&wxPressure=&wxAirDensity=&wxElevation=&wxWindSpeed=&sort=22,1&pageitems=2000000000&pg=0'
    elif hand == 'L':
        gen_url = 'https://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&lg=all&qual=40&type=1&season=2023&month=13&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&startdate=2023-01-01&enddate=2023-12-31'
        #gen_url = 'https://www.fangraphs.com/leaders/splits-leaderboards?splitArr=1&splitArrPitch=&position=B&autoPt=false&splitTeams=false&statType=player&statgroup=2&startDate=2023-03-01&endDate=2023-11-01&players=&filter=PA%7Cgt%7C40&groupBy=season&wxTemperature=&wxPressure=&wxAirDensity=&wxElevation=&wxWindSpeed=&sort=22,1&pageitems=2000000000&pg=0'
    elif hand == 'N':
        gen_url = 'https://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&lg=all&qual=100&type=8&season=2023&month=0&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&startdate=&enddate='
        #gen_url = 'https://www.fangraphs.com/leaders/splits-leaderboards?splitArr=&splitArrPitch=&position=B&autoPt=false&splitTeams=false&statType=player&statgroup=2&startDate=2023-03-01&endDate=2023-11-01&players=&filter=PA%7Cgt%7C100&groupBy=season&wxTemperature=&wxPressure=&wxAirDensity=&wxElevation=&wxWindSpeed=&sort=22,1&pageitems=2000000000&pg=0'

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
        if os.path.exists(CWD+PKL+'pitcher_pitches_'+option+'.pkl'):
            with open(CWD+PKL+'pitcher_pitches_'+option+'.pkl', 'rb') as file:
                pitcher_pitches = pickle.load(file)
        else:
            pitcher_pitches = pitch_percentage_pitchers(option,date)
            with open(CWD+PKL+'pitcher_pitches_'+option+'.pkl', 'wb') as file:
                pickle.dump(pitcher_pitches, file)
                
        # Pitcher Pitch values
        if os.path.exists(CWD+PKL+'pitcher_values_'+option+'.pkl'):
            with open(CWD+PKL+'pitcher_values_'+option+'.pkl', 'rb') as file:
                pitcher_values = pickle.load(file)
        else:
            pitcher_values = pitch_values_pitchers(option,date)
            with open(CWD+PKL+'pitcher_values_'+option+'.pkl', 'wb') as file:
                pickle.dump(pitcher_values, file)
    
        # Get pitches disitribution table for specific pitcher
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
            if os.path.exists(CWD+PKL+'batter_values_'+option+'.pkl'):
                with open(CWD+PKL+'batter_values_'+option+'.pkl', 'rb') as file:
                    temp_table = pickle.load(file)
            else:
                temp_table = pitch_values(option,date)
                with open(CWD+PKL+'batter_values_' + option+'.pkl', 'wb') as file:
                    pickle.dump(temp_table, file)
            
            # Get table for specific team
            batter_values = temp_table[temp_table['Team']==team]
            # Make dict with pitcher coefficients
            batter_ratings = {}
            # Iterate on team's players
            for player in access_team_depth_chart(abb_to_name[team]):
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

    return out

# Function to get days team vs. pitcher matchups
# Input: date(YYYY/MM/DD)
# Output: list of dicts with games, classified as home/away and pitcher/team per matchup
def day_matchups(date): 
    url = 'https://www.espn.com/mlb/scoreboard/_/date/'+date
    open_url = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(open_url,'lxml')
    remove_susp = soup.find_all('section',class_='Card gameModules')[-1]
    sections = remove_susp.find_all('section', class_='Scoreboard bg-clr-white flex flex-auto justify-between')
    games = []
    for section in sections:
        home = {'Team':section.find_all('a')[3].text,'Pitcher':None}
        away = {'Team':section.find_all('a')[1].text,'Pitcher':None}
        temp = section.find('div',class_='Scoreboard__Column ph4 mv4 Scoreboard__Column--3').find_all('span',class_='Athlete__PlayerName')
        home['Pitcher'], away['Pitcher'] = temp[1].text, temp[0].text
        games.append({'home':home,"away":away})
    return games

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
    url = 'https://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&lg=all&qual=0&type=0&season=2023&month=1000&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&startdate='+date_format+'&enddate='+date_format
    open_url = urllib.request.urlopen(url).read()
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

# Function to get betting outcomes in pndas table as opposed to standard box scores
# Input: date(YYYYMMDD)
# Output: pandas table with data, columns specified in function and can be changed
def hitter_fantasy(date):
    data = hitter_box_scores(date)
    data = data.drop(['HBP','SF','SH','GDP'],axis=1)
    fantasy_formula = lambda row: 3*row['1B'] + 5*row['2B'] + 8*row['3B'] + 10*row['HR'] + 2*row['R'] + 2*row['RBI'] + 2*row['BB'] + 5*row['SB'] 
    H_R_RBI_formula = lambda row: row['H'] + row['R'] + row['RBI'] 
    # Make new table
    output = pd.DataFrame()
    # Make new columns
    output['Name'] = data['Name']
    output['PA'] = data['PA']
    output['G'] = data['G']
    output['Fantasy Score'] = data.apply(fantasy_formula, axis=1)
    output['H+R+RBI'] = data.apply(H_R_RBI_formula, axis=1)
    return output

# Function to generate coefficients for a date
# Input: date(YYYYMMDD), boolean to save or not
# Output: prints table and saves it as file, depending on input option
def generate_coefficients(date,save):
    output = day_rankings(date)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    print(output)
    if save:
        output.to_csv(CWD+'/Toto Metric/V2/Coefficients_'+date+'_V2.csv', index=True)
generate_coefficients('20230808',save=False)

