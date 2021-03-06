#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import datetime
import parse
import sys

import pytwis
from pytwis import PytwisConst

def validate_command(raw_command):
    parsed_command = raw_command.split()
    arg_count = len(parsed_command) - 1

    if (len(parsed_command) == 0):
        return

    if (parsed_command[0] == PytwisConst.CMD_REGISTER):
        if (arg_count < 2):
            raise ValueError('register {user_name} {password}')
    elif (parsed_command[0] == PytwisConst.CMD_LOGIN):
        if (arg_count < 2):
            raise ValueError('login {user_name} {password}')
    elif (parsed_command[0] == PytwisConst.CMD_LOGOUT):
        pass
    elif (parsed_command[0] == PytwisConst.CMD_CHANGE_PASSWORD):
        if (arg_count < 3):
            raise ValueError('changepassword {old_password} {new_password} {confirmed_new_password}')
    elif (parsed_command[0] == PytwisConst.CMD_POST):
        if (arg_count < 1):
            raise ValueError('post {tweet}')
    elif (parsed_command[0] == PytwisConst.CMD_FOLLOW):
        if (arg_count < 1):
            raise ValueError('follow {followee}')
    elif (parsed_command[0] == PytwisConst.CMD_UNFOLLOW):
        if (arg_count < 1):
            raise ValueError('unfollow {followee}')
    elif (parsed_command[0] == PytwisConst.CMD_FOLLOWERS):
        pass
    elif (parsed_command[0] ==PytwisConst.CMD_FOLLOWINGS):
        pass
    elif (parsed_command[0] == PytwisConst.CMD_TIMELINE):
        if (arg_count > 2):
            raise ValueError('timeline {tweet count} or timeline')
    elif (parsed_command[0] == 'exit') or (parsed_command[0] == 'quit'):
        pass
    else:
        raise ValueError('Invalid pytwis command')


def pytwis_command_parser(raw_command):
    # Separate the command from its arguments.
    splited_raw_command = raw_command.split(' ', 1)
    command_with_args = [splited_raw_command[0]]

    # Some command (e.g., logout) may not have arguments.
    arg_dict = {}

    validate_command(raw_command)

    if command_with_args[0] == PytwisConst.CMD_REGISTER:
        # register must have two arguments: username and password.
        args = splited_raw_command[1]
        arg_dict = parse.parse('{username} {password}', args)
        if arg_dict is None:
            raise ValueError('register has incorrect arguments')
        elif ' ' in arg_dict[PytwisConst.PASSWORD]:
            raise ValueError("password can't contain spaces")

        print('register: username = {}, password = {}'.format(arg_dict[PytwisConst.USERNAME], arg_dict[PytwisConst.PASSWORD]))
    elif command_with_args[0] == PytwisConst.CMD_LOGIN:
        # login must have two arguments: username and password.
        args = splited_raw_command[1]
        arg_dict = parse.parse('{username} {password}', args)
        if arg_dict is None:
            raise ValueError('login has incorrect arguments')

        print('login: username = {}, password = {}'.format(arg_dict[PytwisConst.USERNAME], arg_dict[PytwisConst.PASSWORD]))
    elif command_with_args[0] == PytwisConst.CMD_LOGOUT:
        # logout doesn't have any arguments.
        pass
    elif command_with_args[0] == PytwisConst.CMD_CHANGE_PASSWORD:
        # changepassword must have three arguments: old_password, new_password, and confirmed_new_password.
        args = splited_raw_command[1]
        arg_dict = parse.parse('{old_password} {new_password} {confirmed_new_password}', args)
        if arg_dict is None:
            raise ValueError('changepassword has incorrect arguments')
        elif arg_dict[PytwisConst.NEW_PASSWORD] != arg_dict[PytwisConst.CONFIRM_PASSWORD]:
            raise ValueError('The confirmed new password is different from the new password')
        elif arg_dict[PytwisConst.NEW_PASSWORD] == arg_dict[PytwisConst.OLD_PASSWORD]:
            raise ValueError('The new password is the same as the old password')

        print('changepassword: old = {}, new = {}'.format(arg_dict[PytwisConst.OLD_PASSWORD], arg_dict[PytwisConst.NEW_PASSWORD]))
    elif command_with_args[0] == PytwisConst.CMD_POST:
        # post must have one argument: tweet
        arg_dict = {PytwisConst.TWEET: splited_raw_command[1]}
    elif command_with_args[0] == PytwisConst.CMD_FOLLOW:
        # follow must have one argument: followee.
        arg_dict = {PytwisConst.FOLLOWEE: splited_raw_command[1]}
    elif command_with_args[0] == PytwisConst.CMD_UNFOLLOW:
        # unfollow must have one argument: followee.
        arg_dict = {PytwisConst.FOLLOWEE: splited_raw_command[1]}
    elif command_with_args[0] == PytwisConst.CMD_FOLLOWERS:
        # followers doesn't have any arguments.
        pass
    elif command_with_args[0] ==PytwisConst.CMD_FOLLOWINGS:
        # followings doesn't have any arguments.
        pass
    elif command_with_args[0] == PytwisConst.CMD_TIMELINE:
        # timeline has either zero or one argument.
        max_cnt_tweets = -1
        if len(splited_raw_command) >= 2:
            max_cnt_tweets = int(splited_raw_command[1])

        arg_dict = {PytwisConst.MAX_TWEET_CNT: max_cnt_tweets}
    elif command_with_args[0] == 'exit' or command_with_args[0] == 'quit':
        # exit or quit doesn't have any arguments.
        pass
    else:
        pass

    command_with_args.append(arg_dict)

    return command_with_args


