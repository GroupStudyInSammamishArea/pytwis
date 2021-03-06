# 
# REST API for pytwis
#
# Resource      Action      Operation
# ===========================================================================
# users         POST        Create a new user (register)
#               GET         Get the information of a user (implicit login, 
#                           following and follower)
#               PUT         Modify a user (change his followers, change his 
#                           password)
# posts         POST        Post a new tweet
#               GET         Get timeline
#
#
# How to run:
# Borrowing code from pytwis_clt.py, if everything about Redis is by default:
# python3 pytwis_rest.py
#
# How to test:
# Use curl tool. For example, to get information of a user
#   curl -H "Content-type: application/json" 
#       -X GET http://127.0.0.1:5000/pytwis/api/v1.0/users 
#       -d '{"username":"gavin","password":"gavin"}'
# To modify password
#   curl -H "Content-type: application/json" 
#       -X PUT http://127.0.0.1:5000/pytwis/api/v1.0/users
#       -d '{"username":"gavin","password":"gavin", "new_password":"g"}'
#

from flask import Flask, jsonify, request, abort, make_response
import pytwis
import time
import sys
import argparse

app = Flask(__name__)

PROJECT_NAME = 'pytwis'
PYTWIS_API_VERSION = "1.0"

HTTP_INDEX_URL = '/' + PROJECT_NAME + '/api/v' + PYTWIS_API_VERSION + '/'

g_pytwis = 0

# Project information
@app.route(HTTP_INDEX_URL)
def index():
        about = {
            'projectname': PROJECT_NAME,
            'apiversion': PYTWIS_API_VERSION,
            'timestamp': time.time()
        }
        return jsonify({'projectinfo':about})

@app.route(HTTP_INDEX_URL+'users', methods=['POST'])
def register_user():
    if not request.json or not PytwisConst.USERNAME in request.json or not PytwisConst.PASSWORD in request.json:
        abort(400)
    # Call twis API to register a new user
    succeeded, result = g_pytwis.register(request.json[PytwisConst.USERNAME], request.json[PytwisConst.PASSWORD])
    if succeeded:
        server_resp = {
            'userid': result[g_pytwis.USER_ID_PROFILE_USERID_NAME],
            PytwisConst.USERNAME: request.json[PytwisConst.USERNAME],
            PytwisConst.AUTH: result[g_pytwis.USER_ID_PROFILE_AUTH_KEY]
        }
        return jsonify(server_resp)
    else:
        return make_response(jsonify(process_error(result)), 404)

@app.route(HTTP_INDEX_URL+'users', methods=['GET'])
def get_user_info():
    # Initialize user properties
    userinfo = {
        'userid': 'n/a',
        PytwisConst.USERNAME: 'n/a'
    }
    auth = ''

    if not request.json: 
        abort(400)
    # If there is a set of credentials, try login first
    elif PytwisConst.USERNAME in request.json and PytwisConst.PASSWORD in request.json:
        succeeded, result = g_pytwis.login(request.json[PytwisConst.USERNAME], request.json[PytwisConst.PASSWORD])
        if succeeded:
            print(result, sys.stderr)
            auth = result[g_pytwis.USER_ID_PROFILE_AUTH_KEY]
            userinfo[PytwisConst.USERNAME] = request.json[PytwisConst.USERNAME]
        else:
            return make_response(jsonify(process_error(result)), 404)
    # If there is auth information, use it.
    elif PytwisConst.AUTH in request.json:
        auth = request.json[PytwisConst.AUTH]
    else:
        abort(400)

    succeeded, result = g_pytwis.get_followers(auth)
    if succeeded:
        userinfo[PytwisConst.CMD_FOLLOWERS] = result['follower_list']
    else:
        return make_response(jsonify(process_error(result)), 404)
    
    succeeded, result = g_pytwis.get_following(auth)
    if succeeded:
        userinfo['followings'] = result['following_list']
    else:
        return make_response(jsonify(process_error(result)), 404)

    return jsonify({'userinfo': userinfo})

