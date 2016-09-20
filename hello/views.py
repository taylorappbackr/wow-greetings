from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Greeting
import json, random, requests, mixpanel, os, psycopg2, urlparse, uuid
from mixpanel import Mixpanel

urlparse.uses_netloc.append("postgres")
url = urlparse.urlparse(os.environ["DATABASE_URL"])

mixpanelToken = os.environ["MIXPANEL_TOKEN"]
mp = Mixpanel(mixpanelToken)

conn = psycopg2.connect(
	database=url.path[1:],
	user=url.username,
	password=url.password,
	host=url.hostname,
	port=url.port
)

cur = conn.cursor()

selectGreetings = """SELECT message_text
					FROM greetings
					LEFT JOIN races on races.id=races_id::integer
					WHERE races.name=%(desired_race)s
					ORDER BY RANDOM()
					LIMIT 1"""
selectFarewells = """SELECT message_text
					FROM farewells
					LEFT JOIN races on races.id=races_id::integer
					WHERE races.name=%(desired_race)s
					ORDER BY RANDOM()
					LIMIT 1"""
checkRace = "SELECT id FROM races WHERE name=%(race_name)s"
selectAllRaces = "SELECT name FROM races"
selectRandomRace = "SELECT name FROM races ORDER BY RANDOM() LIMIT 1"
insertNewUser = "INSERT INTO users (team_name, access_token, team_id, scope, webhook_url, created_at, updated_at) VALUES (%(team_name)s, %(access_token)s, %(team_id)s, %(scope)s, %(webhook_url)s, now(), now())"

