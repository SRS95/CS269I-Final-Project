'''
This script simulates Version 1 of our proposed changes
to Kaggle's model. Specifically, we propose having one
"gold" competition at any given time in which only a fixed
number of users can participate, forcing users who likely
would have otherwise chosen to compete in the highest paying
competition to compete in other "normal" competitions.

Author: Sam Schwager
Last Edited: 12/4/2018
'''

import json
import numpy as np
import pandas as pd
import os
import operator
import copy
from matplotlib import pyplot as plt
from matplotlib import rc
import argparse
import zipfile

# Number of users kept in the gold competition
num_retained = 25

# Mapping from competition name to payout
competitions_to_payouts =\
{"two-sigma-financial-news":100000., "ga-customer-revenue-prediction":45000.,\
"humpback-whale-identification":25000., "airbus-ship-detection":60000.,\
"human-protein-atlas-image-classification":37000., "quora-insincere-questions-classification":25000.,\
"NFL-Punt-Analytics-Competition":80000., "inclusive-images-challenge":25000.,\
"elo-merchant-category-recommendation":50000., "quickdraw-doodle-recognition":25000.,\
"traveling-santa-2018-prime-paths": 25000., "PLAsTiCC-2018":25000.}


# Unzip files and create new directory
def form_leaderboards_dir():
	for fname in os.listdir("Leaderboards_zip"):
		if (fname == ".DS_Store"): continue
		f_title = fname.split('.')[0] + ".csv"
		with zipfile.ZipFile("Leaderboards_zip/" + fname, 'r') as zip_ref:
			zip_ref.extractall("Leaderboards")


# Returns a sorted list over all competitors in the competition that are experts, masters, and grandmasters
# NOTE: the list is sorted by tier and by points with in each tier
def get_competitors(competition, user_info):
	usernames = set(user_info.keys())
	competitors = set(pd.read_csv("./Leaderboards/" + competition + "-publicleaderboard.csv").values[:,1])
	overlap_users = competitors.intersection(usernames)

	result_grandmasters = {}
	result_masters = {}
	result_experts = {}

	for user in overlap_users:
		curr_user_info = user_info[user]
		if curr_user_info[0] == "grandmaster": result_grandmasters[user] = curr_user_info
		elif curr_user_info[0] == "master": result_masters[user] = curr_user_info
		elif curr_user_info[0] == "expert": result_experts[user] = curr_user_info

	result_grandmasters = sorted(result_grandmasters.items(), key=lambda x: x[1][1], reverse=True)
	result_masters = sorted(result_masters.items(), key=lambda x: x[1][1], reverse=True)
	result_experts = sorted(result_experts.items(), key=lambda x: x[1][1], reverse=True)

	result = result_grandmasters + result_masters + result_experts
	return result


# Returs a mapping from all experts, masters, and grandmasters
# to a tuple (tier, points)
def get_user_info(user_data):
	result = {}
	for user in user_data: result[user["displayName"]] = (user["tier"], user["points"])
	return result


# Allocate those eliminated from gold to new competitions
def allocate_eliminated(user_info, normal_competition_names, probabilities, normal_competitors):
	# Assign all users to new competitions
	choices = np.arange(0, len(normal_competition_names))
	for user in user_info:
		assignment = normal_competition_names[np.random.choice(a=choices, p=probabilities)]
		normal_competitors[assignment].append(user)
	return normal_competitors


def compute_score(competitors, user_info):
	 total = 0.0

	 for competitor in competitors:
	 	competitor_name = competitor[0]
	 	total += user_info[competitor_name][1]

	 return total

# Compute the reallocation gains
def compute_gains(before, after, user_info):
	result = {}

	for competition in before.keys():
		before_score = compute_score(before[competition], user_info)
		after_score = compute_score(after[competition], user_info)
		result[competition] = after_score - before_score

	return result

# Makes a competition name readable for plotting purposes
def make_readable(name):
	words = name.split('-')

	result = ""

	for idx, word in enumerate(words):
		word = word[0].upper() + word[1:]
		if idx < len(words) - 1: result += word + " "

	return result



def make_category_histogram(frequencies, competition_name):
	categories = ('Grandmasters', 'Masters', 'Experts')
	y_pos = np.arange(len(categories))
	plt.bar(y_pos, frequencies, align='center', alpha=0.5)
	plt.xticks(y_pos, categories)
	plt.ylabel('Number of competitors')
	plt.xlabel('Competitor category')
	plt.title('Number of competitors by category for ' + competition_name)
	plt.show()


