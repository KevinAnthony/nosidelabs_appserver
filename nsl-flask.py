from __future__ import print_function # In python 2.7


from flask import Flask, flash
from flask import request, json, g, session
from flask import abort, redirect, url_for
from flask_openid import OpenID 

import requests
import urllib
import re

from crossdomain import crossdomain

import sys

app = Flask(__name__)
steam_api_key = "71DE25185EB70B6040AFCC7D6E8799D9" 
oid = OpenID(app)

#origin = 'http://www.nosidelabs.com'
origin = '*'

@app.before_request
def before_request():
    g.user = None
    if 'steamid' in session:
        g.user = session['steamid']
    g.friends = None
    if 'friends' in session:
        g.friends = session['friends'] 

@app.after_request
def after_request(response):
    session['steamid'] = g.user
    session['friends'] = g.friends
    return response

@app.route('/steam/login/', methods=['GET', 'OPTIONS'])
@crossdomain(origin=origin)
@oid.loginhandler
def login():
    if g.user is not None:
        return redirect(oid.get_next_url())
    return oid.try_login('http://steamcommunity.com/openid')

@oid.after_login
def create_or_login(resp):
    match = re.compile('steamcommunity.com/openid/id/(.*?)$').search(resp.identity_url)
    g.user = match.group(1)
    session['steamid'] = g.user
    return redirect(oid.get_next_url())

@app.route('/steam/GetPlayerSummery', methods=['GET', 'OPTIONS'])
@crossdomain(origin=origin)
def steam_get_player_summery():
    url = steam_build_url("ISteamUser","GetPlayerSummaries",2,[("steamids",session['steamid'])])
    text = steam_call_url(url) 
    return text

@app.route('/steam/PopulateFriendList', methods=['GET', 'OPTIONS'])
@crossdomain(origin=origin)
def steam_populate_friend_list():
    url = steam_build_url("ISteamUser","GetFriendList",1,[("relationship","friend")])
    jsontext = json.loads(steam_call_url(url))
    friends = jsontext["friendslist"]["friends"]
    friend_dict = {}
    for friend in friends:
        friend_id = friend["steamid"]
        gamelist = []
        url = steam_build_url("IPlayerService","GetOwnedGames",1,[("include_appinfo","1")], friend_id)
        response = json.loads(steam_call_url(url));
        if "games" in response["response"]:
            games = response["response"]["games"]
        else:
            continue #Profile Priavte
        for game in games:
            gamelist.append(game["appid"])
        friend_dict[friend_id] = gamelist
    g.friends = friend_dict
    return json.dumps(friend_dict)

@app.route('/steam/LoginInfo', methods=['GET', 'OPTIONS'])
@crossdomain(origin=origin)
def steam_get_login_info():
    if not 'steamid' in session:
        return "<a href='http://api.nosidelabs.com/steam/login'><img src='http://cdn.steamcommunity.com/public/images/signinthroughsteam/sits_01.png'>"
    else:
        return "<a href='http://api.nosidelabs.com/steam/login'><img src='http://cdn.steamcommunity.com/public/images/signinthroughsteam/sits_02.png'>"

def steam_build_url(app, function, version, params, sid = None):
    if (sid is None):
        sid = session['steamid']
    params.insert(0,("steamid",sid))
    params.insert(0,("key", steam_api_key))
    return "http://api.steampowered.com/" + app + '/' +function + '/v' + str(version) + '/?' + urllib.urlencode(params)

def steam_call_url(url):
    return requests.get(url).text

# run the app.
if __name__ == "__main__":
    app.secret_key = 'ItsTheEndOfTheWorldAsWeKnowIT'
    app.config['SESSION_TYPE'] = 'filesystem'
    
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    app.debug = True
    app.run(host='0.0.0.0', port=80)
