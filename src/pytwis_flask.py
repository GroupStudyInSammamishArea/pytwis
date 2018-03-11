import datetime
from flask import Flask
import json
import pytwis_clt
import pytwis
from flask import request


## Todo
# 1. Need to add request context information in to the result json strig.
#
# requestId <- from a request.
# command
# userAuthSecrete <- from a request. or generated by login
# sessionId <- we don't support a session yet.
# referenceTag <- tag for filtering log
#
# 2. Add requestId and userAuthSecrete in request parameter
#
# 3. Logging
# Call log --> String dump. so we can replay traffic for testing performance
# Response log
# --> ELK (Elastic search, Log stash, and Kibana) setup for this?
#
# Need to have a key/constant class for key and params in pytwis.

## Commands
# Init
# http://127.0.0.1:5000/init?server=<ip_address>&port=<port>&password=<password>

# Register/Login/Login/Post works.

# http://127.0.0.1:5000/pytwis?cmd=register&username=bjlee3&password=test3
# http://127.0.0.1:5000/pytwis?cmd=login&username=bjlee3&password=test3
# http://127.0.0.1:5000/pytwis?cmd=followers
# http://127.0.0.1:5000/pytwis?cmd=post&tweet=test12345
# http://127.0.0.1:5000/pytwis?cmd=timeline

app = Flask(__name__)
# twis = None
twis =  pytwis.Pytwis("34.217.79.234", "6379", "twitter-redis-sammamish")

@app.route('/')
def homepage():
    return "Hello Sammamish Study Group"

@app.route('/test', methods=['GET','POST'])
def test_request():
    try:
        if(request.method == 'GET'):
            name = request.args['name']
            return 'GET' + name
    except ValueError as e:
        return "error"

@app.route('/init', methods=['GET'])
def init():
    try:
        global twis

        if(request.method == 'GET'):
            server = request.args['server']
            port = request.args['port']
            password = request.args['password']
            twis =  pytwis.Pytwis(server, port, password)
            if twis is None:
                return "Error"
            else:
                return "Success"
    except ValueError as e:
        return "error"

@app.route('/pytwis', methods=['GET'])
def pytwis_get_request():

    command = request.args['cmd']
    print(command)
    command_with_args = [request.args['cmd'], request.args]

    response = pytwis_get_request_processor(twis, request.args['auth'], command_with_args)

    jsonResponse = json.loads(response)
    print(json.dumps(jsonResponse, sort_keys=True, indent=4))  # Beautified Json for debugging with logs

    return response

def pytwis_get_request_processor(twis, auth_secret, command_with_args):
    command = command_with_args[0]
    args = command_with_args[1]

    if command == 'register':
        succeeded, result = twis.register(args['username'], args['password'])
    elif command == 'login':
        succeeded, result = twis.login(args['username'], args['password'])
    elif command == 'logout':
        succeeded, result = twis.logout(auth_secret)
    elif command == 'changepassword':
        succeeded, result = twis.change_password(auth_secret, args['old_password'], args['new_password'])
    elif command == 'post':
        succeeded, result = twis.post_tweet(auth_secret, args['tweet'])
    elif command == 'follow':
        succeeded, result = twis.follow(auth_secret, args['followee'])
    elif command == 'unfollow':
        succeeded, result = twis.unfollow(auth_secret, args['followee'])
    elif command == 'followers':
        succeeded, result = twis.get_followers(auth_secret)
    elif command == 'followings':
        succeeded, result = twis.get_following(auth_secret)
    elif command == 'timeline':
        if('max_cnt_tweets' in args):
            succeeded, result = twis.get_timeline(auth_secret, int(args['max_cnt_tweets']))
        else:
            succeeded, result = twis.get_timeline(auth_secret, twis.GENERAL_TIMELINE_MAX_POST_CNT)
    else:
        pass

    return json.dumps(result)

if __name__ ==  "__main__":
    app.run(host='0.0.0.0', port=4000)