@app.route(HTTP_INDEX_URL+'users', methods=['PUT'])
def update_user():
    auth=''
    if not request.json:
        abort(400)
    # If there is a set of credentials, try login first
    elif PytwisConst.USERNAME in request.json and PytwisConst.PASSWORD in request.json:
        succeeded, result = g_pytwis.login(request.json[PytwisConst.USERNAME], request.json[PytwisConst.PASSWORD])
        if succeeded:
            auth = result[g_pytwis.USER_ID_PROFILE_AUTH_KEY]
        else:
            return make_response(jsonify(process_error(result)), 404)
    elif PytwisConst.AUTH in request.json:
        auth = request.json[PytwisConst.AUTH]

    succeeded = False
    result = {'error': "Unknown operation"}
    if 'added_follower' in request.json:
        succeeded, result = g_pytwis.follow(request.json['added_follower'])
    elif 'removed_follower' in request.json:
        succeeded, result = g_pytwis.unfollow(request.json['removed_follower'])
    elif PytwisConst.NEW_PASSWORD in request.json and PytwisConst.PASSWORD in request.json:
        succeeded, result = g_pytwis.change_password(auth, request.json[PytwisConst.PASSWORD], request.json[PytwisConst.NEW_PASSWORD])

    if succeeded:
        return make_response(jsonify(result), 200)
    else:
        return make_response(jsonify(process_error(result)), 404)

@app.route(HTTP_INDEX_URL+'posts', methods=['POST'])
def add_post():
    auth=''
    if not request.json or not 'tweet_content' in request.json:
        abort(400)
    # If there is a set of credentials, try login first
    elif PytwisConst.USERNAME in request.json and PytwisConst.PASSWORD in request.json:
        succeeded, result = g_pytwis.login(request.json[PytwisConst.USERNAME], request.json[PytwisConst.PASSWORD])
        if succeeded:
            auth = result[g_pytwis.USER_ID_PROFILE_AUTH_KEY]
        else:
            return make_response(jsonify(process_error(result)), 404)
    elif PytwisConst.AUTH in request.json:
        auth = request.json[PytwisConst.AUTH]

    succeeded, result = g_pytwis.post_tweet(auth, request.json['tweet_content'])
    if succeeded:
        return make_response(jsonify(result), 200)
    else:
        return make_response(jsonify(process_error(result)), 404)

@app.route(HTTP_INDEX_URL+'posts', methods=['GET'])
def get_timeline():
    auth=''
    if not request.json or not 'tweet_content' in request.json:
        abort(400)
    # If there is a set of credentials, try login first
    elif PytwisConst.USERNAME in request.json and PytwisConst.PASSWORD in request.json:
        succeeded, result = g_pytwis.login(request.json[PytwisConst.USERNAME], request.json[PytwisConst.PASSWORD])
        if succeeded:
            auth = result[g_pytwis.USER_ID_PROFILE_AUTH_KEY]
        else:
            return make_response(jsonify(process_error(result)), 404)
    elif PytwisConst.AUTH in request.json:
        auth = request.json[PytwisConst.AUTH]

    succeeded, result = g_pytwis.get_timeline(auth)
    if succeeded:
        return make_response(jsonify(result), 200)
    else:
        return make_response(jsonify(process_error(result)), 404)

def process_error(server_result):
    errorinfo = {
        'server_msg': server_result['error'],
        'timestamp': time.time()
    }
    return errorinfo

def pytwis_rest():
    parser = argparse.ArgumentParser(description= \
                                         'Connect to the Redis database of a Twitter clone and '
                                         'then run commands to access and update the database.')
    parser.add_argument('-d', '--hostname', dest='redis_hostname', default='127.0.0.1',
                        help='the Redis server hostname. If not specified, will be defaulted to 127.0.0.1.')
    parser.add_argument('-t', '--port', dest='redis_port', default=6379,
                        help='the Redis server port. If not specified, will be defaulted to 6379.')
    parser.add_argument('-p', '--password', dest='redis_password', default='',
                        help='the Redis server password. If not specified, will be defaulted to an empty string.')

    args = parser.parse_args()

    print('The input Redis server hostname is {}.'.format(args.redis_hostname))
    print('The input Redis server port is {}.'.format(args.redis_port))
    if args.redis_password != '':
        print('The input Redis server password is "{}".'.format(args.redis_password))
    else:
        print('The input Redis server password is empty.')

    try:
        global g_pytwis
        g_pytwis = pytwis.Pytwis(args.redis_hostname, args.redis_port, args.redis_password)
    except ValueError as e:
        print('Failed to connect to the Redis server: {}'.format(str(e)),
              file=sys.stderr)
        return -1

if __name__ == '__main__':
    if not pytwis_rest() == -1:
        app.run(debug=True)