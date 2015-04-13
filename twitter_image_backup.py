#!/usr/bin/python
#########################
# TWITTER IMAGE BACKUP  #
#                       #
# Alexander Martin      #
#########################

from __future__ import print_function
import ConfigParser
import requests
import sys
import urllib
import base64
import time
import datetime
import os

#########################
# Constants
#########################
MAX_TWEET_COUNT = 3200
MAX_COUNT = 200

#########################
# Config Variables
#########################
consumer_key = ""
consumer_secret = ""
save_directory = ""

#########################
# Global Variables
#########################
tweet_count = 1
count = None

def wait_time_till_reset(response):
	"""
	wait_time_till_reset

	Waits a time until API call limit resets.

	Time API gives in epoch seconds.
	"""
	reset_time = response.headers["X-Rate-Limit-Reset"]
	time = time.gmtime()

	# Plus 3 probably has no bearings on program
	# but I just want to give it an extra second or two
	# for Twitter to reset.
	wait = reset_time - time + 3;

	print("NOTICE: Program must wait till API calls limit resets in " + str(datetime.timedelta(seconds = time)), file=sys.stderr)
	time.sleep(time)
	return

def run_request(request, token = None):
	"""
	run_request

	Param: request of ADT Request

	Runs a customized request until proper data is
	given.
	"""
	if token:
		request.headers["Authorization"] = "Bearer " + token

	while True:
		prepared = request.prepare()
		session = requests.Session()
		response = session.send(prepared)

		try:
			json = response.json()
		except:
			print(sys.argv[0] + " ERROR: Did not receive JSON from request.", file=sys.stderr)
			sys.exit(1)

		if "errors" not in json:
			return json
		else:
			for error in json["errors"]:
				# Error 88 is wait error
				if error["code"] == 88:
					wait_till_time_token(response)
					continue
			# Has an error but not limit error.
			print(sys.argv[0] + " WARNING: Request returned an error.  Will try to keep running normally.", file=sys.stderr)
			return json

def authenticate():
	"""
	authenticate

	Twitter API requires to authenticate to use
	the queries needed.  We will be doing an application
	authentication.  We are not going through users.

	Doc: https://dev.twitter.com/oauth/application-only
	"""
	# URL encode key & secret.
	encoded_key = urllib.quote_plus(consumer_key)
	encoded_secret = urllib.quote_plus(consumer_secret)

	# Concatenate (key:secret)
	concat = encoded_key + ":" + encoded_secret

	# Base64 encode
	bearer = base64.b64encode(concat)

	# Send request for token.
	headers = {
			'Authorization': "Basic " + bearer,
			'Content-Type':  'application/x-www-form-urlencoded;charset=UTF-8'
			}

	data = "grant_type=client_credentials"
	url = "https://api.twitter.com/oauth2/token"
	request = requests.Request('POST',
			url,
			data = data,
			headers = headers)

	json = run_request(request)

	if "token_type" in json and json["token_type"] == "bearer":
		return json["access_token"]
	else:
		print(sys.argv[0] + " ERROR: Did not receive bearer token from authorization request.", file=sys.stderr)
		sys.exit(1)

def config():
	"""
	config

	Read the configuration and make sure it is actually changed.
	"""
	global consumer_key, consumer_secret, save_directory
	parser = ConfigParser.SafeConfigParser()

	try:
		parser.read("config")
		consumer_key = parser.get('app', 'key')
		consumer_secret = parser.get('app', 'secret')
		save_directory = parser.get('app', 'save_directory')
	except:
		# Config File is Corrupted :(
		print(sys.argv[0] + " ERROR: Configuration file is corrupted.  Please make or update 'config' file to be like:", file=sys.stderr)
		print("[app]\nkey = YOUR_KEY_HERE\nsecret = YOUR_SECRET_HERE\nsave_directory = DESTINATION_DIRECTORY_HERE", file=sys.stderr)
		sys.exit(1)

	if consumer_key == "default" or consumer_secret == "default":
		print(sys.argv[0] + " ERROR: Please add application secret and key in config", file=sys.stderr)
		sys.exit(1)

