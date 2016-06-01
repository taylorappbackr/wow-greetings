from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
import json, random, requests

from .models import Greeting

BASE_URL = "https://slack.com/api"
API_TOKEN = os.environ.get("SLACK_API_TOKEN")
WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL").strip()
SLASH_COMMAND_TOKEN = os.environ.get("SLACK_SLASH_COMMAND_TOKEN")

greeting_dict = {
					"dwarf": {
						"greetings": ["Hey there!", "Ya got my attention.", "How are ya?", "Talk to me.", "'Lo!", "Well met.", "What's on your mind?", "Great tae meet ya.", "What can I do fer ya?", "Aye?", "Interest ya'n a pint?", "Welcome.", "Hello."],
						"farewells": ["Off with ye.", "Safe travels.", "Keep your feet on the ground.", "See ya soon.", "Watch yer back!", "Be good!"]
					},
					"night elf": {
						"greetings": ["Elune be with you.", "Ishnu-alah.", "Elune light your path.", "I am listening.", "I am honored.", "Till next we meet.", "What brings you here?", "I am listening.", "Greetings.", "Peace be with you."],
						"farewells": ["Be careful.", "Elune guide your path.", "Goddess watch over you.", "Till the next we meet.", "May the stars guide you.", "Del-nadres.", "Asha-felna.", "Farewell.", "Go in peace.", "Good luck, friend.", "Goodbye."]
					},
					"blood elf": {
						"greetings": ["Anaria Shola.", "Bal'a dash, malanore.", "We will persevere!", "Our enemies will fall!", "Victory lies ahead!", "An'u belore delen'na.", "What business have you?", "Glory to the Sin'dorei.", "Yes?", "State your business.", "The Eternal Sun guides us.", "The dark times will pass."],
						"farewells": ["Farewell.", "We will have justice!", "Death to all who oppose us!", "The reckoning is at hand!", "Sela'ma ashal'anore!", "Remember the Sunwell.", "Stay the course.", "Time is of the essense.", "Shorel'aran.", "Keep your wits about you.", "Hold your head high."]
					},
					"draenei": {
						"greetings": ["Blessings upon you.", "Archenon poros. (Good fortune.)", "Krona ki cristorr! (The Legion will fall!)", "May the light embrace you.", "The Naaru have not forgotten us.", "Each day is a blessing.", "Good fortune!", "Open your heart to the light.", "The Legion will fall.", "The Legion's end draws near.", "More wishes to you."],
						"farewells": ["May your days be long and your hardships few.", "Be well.", "Remember the lessons of the past.", "Do not lose faith.", "Dioniss aca. (Safe journey.)", "Be kind to those less fortunate.", "Favor the road traveled by few.", "Remain vigilant.", "Safe journey.", "Blessings upon your family.", "Good health, long life."]
					},
					"gnome": {
						"greetings": ["Hey.", "Greetings!", "Salutations!", "Honored, I'm sure.", "Good day to you.", "My, you're a tall one!", "Hmmm, interesting.", "Pleased to meet you!", "Can I help you?", "Very good.", "Need assistance?"],
						"farewells": ["You have a great day now.", "Very good.", "Very well then.", "Off and away.", "Be seeing you.", "Daylight's burning.", "Right.", "Alrighty, then!"]
					},
					"goblin": {
						"greetings": ["I got what you need.", "Got the best deals anywheres.", "Can I lighten up that coin purse for ya?", "You break it, you buy it.", "I ain't got it, you don't want it.", "Cha-ching!", "Have I got a deal for you.", "This stuff sells itself.", "I know a buyer when I see one.", "I ain't getting paid to chat.", "Smart mouth, huh?", "Heheh, big shot huh?", "It's my way or the highway, pal!", "No loitering, whatever that means.", "I got no respect around here.", "You looking at me?", "Yo, can I help you with something?", "What's the word on the street?", "Yeah, yeah.", "I've seen you around here before?", "What's shaking?", "G.T.L, friend: Gambling, Tinkering, Laundry!", "Wazzup?", "Yeah, what ya want?", "Well, spit it out!", "Heeey, how ya doing?", "Yo!", "Don't waste my time!", "What!?", "Quickly, quickly!", "Go, go!", "Make sense!"],
						"farewells": ["That's it? I got mouths to feed pal.", "Goblin products are built to blast.", "Come back anytime.", "You drive a hard bargain.", "New shipment coming in soon.", "The pleasure was all mine.", "Can I interest you in a payment plan?", "Glad I can help.", "If you ever need anything.", "Pleasure doing business with ya.", "Hey, I got your back.", "If you can make it here, you can make it anywhere.", "This gang ain't so bad.", "Get lost will you?", "Don't trying anything stupid.", "Stay strong pal.", "Do not get on Gallywix's bad side...", "Yeesh, talk my head off why don't ya?", "Security, enforcement, extortion, we do it all.", "You ever need anything, you know where to find me.", "Be careful out there.", "Keep it real.", "Catch ya on the flip side.", "Don't be a stranger.", "See ya round, friend.", "Go get 'em champ.", "Keep your ear to the ground.", "Have a good one.", "Glad I can help.", "Hit the road!", "On your way!", "Move it!", "Go, go!", "Careful out there!"]
					},
					"human": {
						"greetings": ["Hello there.", "Greetings.", "Light be with you.", "What can I do for you?", "Well met.", "Need help?", "King's honor, friend.", "You need somethin'?", "Can I help you?", "How are you?", "Hey there.", "Hello.", "Good day to you."],
						"farewells": ["Farewell.", "Be careful.", "Go with honor, friend.", "Safe travels!", "For the Alliance.", "See you around.", "Light bless you.", "Have a good one."]
					},
					"orc": {
						"greetings": ["Speak.", "Speak friend.", "Zug zug!", "For the Horde!", "Blood and thunder!", "Strength and honor!", "Lok'tar!", "Thrall hall!", "Mok'ra!", "What do you need?", "What can I help you with?", "What you need?", "Greetings."],
						"farewells": ["Dabu.", "For the Horde!", "Go forth to victory.", "Strength.", "Go with honor.", "Farewell.", "Victory.", "Be safe.", "May your blades never dull."]
					},
					"pandaren": {
						"greetings": ["Speak up.", "Hmm?", "Slow down.", "What do you need?", "Hello.", "Greetings wanderer.", "Tell me of your travels.", "Welcome."],
						"farewells": ["Goodbye.", "Enough of that.", "Until next time.", "White Tiger watch over you.", "Jade Serpent guide you.", "Next one is on me.", "May the Mists protect you.", "There is no hurry."]
					},
					"tauren": {
						"greetings": ["Peace friend.", "Hail.", "How?", "How may I aid you?", "What brings you here?", "Ah, I've been expecting you.", "Well met.", "Greetings, traveler.", "Greetings.", "The winds guide you.", "I've been expecting you."],
						"farewells": ["Walk with the Earth Mother.", "Winds be at your back.", "Go in peace.", "May the eternal sun shine upon thee.", "Be careful.", "We shall meet again.", "Ancestors watch over you.", "Farewell.", "Goodbye."]
					},
					"troll": {
						"greetings": ["Talk to me.", "Eh there.", "Who you be?", "Hello mon.", "Greetings mon.", "What be on ya mind?", "How ya doing mon?", "Relax.", "Lo' mon.", "Don't be shy.", "What'chu want?", "You come get da Voodoo."],
						"farewells": ["Layta.", "Ookie Dookie.", "See ya layta.", "Stay away from the Voodoo.", "You be careful mon.", "Be seeing ya.", "Spirits be with ya mon."]
					},
					"worgen": {
						"greetings": ["Ain't you a chipper looking one?", "We've been walled up for far too long.", "Oi!", "Any friend of Greymane is a friend of mine.", "I've got a bad feeling.", "Get gabbing or get going.", "What can I do for you?", "What's your story?", "Yes?"],
						"farewells": ["Watch your back!", "Long live Greymane.", "Farewell.", "Good day.", "Keep your chin up, eh?", "That's enough gabbing from me today.", "Let the light of the new moon guide you.", "We are bound by a common enemy.", "You wouldn't want to see me when I'm angry."]
					},
					"undead": {
						"greetings": ["What do you require?", "This had better be good.", "What is it?", "Speak quickly.", "I'm listening.", "What do you ask of death?", "We are Forsaken.", "I am Forsaken.", "What now?!", "Hello?", "And you are...?"],
						"farewells": ["Dark Lady watch over you.", "Victory for Sylvanas.", "Watch your back.", "Trust no one.", "Do not seek death.", "Goodbye.", "Our time will come.", "Beware, our enemies abound.", "Beware the living.", "Remember, patience... discipline.", "Embrace the shadow."]
					}
				}