def get_frequencies(competitor_info):
	frequencies = [0, 0, 0]

	for competitor in competitor_info:
		if competitor[1][0] == "grandmaster": frequencies[0] += 1
		elif competitor[1][0] == "master": frequencies[1] += 1
		elif competitor[1][0] == "expert": frequencies[2] += 1

	return frequencies


def plot_competitor_info(normal_competitors_info, gold_competitors_info=None):
	global num_retained

	if gold_competitors_info is not None: 
		make_category_histogram(get_frequencies(gold_competitors_info), make_readable("two-sigma-financial-news"))

	for key in normal_competitors_info:
		make_category_histogram(get_frequencies(normal_competitors_info[key]), make_readable(key))


'''
Plots best fit lines for number of players
in a given category vs. payout competition.

This should allow us to get a sense of how
the number of players of a given category
changes as the payout is changed.

Author: John Solitario
Last Edited: 12/6/2018
'''
def plot_payout_category_best_fits(gold_competitors_info, normal_competitors_info, after_comp):
	# Mapping from competition name to payout
	global competitions_to_payouts

# input:
#	gold_competitors_info -- sorted list over all competitors in the gold competition:
#	(sorting done by tier and by points with in each tier from grandmaster to expert
#	and within each category from most to least points)
#
#	normal_competitors_info -- dict mapping from competition name to sorted list over
#	all competitors in the gold competition (sorted done as in gold_competitors_info)

	# Index 0 -> gramndmaster, Index 2 -> master, Index 3 -> expert


	frequencies = {}
	for comp in normal_competitors_info:
		if comp == "NFL-Punt-Analytics-Competition": continue
		frequencies[comp] = get_frequencies(normal_competitors_info[comp])
	frequencies["two-sigma-financial-news"] = get_frequencies(gold_competitors_info)

	bar1, bar2, bar3, bar4 = [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0] # bucket1 0 - 25,000, bucket2 25,001 to 50,000, etc.
	bucket1_count, bucket2_count, bucket3_count, bucket4_count = 0, 0, 0, 0

	for comp in frequencies:
		if competitions_to_payouts[comp] <= 25000:
			bucket1_count +=1
			frequency = frequencies[comp]
			for index in range(len(bar1)): bar1[index] += frequency[index]
		elif competitions_to_payouts[comp] > 25000 and competitions_to_payouts[comp] <= 50000: 
			bucket2_count +=1
			frequency = frequencies[comp]
			for index in range(len(bar2)): bar2[index] += frequency[index]
		elif competitions_to_payouts[comp] > 50000 and competitions_to_payouts[comp] <= 75000: 
			bucket3_count +=1
			frequency = frequencies[comp]
			for index in range(len(bar3)): bar3[index] += frequency[index]
		else: 
			bucket4_count +=1
			frequency = frequencies[comp]
			for index in range(len(bar4)): bar4[index] += frequency[index]

	for index in range(3):
		bar1[index] = float(bar1[index]) / bucket1_count
		bar2[index] = float(bar2[index]) / bucket2_count
		bar3[index] = float(bar3[index]) / bucket3_count
		bar4[index] = float(bar4[index]) / bucket4_count

		grandmasters = [bar1[0], bar2[0], bar3[0], bar4[0]]
		masters = [bar1[1], bar2[1], bar3[1], bar4[1]]
		experts = [bar1[2], bar2[2], bar3[2], bar4[2]]
		ind = np.arange(4)
		bars = [bar1[1] + bar1[2], bar2[1] + bar2[2], bar3[1] + bar3[2], bar4[1] + bar4[2]]


		p1 = plt.bar(ind, experts) 
		p2 = plt.bar(ind, masters, bottom = experts) 
		p3 = plt.bar(ind, grandmasters, bottom = bars)

		plt.ylabel('Average Number of Particpators')
		if after_comp: plt.title('After Reallocation: Partipation Compared to Competition Payout')
		else: plt.title('Before Reallocation: Partipation Compared to Competition Payout')

		plt.xticks(ind, ('0 to 25K', '25K to 50K', '50K to 75K', '75K to 100K'))
		plt.xlabel('Total Competition Payout ($)')
		plt.legend((p1[0], p2[0], p3[0]), ('Experts', 'Masters', 'Grandmasters'))
		plt.show()