def get_amount_of_tweets(token, user):
	"""
	get_amount_of_tweets

	Token => Authentication Token
	User => Username of Twitter User

	Get amount of tweets a user has up to the API limit.
	"""
	params = { 'screen_name' : user }
	url = "https://api.twitter.com/1.1/users/show.json?"
	url += urllib.urlencode(params)
	request = requests.Request('GET', url)
	json = run_request(request, token)

	try:
		count = json["statuses_count"]
	except KeyError:
		print(sys.argv[0] + " ERROR: Could not retrieve user tweet count.  Usually invalid username provided", file=sys.stderr)
		sys.exit(1)

	if count > MAX_TWEET_COUNT:
		return MAX_TWEET_COUNT
	else:
		return count

def query_for_tweets(token, user, last_id = None):
	"""
	Query for Tweets

	Returns JSON for a tweet
	"""
	params = {
			'screen_name' : user,
			'count' : MAX_COUNT
			}

	if (last_id):
		params["max_id"] = last_id - 1

	url = "https://api.twitter.com/1.1/statuses/user_timeline.json?"
	url += urllib.urlencode(params)
	request = requests.Request('GET', url)
	json = run_request(request, token)

	return json

def retrieve_images_from_tweets(user, json):
	"""
	Retrieve Images from Tweets

	Pass it a list of tweets and it will search for image urls
	and download them.
	"""
	global tweet_count
	for tweet in json:
		if "media" in tweet["entities"]:
			media = tweet["entities"]["media"]
			media_url = None

			# I have no idea why entities/media returns a list of dictionaries
			for dictionary in media:
				if "media_url" in dictionary:
					media_url = dictionary["media_url"]

			print(sys.argv[0] + " (" + str(int(100 * ( float(tweet_count) / float(count)))) + "% Done) Retrieving Image: " + media_url, file=sys.stdout)

			if media_url:
				filename = save_directory + user + "/" + str(tweet["id"]) + media_url[-4:]
				try:
					image = urllib.urlopen(media_url).read()
				except:
					print(sys.argv[0] + " ERROR: Could not retrieve image", file=sys.stderr)
					print(sys.argv[0] + " Will try to continue running...", file=sys.stderr)

				try:
					f = open(filename, 'wb')
					try:
						f.write(image)
					finally:
						f.close()
				except IOError as error:
					print(sys.argv[0] + " ERROR: Could not open file", file=sys.stderr)
					print(sys.argv[0] + " ERROR: IOError: [" + error.errno + "] " + error.filename + " - " + error.strerror, file=sys.stderr)
					sys.exit(1)
		tweet_count += 1


def main():
	global count, save_directory
	try:
		user = sys.argv[1]
	except IndexError:
		print(sys.argv[0] + " ERROR: Please include a username (ex " + sys.argv[0] + " username)", file=sys.stderr)
		sys.exit(1)

	config()
	token = authenticate()
	count = get_amount_of_tweets(token, user)
	if count == MAX_TWEET_COUNT:
		print("WARNING:  Currently Twitter API limits retrieving " + str(MAX_TWEET_COUNT) + " tweets.", file=sys.stderr)
	print("Amount of tweets to search: " + str(count), file=sys.stdout)


	if save_directory[-1] != "/":
		save_directory += "/"

	# Let's make sure folders exist, if not create them.
	if not os.path.exists(save_directory + user):
		try:
			os.makedirs(save_directory + user)
		except OSError as error:
			print(sys.argv[0] + " ERROR: Could not make folder " + save_directory + user, file=sys.stderr)
			print(sys.argv[0] + " ERROR: OSError: [" + error.errno + "] " + error.filename + " - " + error.strerror, file=sys.stderr)
			sys.exit(1)

	max_id = None
	while True:
		tweets = query_for_tweets(token, user, max_id)
		if tweets:
			retrieve_images_from_tweets(user, tweets)
			max_id = tweets[-1]["id"]
			continue
		break

if __name__ == "__main__":
	main()
