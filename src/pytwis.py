# -*- coding: utf-8 -*-

import redis
from redis.exceptions import (ResponseError, TimeoutError, WatchError)
import secrets

class Pytwis:
    
    REDIS_SOCKET_CONNECT_TIMEOUT = 60
    
    NEXT_USER_ID_KEY = 'next_user_id'
    USERS_HASH_KEY = 'users'
    USER_ID_PROFILE_KEY_FORMAT = 'user:{}'
    USER_ID_PROFILE_USERNAME_KEY = 'username'
    USER_ID_PROFILE_PASSWORD_KEY = 'password'
    USER_ID_PROFILE_AUTH_KEY = 'auth'
    AUTHS_HASH_KEY = 'auths'
    
    def __init__(self, hostname = '127.0.0.1', port = 6379, password = ''):
        # TODO: Set unix_socket_path='/tmp/redis.sock' to use Unix domain socket 
        # if the host name is 'localhost'. Note that need to uncomment the following 
        # line in /etc/redis/redis.conf:
        #
        # unixsocket /tmp/redis.sock
        # 
        self._rc = redis.StrictRedis(
            host=hostname,
            port=port,
            password=password,
            decode_responses=True, # Decode the response bytes into strings.
            socket_connect_timeout=self.REDIS_SOCKET_CONNECT_TIMEOUT)
        
        # Test the connection by ping.
        try:
            if self._rc.ping() == True:
                print('Ping {} returned True'.format(hostname))
        except (ResponseError, TimeoutError) as e:
            raise ValueError(str(e)) from e
        
    def _is_loggedin(self, auth_secret):
        # Get the user_id from the authentication secret.
        user_id = self._rc.hget(self.AUTHS_HASH_KEY, auth_secret)
        if user_id is None:
            return (False, None)
        
        # Compare the input authentication secret with the stored one.
        user_id_profile_key = self.USER_ID_PROFILE_KEY_FORMAT.format(user_id)
        stored_auth_secret = self._rc.hget(user_id_profile_key, self.USER_ID_PROFILE_AUTH_KEY)
        if auth_secret == stored_auth_secret:
            return (True, user_id)
        else:
            # TODO: Resolve the inconsistency of the two authentication secrets. 
            return (False, None)

    def register(self, username, password):
        result = {'error': None}
        
        # TODO: add the username check.
        # TODO: add the password check.
        # https://stackoverflow.com/questions/16709638/checking-the-strength-of-a-password-how-to-check-conditions
        
        # Update the username-to-user_id mapping.
        with self._rc.pipeline() as pipe:
            while True:
                try:
                    # Put a watch on the Hash 'users': username -> user-id, in cast that 
                    # multiple clients are registering with the same username.
                    pipe.watch(self.USERS_HASH_KEY)
                    username_exists = pipe.hexists(self.USERS_HASH_KEY, username)
                    if username_exists:
                        result['error'] = 'username {} already exists'.format(username)
                        return (False, result);
                    
                    # Get the next user-id. If the key "next_user_id" doesn't exist,
                    # it will be created and initialized as 0, and then incremented by 1.
                    user_id = pipe.incr(self.NEXT_USER_ID_KEY)
                    
                    # Set the username-to-user_id pair in USERS_HASH_KEY.
                    pipe.multi()
                    pipe.hset(self.USERS_HASH_KEY, username, user_id)
                    pipe.execute()
                    
                    break
                except WatchError:
                    continue
                
            # Generate the authentication secret.
            auth_secret = secrets.token_hex()
            user_id_profile_key = self.USER_ID_PROFILE_KEY_FORMAT.format(user_id)
            
            pipe.multi()
            # Update the authentication_secret-to-user_id mapping.
            pipe.hset(self.AUTHS_HASH_KEY, auth_secret, user_id)
            # Create the user profile.
            # TODO: Store the hashed password instead of the raw password.
            pipe.hmset(user_id_profile_key, 
                       {self.USER_ID_PROFILE_USERNAME_KEY: username, 
                        self.USER_ID_PROFILE_PASSWORD_KEY: password,
                        self.USER_ID_PROFILE_AUTH_KEY: auth_secret})
            pipe.execute()
        
        return (True, result)
            
    def change_password(self, auth_secret, old_password, new_password):
        result = {'error': None}
        
        # Check if the user is logged in.
        loggedin, user_id = self._is_loggedin(auth_secret)
        if not loggedin:
            result['error'] = 'Not logged in'
            return (False, result)
        
        # Check if the old password matches.
        user_id_profile_key = self.USER_ID_PROFILE_KEY_FORMAT.format(user_id)
        stored_password = self._rc.hget(user_id_profile_key, self.USER_ID_PROFILE_PASSWORD_KEY)
        if stored_password != old_password:
            result['error'] = 'Incorrect old password'
            return (False, result)
        
        # TODO: add the new password check.
        
        # Generate the new authentication secret.
        new_auth_secret = secrets.token_hex()
        
        # Replace the old password by the new one and the old authentication secret by the new one.
        with self._rc.pipeline() as pipe:
            pipe.multi()
            pipe.hset(user_id_profile_key, self.USER_ID_PROFILE_PASSWORD_KEY, new_password)
            pipe.hset(user_id_profile_key, self.USER_ID_PROFILE_AUTH_KEY, new_auth_secret)
            pipe.hset(self.AUTHS_HASH_KEY, new_auth_secret, user_id)
            pipe.hdel(self.AUTHS_HASH_KEY, auth_secret)
            pipe.execute()
        
        result[self.USER_ID_PROFILE_AUTH_KEY] = new_auth_secret
        return (True, result)
    
    def login(self, username, password):
        result = {'error': None}
        
        # Get the user-id based on the username.
        user_id = self._rc.hget(self.USERS_HASH_KEY, username)
        if user_id is None:
            result['error'] = "username {} doesn't exist".format(username)
            return (False, result)
        
        # Compare the input password with the stored one. If it matches, 
        # return the authentication secret.
        user_id_profile_key = self.USER_ID_PROFILE_KEY_FORMAT.format(user_id)
        stored_password = self._rc.hget(user_id_profile_key, self.USER_ID_PROFILE_PASSWORD_KEY)
        if password == stored_password:
            result[self.USER_ID_PROFILE_AUTH_KEY] = self._rc.hget(user_id_profile_key, self.USER_ID_PROFILE_AUTH_KEY)
            return (True, result)
        else:
            result['error'] = 'Incorrect password'
            return (False, result)
    
    def logout(self, auth_secret):
        result = {'error': None}
        
        # Check if the user is logged in.
        loggedin, user_id = self._is_loggedin(auth_secret)
        if not loggedin:
            result['error'] = 'Not logged in'
            return (False, result)
        
        # Generate the new authentication secret.
        new_auth_secret = secrets.token_hex()
        
        # Replace the old authentication secret by the new one.
        user_id_profile_key = self.USER_ID_PROFILE_KEY_FORMAT.format(user_id)
        with self._rc.pipeline() as pipe:
            pipe.multi()
            pipe.hset(user_id_profile_key, self.USER_ID_PROFILE_AUTH_KEY, new_auth_secret)
            pipe.hset(self.AUTHS_HASH_KEY, new_auth_secret, user_id)
            pipe.hdel(self.AUTHS_HASH_KEY, auth_secret)
            pipe.execute()
            
        result[self.USER_ID_PROFILE_USERNAME_KEY] = self._rc.hget(user_id_profile_key, self.USER_ID_PROFILE_USERNAME_KEY)
        return (True, result)
    
    def post_tweet(self, auth_secret, tweet):
        pass
    
    def following(self, auth_secret, followee_username):
        pass
    
    def get_followers(self, auth_secret):
        pass
    
    def get_timeline(self, auth_secret, max_cnt_tweets):
        pass