'''
Plots point gain for each competition (outside of the gold competition)
Using a stacked bar chart

Author: Sam Sklar
Last Edited 12/6/2018
'''
def plot_point_gains(average_gains, user_info):
    bars1 = []
    bars2 = []
    r = []
    shortened_names = ["Revenue", "Quora", "Airbus", "Protein Atlas", "Santa",\
    					"Whales", "Merchants", "Images", "PlastiCC", "Doodles"]
    count = 0
    
    for key in average_gains.keys(): 
        # Don't plot the NFL competition since we don't
        # have enough data about it
        if key == "NFL-Punt-Analytics-Competition": continue
        competitors = get_competitors(key, user_info)
        original_score = compute_score(competitors, user_info)
        bars1.append(original_score)
        point_gain = average_gains[key]
        new_score = point_gain
        bars2.append(new_score)
        r.append(count)
        count += 1
                
    # Names of group and bar width
    barWidth = 1
     
    # Create brown bars
    plt.bar(r, bars1, edgecolor='white', width=barWidth)
    # Create green bars (middle), on top of the firs ones
    plt.bar(r, bars2, bottom=bars1, edgecolor='white', width=barWidth)
     
    # Custom X axis
    plt.xticks(r, shortened_names, fontweight='bold')
    plt.xlabel("Competition")
    
    #Custom Y axis
    plt.ylabel("Points (Before:Blue and After:Orange)")
     
    # Show graphic
    plt.show()


# Perform the simulation
def perform_simulation(user_data, gold_competition, normal_competition_names, make_plots):
	global num_retained

	# mapping from expert, master, and grandmaster usernames to (tier, points)
	user_info = get_user_info(user_data)

	gold_competitors_info = get_competitors(gold_competition, user_info)
	
	# Mapping from competition name to numpy array of competitor names
	normal_competitors_info = {}
	for name in normal_competition_names: normal_competitors_info[name] = get_competitors(name, user_info)

	# Only keep the top "num_retained" in the gold competition
	gold_competitors_retained_info = gold_competitors_info[:num_retained]
	gold_competitors_eliminated_info = gold_competitors_info[num_retained:]

	if make_plots: plot_competitor_info(normal_competitors_info, gold_competitors_info)

	# Find the assignment probabilities for the remaining 11 competitions
	normal_payouts = [45000., 25000., 60000., 37000., 25000., 80000., 25000., 50000., 25000., 25000., 25000.]
	norm_const = sum(normal_payouts)
	probabilities = [x / norm_const for x in normal_payouts]

	# Plot payout by category best fit lines BEFORE reallocation
	if make_plots: plot_payout_category_best_fits(gold_competitors_info, normal_competitors_info, False)

	# Average across 100 allocations
	average_gains = {}
	for name in normal_competition_names: average_gains[name] = 0.0
	num_iterations = 100

	normal_competitors_info_updated = None
	for simulation_index in range(num_iterations):
		# Allocate eliminated competitors to other competitions
		normal_competitors_info_updated = allocate_eliminated(gold_competitors_eliminated_info, normal_competition_names, probabilities, copy.deepcopy(normal_competitors_info))

		# Compute gains from reallocation 
		gains = compute_gains(normal_competitors_info, normal_competitors_info_updated, user_info)
		for name in normal_competition_names: average_gains[name] = average_gains[name] + gains[name]
	
	for key in average_gains.keys(): 
		average_gains[key] /= num_iterations
		print ("Competition " + key + " gained " + str(average_gains[key]) + " points.")

	# Plot payout by category best fit lines, competitor info and marginal gains AFTER reallocation
	if make_plots: 
		plot_payout_category_best_fits(gold_competitors_info, normal_competitors_info_updated, False)
		plot_competitor_info(normal_competitors_info_updated)
		plot_point_gains(average_gains, user_info)



def main():
	# Make life easier for the user
	if not os.path.isdir("Leaderboards"): form_leaderboards_dir()

	# Load user data (experts, masters, and grandmasters)
	user_data = np.load("kaggle_users.npy")

	# Get a list of competition names
	competition_names = ["-".join(name.split('.')[0].split('-')[:-1]) for name in os.listdir("Leaderboards") if name != ".DS_Store"]

	# Just one "gold" competition in version 1
	gold_competition = "two-sigma-financial-news"

	# The rest are normal competitions
	normal_competition_names = [name for name in competition_names if name != gold_competition]


	# Simulate the reassignment
	# If make_plots is true then we generate plots throughout
	parser = argparse.ArgumentParser()
	parser.add_argument("-p", "--plot", help="run simulation with plotting", action="store_true")
	args = parser.parse_args()
	perform_simulation(user_data, gold_competition, normal_competition_names, make_plots=args.plot)
	

if __name__ == "__main__":
	main()