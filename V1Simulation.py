import json
import numpy as np
import pandas as pd
import os
import operator
import copy

# Number of users kept in the gold competition
num_retained = 25


# Returns a sorted list over all competitors in the competition that are experts, masters, and grandmasters
# NOTE: the list is sorted by tier and by points with in each tier
def get_competitors(competition, user_info):
	usernames = set(user_info.keys())
	competitors = set(pd.read_csv("./Leaderboards/" + competition + "/" + competition + "-publicleaderboard.csv").values[:,1])
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


# Perform the simulation
def perform_simulation(user_data, gold_competition, normal_competition_names):
	global num_retained

	# mapping from expert, master, and grandmaster usernames to (tier, points)
	user_info = get_user_info(user_data)

	gold_competitors_info = get_competitors(gold_competition, user_info)
	
	# Mapping from competition name to numpy array of competitor names
	normal_competitors_info = {}
	for name in normal_competition_names: normal_competitors_info[name] = get_competitors(name, user_info)

	# Only keep the top 25 in the gold competition
	gold_competitors_retained_info = gold_competitors_info[:25]
	gold_competitors_eliminated_info = gold_competitors_info[25:]

	# Find the assignment probabilities for the remaining 11 competitions
	payouts = [45000., 25000., 60000., 37000., 25000., 80000., 25000., 50000., 25000., 25000., 25000.]
	norm_const = sum(payouts)
	probabilities = [x / norm_const for x in payouts]

	# Allocate eliminated competitors to other competitions
	normal_competitors_info_updated = allocate_eliminated(gold_competitors_eliminated_info, normal_competition_names, probabilities, copy.deepcopy(normal_competitors_info))

	# Compute and print gains from reallocation
	gains = compute_gains(normal_competitors_info, normal_competitors_info_updated, user_info)
	for key in gains.keys(): print ("Competition " + key + " gained " + str(gains[key]) + " points.")


def main():
	# Load user data (experts, masters, and grandmasters)
	user_data = np.load("kaggle_users.npy")

	# Get a list of competition names
	competition_names = [name for name in os.listdir('./Leaderboards') if name != ".DS_Store"]

	# Just one "gold" competition in version 1
	gold_competition = "two-sigma-financial-news"

	# The rest are normal competitions
	normal_competition_names = [name for name in competition_names if name != gold_competition]

	# Simulate the reassignment
	perform_simulation(user_data, gold_competition, normal_competition_names)
	

if __name__ == "__main__":
	main()