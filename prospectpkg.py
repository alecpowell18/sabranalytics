# Python script for projecting future value of prospect packages
# @Author: Alec Powell (atpowell@stanford.edu)
# 2015 Diamond Dollars Case Competition - SABR Analytics Conference
# @Date: March 4, 2015

import sqlite3
import sys

unique_players = []
all_top_prospects = []
COMPARABLE_THRESHOLD = 0.05

def is_pitcher(player_pos):
	if 'P' in player_pos:
		return True
	return False

def not_duplicate(value):
	if (value[0], value[1], value[2]) in unique_players:
		return False
	return True

def get_recent_stats(player_name, player_pos, age):
	max_games = 0
	to_return = tuple()
	t = (player_name, age,)
	if is_pitcher(player_pos):
		for row in cursor.execute('''SELECT * FROM master_pitching WHERE name=? AND age=?''', t):
			if row[3] > max_games:
				to_return = row
				max_games = row[3]
	else:
		for row in cursor.execute('''SELECT * FROM master_batting WHERE name=? AND age=?''', t):
			if row[3] > max_games:
				to_return = row
				max_games = row[3]
	return to_return

def get_level(teamStr):
	if "AAA" in teamStr:
		return "AAA"
	elif "AA" in teamStr:
		return "AA"
	elif "A+" in teamStr:
		return "A+"
	elif "A-" in teamStr:
		return "A-"
	else: return "A"

def get_comparable_players(stats_tup, player_pos):
	team = stats_tup[0]
	age_to_match = stats_tup[1]
	stat_to_match = float(stats_tup[2])
	level_to_match = get_level(team)
	rg_lower = float(stat_to_match - (COMPARABLE_THRESHOLD*stat_to_match))
	rg_upper = float(stat_to_match + (COMPARABLE_THRESHOLD*stat_to_match))
	range_tup = (rg_lower, rg_upper)
	to_return_set = []
	t = (age_to_match, rg_lower, rg_upper)
	if is_pitcher(player_pos):
		for row in cursor.execute('''SELECT * FROM master_pitching WHERE age=? AND fip>=? AND fip<=? ORDER BY fip ASC''', t):
			if level_to_match == get_level(row[1]):
				to_return_set.append(row)
	else:
		for row in cursor.execute('''SELECT * FROM master_batting WHERE age=? AND woba>=? AND woba<=? ORDER BY woba DESC''', t):
			if level_to_match == get_level(row[1]):
				to_return_set.append(row)
	return to_return_set

def show_comparables(comparables_set):
	prospects_to_return = []
	if len(comparables) > 1:
		for player in comparables:
			if player[0] != player_name and player[0] in all_top_prospects:
				prospects_to_return.append(player)
	return prospects_to_return

def get_seasons(service_time):
	st = str(service_time)
	num_seasons = int(st[:st.find('.')])
	decimal = float(int(st[st.find('.')+1:])/float(172))
	return float(num_seasons + decimal)

def prospect_query(prospect_name):
	#SQL query of all_top_prospects database
	#returns tuple (war, svc_time)
	t = (prospect_name,)
	for match in cursor.execute('''SELECT war, svc FROM top_prospects WHERE name=?''', t):
		# print prospect_name, "in MLB:", match[0], "WAR,", match[1], "SVC TIME."
		return (match[0], match[1])
	return tuple("","")

def player_value_raw(prospects):
	player_value = 0.0
	sums = 0.0
	if len(prospects) > 0:
		for prospect in prospects:
			if prospect[0] in all_top_prospects:
				query_tuple = prospect_query(prospect[0])
				careerWAR = query_tuple[0]
				career_seasons = get_seasons(float(query_tuple[1]))
				sums += float(careerWAR)/float(career_seasons)
			else:
				print "This player is not a former BA Top 10 prospect!!>>>>>>>", prospect
		player_value = float(sums)/float(len(prospects))
		print "PLAYER VALUE =", player_value
	return player_value

# def main(argv):
prospect_db = sqlite3.connect('data/prospect_db')
prospect_db.text_factory = str
#load data into database
cursor = prospect_db.cursor()
cursor.execute('''DROP TABLE IF EXISTS master_batting''')
cursor.execute('''
	CREATE TABLE master_batting(name TEXT, team TEXT, age INTEGER, woba DOUBLE, CONSTRAINT name_team PRIMARY KEY (name, team, age))
''')
cursor.execute('''DROP TABLE IF EXISTS master_pitching''')
cursor.execute('''
	CREATE TABLE master_pitching(name TEXT, team TEXT, age INTEGER, fip DOUBLE, CONSTRAINT name_team PRIMARY KEY (name, team, age))
''')
files = ['AAA_2014_master',
		'AA_2014_master',
		'A+_2014_master',
		'A_2014_master',
		'AAA_2013_master',
		'AA_2013_master',
		'A+_2013_master',
		'A_2013_master',
		'AAA_2012_master',
		'AA_2012_master',
		'A+_2012_master',
		'A_2012_master',
		'AAA_2011_master',
		'AA_2011_master',
		'A+_2011_master',
		'A_2011_master',
		'AAA_2010_master',
		'AA_2010_master',
		'A+_2010_master',
		'A_2010_master']
