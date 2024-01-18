# MLB Folder

This folder contains scripts and data related to Major League Baseball (MLB) analysis.

## Files

- `Baseball.py`: This is the main script for analyzing baseball data. It includes functions for creating pitcher name dictionaries, iterating over games, and generating individual game matchups.

### Baseball.py

The script `Baseball.py` is designed to analyze baseball data. It works by creating a dictionary of pitcher names for a given date, then iterating over a list of games. For each game, it retrieves the team names and the names of the opposing pitchers. If the pitcher's name is found in the dictionary, it retrieves the individual game matchups for that pitcher and concatenates them together. The output is a pandas DataFrame that includes the team name and the individual game matchups for each pitcher that was found in the dictionary. The matchups are shown by batter, so every row includes a batter and their team, the corresponding pitcher and their team, and the numreic metric value.