def print_tweets(tweets):
    print('=' * 60)
    for index, tweet in enumerate(tweets):
        print('-' * 60)
        print('Tweet {}:'.format(index))
        print('Username:', tweet[PytwisConst.USERNAME])
        print('Time:', datetime.datetime.fromtimestamp(int(tweet['unix_time'])).strftime('%Y-%m-%d %H:%M:%S'))
        print('Body:\n\t', tweet['body'])
        print('-' * 60)
    print('=' * 60)


def pytwis_command_processor(twis, auth_secret, command_with_args):
    command = command_with_args[0]
    args = command_with_args[1]

    if command == PytwisConst.CMD_REGISTER:
        succeeded, result = twis.register(args[PytwisConst.USERNAME], args[PytwisConst.PASSWORD])
        if succeeded:
            print('Succeeded in registering {}'.format(args[PytwisConst.USERNAME]))
        else:
            print('Failed to register {} with error = {}'.format(args[PytwisConst.USERNAME], result['error']))
    elif command == PytwisConst.CMD_LOGIN:
        succeeded, result = twis.login(args[PytwisConst.USERNAME], args[PytwisConst.PASSWORD])
        if succeeded:
            auth_secret[0] = result[PytwisConst.AUTH]
            print('Succeeded in logging into username {}'.format(args[PytwisConst.USERNAME]))
        else:
            print("Couldn't log into username {} with error = {}".format(args[PytwisConst.USERNAME], result['error']))
    elif command == PytwisConst.CMD_LOGOUT:
        succeeded, result = twis.logout(auth_secret[0])
        if succeeded:
            auth_secret[0] = result[PytwisConst.AUTH]
            print('Logged out of username {}'.format(result[PytwisConst.USERNAME]))
        else:
            print("Couldn't log out with error = {}".format(result['error']))
    elif command == PytwisConst.CMD_CHANGE_PASSWORD:
        succeeded, result = twis.change_password(auth_secret[0], args[PytwisConst.OLD_PASSWORD], args[PytwisConst.NEW_PASSWORD])
        if succeeded:
            auth_secret[0] = result[PytwisConst.AUTH]
            print('Succeeded in changing the password')
        else:
            print("Couldn't change the password with error = {}".format(result['error']))
    elif command == PytwisConst.CMD_POST:
        succeeded, result = twis.post_tweet(auth_secret[0], args[PytwisConst.TWEET])
        if succeeded:
            print('Succeeded in posting the tweet')
        else:
            print("Couldn't post the tweet with error = {}".format(result['error']))
    elif command == PytwisConst.CMD_FOLLOW:
        succeeded, result = twis.follow(auth_secret[0], args[PytwisConst.FOLLOWEE])
        if succeeded:
            print('Succeeded in following username {}'.format(args[PytwisConst.FOLLOWEE]))
        else:
            print("Couldn't follow the username {} with error = {}".format(args[PytwisConst.FOLLOWEE], result['error']))
    elif command == PytwisConst.CMD_UNFOLLOW:
        succeeded, result = twis.unfollow(auth_secret[0], args[PytwisConst.FOLLOWEE])
        if succeeded:
            print('Succeeded in unfollowing username {}'.format(args[PytwisConst.FOLLOWEE]))
        else:
            print("Couldn't unfollow the username {} with error = {}".format(args[PytwisConst.FOLLOWEE], result['error']))
    elif command == PytwisConst.CMD_FOLLOWERS:
        succeeded, result = twis.get_followers(auth_secret[0])
        if succeeded:
            print('Succeeded in get the list of {} followers'.format(len(result['follower_list'])))
            print('=' * 20)
            for follower in result['follower_list']:
                print('\t' + follower)
            print('=' * 20)
        else:
            print("Couldn't get the follower list with error = {}".format(result['error']))
    elif command ==PytwisConst.CMD_FOLLOWINGS:
        succeeded, result = twis.get_following(auth_secret[0])
        if succeeded:
            print('Succeeded in get the list of {} followings'.format(len(result['following_list'])))
            print('=' * 60)
            for following in result['following_list']:
                print('\t' + following)
            print('=' * 60)
        else:
            print("Couldn't get the following list with error = {}".format(result['error']))
    elif command == PytwisConst.CMD_TIMELINE:
        succeeded, result = twis.get_timeline(auth_secret[0], args[PytwisConst.MAX_TWEET_CNT])
        if succeeded:
            if auth_secret[0] != '':
                print('Succeeded in get {} tweets in the user timeline'.format(len(result[PytwisConst.TWEETS])))
            else:
                print('Succeeded in get {} tweets in the general timeline'.format(len(result[PytwisConst.TWEETS])))
            print_tweets(result[PytwisConst.TWEETS])
        else:
            if auth_secret[0] != '':
                print("Couldn't get the user timeline with error = {}".format(result['error']))
            else:
                print("Couldn't get the general timeline with error = {}".format(result['error']))
    else:
        pass