# Create your views here.
@csrf_exempt
def index(request):

	## get the inputs
	if request.method == 'GET':
		print "GET order up!"
		print request.GET
		inputs = dict(request.GET)
	elif request.method == 'POST':
		print "POST order up!"
		print request.POST
		inputs = dict(request.POST)

	## process
	if 'text' in inputs and inputs['text'] != []:

		## get list of all given command words
		text = inputs['text'][0].split(" ")

		## first should be my main command
		greeting_or_farewell = text[0].lower()

		## initialize race_id for later use checking whether a specific race was requested
		race_id = None

		## second is optional, specifies race
		if len(text) > 1:
			if text[1].lower() == "night" and text[2].lower() == "elf":
				desired_race = "night elf"
			elif text[1].lower() == "blood" and text[2].lower() == "elf":
				desired_race = "blood elf"
			else:
				desired_race = text[1].lower()
				cur.execute(checkRace, {'race_name':desired_race})
				race_id = cur.fetchone()
				if race_id is None:
					## return an unknown race error
					cur.execute(selectAllRaces,)
					races = cur.fetchall()
					races_list = [str(race[0])for race in races]

					## track Mixpanel
					mp.track(inputs['team_id'][0]+"_"+inputs['user_id'][0], "Unknown Race", {'desired_race':desired_race, 'specific_race_requested':True, 'slack_user_name':inputs['user_name'][0], 'channel_name':inputs['channel_name'][0], 'slack_team_name':inputs['team_domain'][0], 'given_text':inputs['text'][0]})

					## create/update Mixpanel User
					mp.people_set(inputs['team_id'][0]+"_"+inputs['user_id'][0], {'$name':inputs['user_name'][0], '$distinct_id':inputs['team_id'][0]+"_"+inputs['user_id'][0], 'slack_user_name':inputs['user_name'][0], 'slack_team_name':inputs['team_domain'][0]})

					return JsonResponse({"text":"Sorry friend, afraid I've never seen specimen of the %(desired_race)s species round these parts.\nWorld of Warcraft races available for you to choose from are: %(races)s"%{"desired_race":desired_race, "races":races_list}})
				else:
					race_id = race_id[0]
		else:
			cur.execute(selectRandomRace,)
			desired_race = cur.fetchone()[0]


		## check first greeting or farewell or unknown
		if greeting_or_farewell == "greeting" or greeting_or_farewell == "greetings":
			cur.execute(selectGreetings, {'desired_race':desired_race})
			wow_message = cur.fetchone()
			if wow_message is not None:
				wow_message = wow_message[0]

				## send event to Mixpanel
				if race_id is None:
					requested_race = False
				else:
					requested_race = True
				mp.track(inputs['team_id'][0]+"_"+inputs['user_id'][0], "Greeting", {'desired_race':desired_race, 'specific_race_requested':requested_race, "message_text":wow_message, 'slack_user_name':inputs['user_name'][0], 'channel_name':inputs['channel_name'][0], 'slack_team_name':inputs['team_domain'][0], 'given_text':inputs['text'][0]})

				## create/update Mixpanel User
				mp.people_set(inputs['team_id'][0]+"_"+inputs['user_id'][0], {'$name':inputs['user_name'][0], '$distinct_id':inputs['team_id'][0]+"_"+inputs['user_id'][0], 'slack_user_name':inputs['user_name'][0], 'slack_team_name':inputs['team_domain'][0]})

				requests.post(inputs['response_url'][0], data=json.dumps({"text":"Master @%(username)s says: %(wow_message)s"%{'username':inputs['user_name'][0], 'wow_message':wow_message}, "response_type":"in_channel"}))
				return HttpResponse(status=201)
			else:
				return JsonResponse({"text":"I'm ever so sorry Master @%(username)s.  It appears my tomes have gotten mixed up.  Please query my wisdom later. :crystal_ball:"%{'username':inputs['user_name'][0]}})

		elif greeting_or_farewell == "farewell" or greeting_or_farewell == "farewells":
			cur.execute(selectFarewells, {'desired_race':desired_race})
			wow_message = cur.fetchone()
			if wow_message is not None:
				wow_message = wow_message[0]

				## send event to Mixpanel
				if race_id is None:
					requested_race = False
				else:
					requested_race = True
				mp.track(inputs['team_id'][0]+"_"+inputs['user_id'][0], "Farewell", {'desired_race':desired_race, 'specific_race_requested':requested_race, "message_text":wow_message, 'slack_user_name':inputs['user_name'][0], 'channel_name':inputs['channel_name'][0], 'slack_team_name':inputs['team_domain'][0], 'given_text':inputs['text'][0]})

				## create/update Mixpanel User
				mp.people_set(inputs['team_id'][0]+"_"+inputs['user_id'][0], {'$name':inputs['user_name'][0], '$distinct_id':inputs['team_id'][0]+"_"+inputs['user_id'][0], 'slack_user_name':inputs['user_name'][0], 'slack_team_name':inputs['team_domain'][0]})

				requests.post(inputs['response_url'][0], data=json.dumps({"text":"Master @%(username)s says: %(wow_message)s"%{'username':inputs['user_name'][0], 'wow_message':wow_message}, "response_type":"in_channel"}))
				return HttpResponse(status=201)
			else:
				return JsonResponse({"text":"I'm ever so sorry Master @%(username)s.  It appears my tomes have gotten mixed up.  Please query my wisdom later. :crystal_ball:"%{'username':inputs['user_name'][0]}})

		elif greeting_or_farewell == "":

			## track Mixpanel
			mp.track(inputs['team_id'][0]+"_"+inputs['user_id'][0], "Blank Request", {'slack_user_name':inputs['user_name'][0], 'channel_name':inputs['channel_name'][0], 'slack_team_name':inputs['team_domain'][0], 'given_text':inputs['text'][0]})

			## create/update Mixpanel User
			mp.people_set(inputs['team_id'][0]+"_"+inputs['user_id'][0], {'$name':inputs['user_name'][0], '$distinct_id':inputs['team_id'][0]+"_"+inputs['user_id'][0], 'slack_user_name':inputs['user_name'][0], 'slack_team_name':inputs['team_domain'][0]})

			return JsonResponse({"text":"Try either 'greeting' or 'farewell' and I'll return a random World of Warcraft quote of that type. :crossed_swords:"})

		elif greeting_or_farewell == "help":

			## track Mixpanel
			mp.track(inputs['team_id'][0]+"_"+inputs['user_id'][0], "Help", {'slack_user_name':inputs['user_name'][0], 'channel_name':inputs['channel_name'][0], 'slack_team_name':inputs['team_domain'][0], 'given_text':inputs['text'][0]})

			## create/update Mixpanel User
			mp.people_set(inputs['team_id'][0]+"_"+inputs['user_id'][0], {'$name':inputs['user_name'][0], '$distinct_id':inputs['team_id'][0]+"_"+inputs['user_id'][0], 'slack_user_name':inputs['user_name'][0], 'slack_team_name':inputs['team_domain'][0]})

			return JsonResponse({"text":"Try either 'greeting' or 'farewell' and I'll return a random World of Warcraft quote of that type. :crossed_swords:\nYou can also try 'races' for a list of all the World of Warcraft races you can choose a greeting from."})

		elif greeting_or_farewell == "races":
			cur.execute(selectAllRaces,)
			races = cur.fetchall()
			if races == []:
				return JsonResponse({"text":"I'm ever so sorry Master @%(username)s.  It appears my tomes have gotten mixed up.  Please query my wisdom later. :crystal_ball:"%{'username':inputs['user_name'][0]}})
			else:
				races_list = [str(race[0]) for race in races]

				## track Mixpanel
				mp.track(inputs['team_id'][0]+"_"+inputs['user_id'][0], "List Races", {'slack_user_name':inputs['user_name'][0], 'channel_name':inputs['channel_name'][0], 'slack_team_name':inputs['team_domain'][0], 'given_text':inputs['text'][0]})

				## create/update Mixpanel User
				mp.people_set(inputs['team_id'][0]+"_"+inputs['user_id'][0], {'$name':inputs['user_name'][0], '$distinct_id':inputs['team_id'][0]+"_"+inputs['user_id'][0], 'slack_user_name':inputs['user_name'][0], 'slack_team_name':inputs['team_domain'][0]})

				return JsonResponse({"text":"World of Warcraft races available for you to choose from are: %(races)s  (Make your selection after 'greeting' or 'farewell')"%{"races":races_list}})

		else:
			return JsonResponse({"text":"Sorry friend, afraid I'm not attuned to \"%(input_text)s\" in these parts.  You'll have better luck with either 'greeting' or 'farewell'. :crossed_swords:."%{'input_text': text[0]}})

