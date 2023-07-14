import netCDF4 as nc
import requests
from bs4 import BeautifulSoup
import urllib
import pandas as pd
from copy import copy

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
#print(team_links('hello'))

# Access a team's schedule and basic matchup info 
def access_team_schedule(team):
    url = 'https://www.fangraphs.com/teams/' + team + '/schedule'
    open_url = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(open_url,'lxml')
    table = soup.find('div', class_='team-schedule-table')
    pandas_table = pd.read_html(str(table))[0]
    pandas_table = pandas_table.drop('Unnamed: 1', axis=1)
    return pandas_table

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
        #print('player:',player.text, 'link:', 'https://www.fangraphs.com/' + player.get('href'))
        players[player.text] = 'https://www.fangraphs.com/' + player.get('href')     
    return players
#print(access_team_depth_chart('Giants'))

# Helper function to extract a pd dataframe from inputted html table code 
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
    gen_url = 'https://www.fangraphs.com/leaders.aspx?pos=all&stats=pit&lg=all&qual=y&type=14&season=2023&month=0&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&startdate=2023-01-01&enddate=2023-12-31'
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
#print(pitch_values_pitchers())

def pitch_percentage_pitchers():
    gen_url = 'https://www.fangraphs.com/leaders.aspx?pos=all&stats=pit&lg=all&qual=y&type=9&season=2023&month=0&season1=2023&ind=0&team=0&rost=0&age=0&filter=&players=0&startdate=2023-01-01&enddate=2023-12-31'
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
print(pitch_percentage_pitchers())