for master_filestr in files:
	actual_filestr_batting = "masters/" + master_filestr + "_batting.csv"
	actual_filestr_pitching = "masters/" + master_filestr + "_pitching.csv"
	with open(actual_filestr_batting,'r') as hf:
		for lines in hf:
			wOBA_idx = 0
			for line in lines.split('\r'):
				value = line.split(',')
				if value[0] == 'Name':
					for i in range(len(value)):
						if value[i] == 'wOBA':
							wOBA_idx = i
				elif not_duplicate(value):
					# print value
					# unique_players[value[0]] = value[1]
					unique_players.append((value[0], value[1], value[2]))
					cursor.execute('''INSERT INTO master_batting(name, team, age, woba) VALUES(?,?,?,?)''', (value[0], value[1], value[2], value[wOBA_idx]))
					# print "Player:", value[0], "inserted!"
				# else: print "Duplicate found!!", value[0], value[1]
	prospect_db.commit()
	hf.close()
	with open(actual_filestr_pitching,'r') as pf:
		for lines in pf:
			fip_idx = 0
			for line in lines.split('\r'):
				value = line.split(',')
				if value[0] == 'Name':
					for i in range(len(value)):
						if value[i] == 'FIP':
							fip_idx = i
				elif not_duplicate(value):
					# print value
					# unique_players[value[0]] = value[1]
					unique_players.append((value[0], value[1], value[2]))
					cursor.execute('''INSERT INTO master_pitching(name, team, age, fip) VALUES(?,?,?,?)''', (value[0], value[1], value[2], value[fip_idx]))
					# print "Player:", value[0], "inserted!"
				# else: print "Duplicate found!!", value[0], value[1]
	prospect_db.commit()
	pf.close()

cursor.execute('''DROP TABLE IF EXISTS top_prospects''')
cursor.execute('''
	CREATE TABLE top_prospects(name TEXT PRIMARY KEY, debut_age INTEGER, war DOUBLE, svc TEXT)
''')

teamAbbrs = ['ARI','ATL','BAL','BOS','CHA','CHN','CIN','CLE','COL','DET','HOU','KCA','LAA','LAN','MIA','MIN','NYA','NYN','OAK','PHI','SDN','SFN','SLN','TBR','TEX','TOR','WSN']
for team in teamAbbrs:
	fileStr = "data/" + team + ".csv"
	# print "TEAM:", team, "\n--------------"
	with open(fileStr,'r') as teamF:
		for lines in teamF:
			for line in lines.split('\r'):
				data = line.split(',')
				if data[0] != 'Name':
					player_name = data[0]
					debut_age = data[11]
					if debut_age != "null" and debut_age != "":
						(age, svc_time, war) = (data[9], data[12], data[13])
						# print float(war)
						# print float(svc_time)
						war = float(war)
						if player_name not in all_top_prospects:
							cursor.execute('''INSERT INTO top_prospects(name, debut_age, war, svc) VALUES(?,?,?,?)''', (player_name, debut_age, war, svc_time))
							all_top_prospects.append(player_name)
	teamF.close()
	prospect_db.commit()

inputfile_name = str(sys.argv[1])
output = []
with open(inputfile_name,'r') as inputF:
	for lines in inputF:
		for line in lines.split('\r'):
			data = line.split(',')
			player_name = data[0]
			player_pos = data[1]
			debut_age = data[8]
			# if debut_age != "null":
			# 	debut_age = int(debut_age)-1
			# 	print player_name, "doesn't fit into the data."
			# else:
			print "======="
			print data
			age = int(data[7])-1
			recent_stats = get_recent_stats(player_name, player_pos, age)
			# proper_level = len(recent_stats)-1
			# if len(recent_stats) == 1:
			if len(recent_stats) != 0:
				print player_name, "has yet to make his major league debut, but we can predict his stats!"
				# print recent_stats
				stats = (recent_stats[1], recent_stats[2], recent_stats[3])
				comparables = get_comparable_players(stats, player_pos)
				prospects_to_use = show_comparables(comparables)
				# print len(prospects_to_use), "TOP 10 PROSPECT COMPARES for", player_name
				# print "---------PLAYER VALUE-----------"
				pv = player_value_raw(prospects_to_use)
				output.append((player_name, pv))
			else:
				print "second try..."
				# print player_name, "'s data is messed up (or we don't have any data for him) >>>"
				new_recentStats = get_recent_stats(player_name, player_pos, age-1)
				if len(new_recentStats) > 0:
					stats = (new_recentStats[1], new_recentStats[2], new_recentStats[3])
					comparables = get_comparable_players(stats, player_pos)
					prospects_to_use = show_comparables(comparables)
					# print len(prospects_to_use), "TOP 10 PROSPECT COMPARES for", player_name
					# print "---------PLAYER VALUE-----------"
					pv = player_value_raw(prospects_to_use)
					output.append((player_name, pv))
					# print recent_stats
				else: print "SHIT."
inputF.close()
prospect_db.close()
outputfile_name = str(sys.argv[2])
with open(outputfile_name, 'w') as outputF:
	for line in output:
		line_str = line[0] + "," + str(line[1]) + "\n"
		outputF.write(line_str)
outputF.close()
