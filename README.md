# pytwis

A twitter-clone backend using Python and Redis.

Note that **this package requires Python 3.6 and later** since it depends on Python 3.6 built-in module [`secrets`](https://docs.python.org/3/library/secrets.html).

To get the help information,

```bash
$ ./pytwis_clt.py -h
```

## 1. Connect to the twitter clone.

(1) Connect to the local Redis server at the default port 6379 with no password.

```bash
$ ./pytwis_clt.py 
```

(2) Connect to a remote Redis server with IP = xxx.xxx.xxx.xxx at port yyyy with password zzzzzz.

```bash
$ ./pytwis_clt.py -d xxx.xxx.xxx.xxx -t yyyy -p zzzzzz
```

## 2. Online commands after successfully connecting to the twitter clone.

Note that the following commands have to be executed after a successful log-in.

* logout
* changepassword
* follow
* unfollow
* followers
* followings
* post

(1) Register a new user xxxxxx with password yyyyyy.

```bash
> register xxxxxx yyyyyy
```

(2) Log into a user xxxxxxx with password yyyyyy.

```bash
> login xxxxxx yyyyyy
```

(3) Log out.

```bash
> logout
```

(4) Change the password. Assume that the old password is yyyyyy and the new password is zzzzzz.

```bash
> changepassword yyyyyy zzzzzz zzzzzz
```

(5) Follow a user xxxxxx.

```bash
> follow xxxxxx
```

(6) Unfollow a user.

```bash
> unfollow xxxxxx
```

(7) Get the follower list of a user.

```bash
> followers
```

(8) Get the following list of a user.

```bash
> followings
```

(9) Post a tweet

```bash
> post tweet
```

(10) Get the general/user timeline.

```bash
> timeline [max-tweet-count]
```

It will return the user timeline if a user is logged in and will return the general timeline otherwise. Also, it will return all the tweets in the timeline if max-tweet-count is not specified.

(11) Exit the console program.

```bash
> exit
```

or 

```bash
> quit
```

## 3. Unit test.

To run the unit test,

```bash
$ python3 pytwis_test.py
```

or 

```bash
$ ./pytwis_test.py
```