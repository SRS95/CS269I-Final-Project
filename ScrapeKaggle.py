from bs4 import BeautifulSoup
import requests
import json
import numpy as np
import time


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
		
		# Parse out user data from request
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



def main():
	data = np.load("kaggle_users.npy")




if __name__ == "__main__":
	main()