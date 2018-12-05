from bs4 import BeautifulSoup
import requests
import json
import numpy as np
import time
import os.path
from subprocess import call


# First pass at scraping
def naively_scrape_html():
	url = "https://www.kaggle.com/rankings"
	page = requests.get(url)
	soup = BeautifulSoup(page.content, 'html.parser')
	
	main_content_div = soup.find("div",  {"class": "site-layout__main-content"})
	main_content_script = main_content_div.findChildren('script', recursive=False)[0]

	text = main_content_script.text
	str_to_load = "["
	should_append = False

	for char_idx in range(len(text)):
		if text[char_idx: char_idx + 3] == '});': break

		if should_append: 
			str_to_load += text[char_idx]
			continue

		if text[char_idx: char_idx + 4] == '[{\"c': should_append = True

	users = json.loads(str_to_load)

	for user in users:
		print(user["displayName"])



# Note that we are only able to scrape expert, master, and grand master data
# But probably not a big deal to ignore novice and contributor data
def scrape_kaggle_user_data():
	users = []
	page_counter = 1

	# Should be able to get to page 247
	while(True):
		# Make request
		url = "https://www.kaggle.com/rankings.json?group=competitions&page=" + str(page_counter) + "&pageSize=20"
		page = requests.get(url)
		
		# Parse user data from request
		data = page.json()["list"]
		if len(data) == 0: break
		
		# Add user data to list
		users = users + data

		# Report progress
		print ("Page counter is: " + str(page_counter))
		print ("Number of users so far is: " + str(len(users)))
		
		# Increment counter
		page_counter += 1

		# Pause so as not to upset API
		time.sleep(0.1)

	np.save("kaggle_users", users)
	return kaggle_users


# Currently only used to find the LIVE competitions a user is
# participating in, so a while loop over pages is not necessary.
# However, would be necessary if finding ALL competitions a user
# has participated in since some have participated in more than 20,
# which is the page size of the API request.
def get_competitions_data(user_url):
	fail_count = 0

	# loop in case response is malformed
	while(True):
		# Make request
		url = "https://www.kaggle.com" + user_url + "/competitions.json?sortBy=grouped&group=entered&page=1&pageSize=20"
		page = requests.get(url)

		status_code = page.status_code
		print("Response status code: " + str(status_code))

		if status_code == 200: break
		elif status_code == 429: 
			fail_count += 1
			time.sleep(min(fail_count * 60, 180))

	# Pause so as not to upset API
	time.sleep(5 * np.random.rand() + 10)

	# Parse LIVE competition data from response
	# This will be in the form of a list of length k
	# Each item in the list is JSON for a given live competition
	try:
		result = page.json()["fullCompetitionGroups"][0]["competitions"]
		return result
	except:
		print("Error parsing JSON")
		return []


def get_user_id_to_competitions(user_data):
	result = {}
	num_completed = 0

	for user in user_data:
		user_url = user["userUrl"]
		competitions_data = get_competitions_data(user_url)
		result[user["userId"]] = competitions_data

		# Display progress
		num_completed += 1
		print ("Number of users completed: " + str(num_completed))

		# Save intermediate results
		if num_completed % 250 == 0: np.save("user_id_to_competitions", result)

	# Save final results
	np.save("user_id_to_competitions", result)


def main():
	# Load Kaggle user data, but only do network-bound work once
	user_data = None
	if not os.path.isfile("kaggle_users.npy"): user_data = scrape_kaggle_user_data()

	''' 
	Load user to competition dictionary; once again don't repeat network-bound work
	Not used due to API rate limit issues:

	user_id_to_competitions = None
	if not os.path.isfile("user_id_to_competitions.npy"): user_id_to_competitions = get_user_id_to_competitions(user_data)
	'''


if __name__ == "__main__":
	main()