1. Setup Directory Structure for Project
2. Setup Python Development Environment (venv, install dependencies, etc)
3. Review `avymail` Repo
   - I've checked out a repo called 'avymail' which you'll find in this directory.
   - This is a similar project. The difference being it emails individuals forecasts, where as we're generating RSS feeds.
   - This project is a useful reference for us as it demonstrates how to obtain a forecast for a zone using the avalanche.org api as well as listing avalanche centers. Somewhere in here is also how to obtain a list of zones for each center, but I'm not quite sure what code in the repo is doing that.
3. Create the avalanche center configuration yaml file
   - This is where we store an enumeration of all avalanche centers.
   - Any additional information about an avalanche center that we need to store should be here as well.
4. Write a Python function to Translate human readable zone info to avalanche.org id
   - This should accept a human readable avalance center shortcode and human readable zone short code
   - It should translate this to an id that can be used by the avalanche.org API.
4. Write a Python Function to obtain today's forecast for a specified avalanche center
   - This should accept an zone id
   - Get a copy of today's forecast (I'm assuming this will be json string).
   - Convert the json string to Python native types (dict, etc)
   - Create a dictionary which will contain date/time we initiated the request in UTC, the duration of the request (how long did the response take), and the forecast itself.
   - Return this data structure.
5. Write a python function to download forecasts for all known zones
   - This should enumerate all avalache centers and their zones
   - For each zone:
	 - Call the function to obtain a forecast this zone
	 - Create any necessary directory structure for storing that zone forecast
	 - Write the zone forecast to disk in a JSON encoding.
6. Write a python function that generates an RSS feed for a specified zone based on json files on disk
   - This function should accept a human readable short code for an avalanche center and human readable short code for the zone.
   - It should look up the 10 most recent forecasts for this zone from the forecasts we've saved to disk. Note this should not be done by enumerating all past forecasts on disk as there could be a large number of these. Instead, use the encoding of attributes in the path to the forecasts to do this more easily. If you need to change the encoding to enable this, lets discuss it. 
   - It should generate an RSS using these forecasts. The body for each entry should contain the text of the 'bottom line' section of the forecast as well as a link to the avalanche center's full forecast. We'll expand on this text contents in the future.
   - It should return the RSS feed.
7. Write a python function that generates all RSS feeds for all known zones
   - This should enumerate all avalance centers and their zones.
   - For each zone:
	 - Call the function to generate the feed.
	 - Write out the feed to our feeds directory.
8. Write a script for executing off line operations.
   - Create a command line program which will serve as an entry point for a number of processes.
   - It should let us run a "full update" which consists of, for each zone, downloading an updated forecast and generating an updated RSS feed.
   - It should let us download an updated forecast for a single zone using human readable avi center and zone names.
   - It should let us create an updated RSS feed for a single w/o downloading an updated forecast.
   - It should let us generate the html index page based on our avalanche center configuration file.
9. Create simple web app
   - It will contain a single route to start with.
   - a `/feed/{avi-center}/{zone}` route which returnes the corresponding RSS feed.
10. Create a template html file that will be used to link our RSS feeds
11. Update our offline operations script to include option to render the template to html
12. Update the web app to serve this rendered html file as the root of the app (ie - requests for '/')
13. Create a README.md suitable for desribing the project and basic information about development and other backend operations.