def pytwis_cli_init():
    # TODO: Add epilog for the help information about online commands after connecting to the Twitter clone.
    parser = argparse.ArgumentParser(description= \
                                         'Connect to the Redis database of a Twitter clone and '
                                         'then run commands to access and update the database.')
    parser.add_argument('-n', '--hostname', dest='redis_hostname', default='127.0.0.1',
                        help='the Redis server hostname. If not specified, will be defaulted to 127.0.0.1.')
    parser.add_argument('-t', '--port', dest='redis_port', default=6379,
                        help='the Redis server port. If not specified, will be defaulted to 6379.')
    parser.add_argument('-d', '--database', dest='redis_database', default=0,
                        help='the Redis server database. If not specified, will be defaulted to 0.')
    parser.add_argument('-p', '--password', dest='redis_password', default='',
                        help='the Redis server password. If not specified, will be defaulted to an empty string.')

    args = parser.parse_args()

    print('The input Redis server hostname is {}.'.format(args.redis_hostname))
    print('The input Redis server port is {}.'.format(args.redis_port))
    print('The input Redis server database is {}.'.format(args.redis_database))
    if args.redis_password != '':
        print('The input Redis server password is "{}".'.format(args.redis_password))
    else:
        print('The input Redis server password is empty.')

    try:
        return pytwis.Pytwis(args.redis_hostname, args.redis_port, args.redis_database, args.redis_password), args
    except ValueError as e:
        print('Failed to connect to the Redis server: {}'.format(str(e)),
              file=sys.stderr)
        return None, None


def pytwis_cli():
    twis, args = pytwis_cli_init()
    if twis == None:
        return

    auth_secret = ['']
    while True:
        try:
            command_with_args = pytwis_command_parser(
                input('Please enter a command '
                      '(register, login, logout, changepassword, post, '
                      'follow, unfollow, followers, followings, timeline):\n{}:{}> ' \
                      .format(args.redis_hostname, args.redis_port)))
            if command_with_args[0] == "exit" or command_with_args[0] == 'quit':
                # Log out of the current user before exiting.
                if len(auth_secret[0]) > 0:
                    pytwis_command_processor(twis, auth_secret, [PytwisConst.CMD_LOGOUT, {}])
                print('pytwis is exiting.')
                return 0;

        except ValueError as e:
            print('Invalid pytwis command: {}'.format(str(e)),
                  file=sys.stderr)
            continue

        pytwis_command_processor(twis, auth_secret, command_with_args)


if __name__ == "__main__":
    pytwis_cli()
