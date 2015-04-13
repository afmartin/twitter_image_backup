# Twitter Image Backup

## Purpose

This script allows a user to download images from their tweets.  While it is limited by what the Twitter API can provide, it can retrieve up to 3200 of the most recent tweets.

## Setup

Python 2 is required.

Use:

	$ pip install requests
	$ git clone https://github.com/afmartin/twitter-image-backup.git

## Configuration

All configuration can be be found in "config".  You are required to have a Twitter application setup and have a consumer key and consumer secret.

Important: do not share your consumer key/secret.

## Use

Simply run:

	$ ./twitter_image_backup.py USERNAME

## Limits

Twitter's API only allows retrieving up to 3200 of the most recent tweets.

Twitter's API has time constraints on the amount of requests, if a request is hit and a 15 minute period must pass.

Also this script does not retrieve the source image if it was embedded, it downloads whatever Twitter has so resolutions may be downscaled. 

## License

This project is licensed under the MIT License.  A LICENSE file is included.
