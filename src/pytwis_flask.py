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
auth_secret = ['']
twis = None
# twis =  pytwis.Pytwis(server, port, password)

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
    global auth_secret
    command = request.args['cmd']
    print(command)
    command_with_args = [request.args['cmd'], request.args]
    response = pytwis_get_request_processor(twis, auth_secret, command_with_args)
    print(response)
    return response

def pytwis_get_request_processor(twis, auth_secret, command_with_args):
    command = command_with_args[0]
    args = command_with_args[1]

    if command == 'register':
        succeeded, result = twis.register(args['username'], args['password'])
    elif command == 'login':
        succeeded, result = twis.login(args['username'], args['password'])
        if succeeded:
            auth_secret[0] = result['auth'] # Need to move this to front end service
    elif command == 'logout':
        succeeded, result = twis.logout(auth_secret[0])
        if succeeded:
            auth_secret[0] = ''
    elif command == 'changepassword':
        succeeded, result = twis.change_password(auth_secret[0], args['old_password'], args['new_password'])
        if succeeded:
            auth_secret[0] = result['auth']
    elif command == 'post':
        succeeded, result = twis.post_tweet(auth_secret[0], args['tweet'])
    elif command == 'follow':
        succeeded, result = twis.follow(auth_secret[0], args['followee'])
    elif command == 'unfollow':
        succeeded, result = twis.unfollow(auth_secret[0], args['followee'])
    elif command == 'followers':
        succeeded, result = twis.get_followers(auth_secret[0])
    elif command == 'followings':
        succeeded, result = twis.get_following(auth_secret[0])
    elif command == 'timeline':
        if('max_cnt_tweets' in args):
            succeeded, result = twis.get_timeline(auth_secret[0], int(args['max_cnt_tweets']))
        else:
            succeeded, result = twis.get_timeline(auth_secret[0], twis.GENERAL_TIMELINE_MAX_POST_CNT)
    else:
        pass

    print(json.dumps(result, sort_keys=True, indent=4)) # Beautified Json for debugging with logs
    return json.dumps(result)

if __name__ ==  "__main__":
    app.run()