## Display homepage for people to learn and signup
def home(request):

	print "Loading homepage from Auth view."

	## track Mixpanel
	mp.track(str(uuid.uuid4()), "Load Homepage")

	return render(request, 'base.html')


## Not needed (from original setup code), but crashes the setup files somewhere...
def db(request):

	greeting = Greeting()
	greeting.save()

	greetings = Greeting.objects.all()

	return render(request, 'db.html', {'greetings': greetings})



## displays a page with the Slack Button to authorize me to enter their team
def auth(request):

	print "Loading Auth page."

	## track Mixpanel
	mp.track(str(uuid.uuid4()), "Load Auth Page")

	return render(request, 'base.html')

	print "Auth page loaded with no problems."



## Slack Button authorization success calls this method to exchange a temporary code for a permanent access token, which I'll save (but don't know why I need since I always get a reponse_url from the /command)
def auth_success(request):

	print "User has given me permission to join their Guild!"

	if request.method == 'GET':

		print request.GET
		inputs = dict(request.GET)

		tempCode = inputs['code'][0]
		print "tempCode:", tempCode

		print "Calling the Slack server to exchange tempCode for an access_token...."
		slackExchangeCodeForAccessTokenUrl = "https://slack.com/api/oauth.access"
		response = requests.get(slackExchangeCodeForAccessTokenUrl, params={'code':tempCode, 'client_id':os.environ["WOW_SLACK_CLIENT_ID"], 'client_secret':os.environ["WOW_SLACK_CLIENT_SECRET"]})
		print "have now called the Slack server with a status code of: %s"%response.status_code

		dataReceived = response.json()

		print "response:", dataReceived

		try:
			access_token = dataReceived['access_token']
			print "access_token:", access_token
		except:
			print "Error retreiving access_token from response. Logging as None"
			access_token = None
		try:
			team_name = dataReceived['team_name']
			print "team_name:", team_name
		except:
			print "Error retreiving team_name from response. Logging as None"
			team_name = None
		try:
			team_id = dataReceived['team_id']
			print "team_id", team_id
		except:
			print "Error retreiving team_id from response. Logging as None"
			team_id = None
		try:
			scope = dataReceived['scope']
			print "scope", scope
		except:
			print "Error retreiving scope from response. Logging as None"
			scope = None
		try:
			user_id = dataReceived['user_id']
			print "user_id", user_id
		except:
			print "Error retreiving user_id from response. Logging as None"
			user_id = None
		try:
			webhook_url = dataReceived['incoming_webhook']['url']
			print "webhook_url", webhook_url
		except:
			print "Error retreiving webhook_url from response. Logging as None"
			webhook_url = None


		##### still need to log this in my database, might need it later #####
		cur.execute(insertNewUser, {'team_name':team_name, 'access_token':access_token, 'team_id':team_id, 'scope':scope, 'webhook_url':webhook_url})
		conn.commit()

		print "Success! I should now have an access_token for the new user's team, and they should now be able to use my service!"

		## ping team using webhook_url and introduce myself
		print "Introducing myself to "+str(team_name)
		if webhook_url is not None:
			response = requests.post(webhook_url, data=json.dumps({'text':'Lo!\nThanks for the Guild invite, %(team_name)s.  Here to make daily introductions a little more friendly.\nGive it a whirl with:\n>`/wow greetings`\nAnd if you ever find yourself stuck LFM, `/wow help` or `/wow races` are your friends.\nWatch yer back! :crossed_swords:'%{'team_name':team_name}, 'username':'Warcraft Greetings', 'icon_url':'https://s3-us-west-2.amazonaws.com/slack-files2/avatars/2016-08-11/68703636325_479501fda3b50e7281a8_512.png'}))
			if response.status_code != 200:
				print response
				print "Introduction response META:", response.META
				print "Introduction response data:", response.json()
		else:
			print "webhook_url was None, so I am unable to introduce myself to "+str(team_name)

		## track Mixpanel
		mp.track(str(team_id)+"_"+str(user_id), "Signup", {'scope':scope, 'team_id':team_id, 'team_name':team_name, 'user_id':user_id})

		## create/update Mixpanel User
		mp.people_set(str(team_id)+"_"+str(user_id), {'$distinct_id':str(team_id)+"_"+str(user_id), 'slack_team_name':team_name})

		## ping myself in Slack
		MY_SLACK_WEBHOOK_URL = os.environ['SLACK_WEBHOOK_URL']
		response = requests.post(MY_SLACK_WEBHOOK_URL, data=json.dumps({'text':'A new User has signed up for Warcraft Greetings!  Huzzah! :crossed_swords:\nMeet the %(team_name)s Team.'%{'team_name':team_name}, 'channel':'@taylor', 'username':'Warcraft Greetings', 'icon_url':'https://s3-us-west-2.amazonaws.com/slack-files2/avatars/2016-08-11/68703636325_479501fda3b50e7281a8_512.png'}))
		if response.status_code != 200:
			print response
			print "Slack response META:", response.META
			print "Slack response data:", response.json()

		return render(request, 'auth_success.html')