def find_user_info(user_id):
	url = BASE_URL + "/users.info?token={0}&user={1}".format(API_TOKEN, user_id)
	response = requests.get(url)

	user = response.json()["user"]
	username = user["name"]
	icon_url = user["profile"]["image_48"]

	return {"username": username, "icon_url": icon_url}

# Create your views here.
def index(request):
	if request.method == 'GET':
		print "Order up!"
		print request.GET
		inputs = dict(request.GET)

		if 'token' in inputs and inputs['token'][0] == "cL9cTdOYUlMGaD8ozxpYw2oM":

			if 'text' in inputs and inputs['text'] != []:

				## get list of all given command words
				text = inputs['text'][0].split(" ")

				## first should be my main command
				greeting_or_farewell = text[0].lower()
				
				## second is optional, specifies race
				if len(text) > 1:
					if text[1].lower() == "night" and text[2].lower() == "elf":
						desired_race = "night elf"
					elif text[1].lower() == "blood" and text[2].lower() == "elf":
						desired_race = "blood elf"
					else:
						desired_race = text[1].lower()
						if desired_race not in greeting_dict:
							## return an unknown race error
							return JsonResponse({"text":"Sorry friend, afraid I've never seen specimen of the %(desired_race)s species round these parts.\nWorld of Warcraft races available for you to choose from are: %(races)s"%{"desired_race":desired_race, "races":greeting_dict.keys()}})
				else:
					desired_race = random.choice(greeting_dict.keys())


				## check first greeting or farewell or unknown
				if greeting_or_farewell == "greeting":
					wow_message = random.choice(greeting_dict[desired_race]['greetings'])

					user_stuff = find_user_info(inputs['user_id'][0])

					requests.post(inputs['response_url'][0], data=json.dumps({"text":"Master @%(username)s says: %(wow_message)s"%{'username':inputs['user_name'][0], 'wow_message':wow_message}, "response_type":"in_channel", "username":user_stuff['username'], "icon_url": user_stuff['icon_url']}))
					return HttpResponse(status=201)

				elif greeting_or_farewell == "farewell":
					wow_message = random.choice(greeting_dict[desired_race]['farewells'])
					requests.post(inputs['response_url'][0], data=json.dumps({"text":"Master @%(username)s says: %(wow_message)s"%{'username':inputs['user_name'][0], 'wow_message':wow_message}, "response_type":"in_channel"}))
					return HttpResponse(status=201)

				elif greeting_or_farewell == "":
					return JsonResponse({"text":"Try either 'greeting' or 'farewell' and I'll return a random World of Warcraft quote of that type. :crossed_swords:"})

				elif greeting_or_farewell == "races":
					return JsonResponse({"text":"World of Warcraft races available for you to choose from are: %(races)s  (Make your selection after 'greeting' or 'farewell')"%{"races":greeting_dict.keys()}})

				else:
					return JsonResponse({"text":"Sorry friend, afraid I'm not attuned to %(input_text)s in these parts.  You'll have better luck with either 'greeting' or 'farewell'. :crossed_swords:."%{'input_text': text[0]}})






def db(request):

    greeting = Greeting()
    greeting.save()

    greetings = Greeting.objects.all()

    return render(request, 'db.html', {'greetings': greetings})

