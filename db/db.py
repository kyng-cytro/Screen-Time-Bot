from http import client
from pymongo import MongoClient
from datetime import datetime
import os

client = MongoClient(
    os.getenv('pharse')
)

db = client.screen_time_db


# gets user info
def get_user(id):
    users = db.users
    return users.find_one({"user_id": id})


# get all user with custom sub
def get_shows_users():
    users = db.users
    return users.find({"series_sub": True})


# creates new user
def add_user(name, id):
    users = db.users
    users.insert_one({"name": name,
                      "user_id": id,
                     "create_date": datetime.now(),
                      "modified_date": datetime.now(),
                      "series_sub": False,
                      "custom": False,
                      "custom_username": "",
                      "custom_password": "",
                      "account_id": "",
                      "k_value": "",
                      }
                     )


# subscribes user to TV-Show updates
def subscribe(id, type, username="", password="", account_id="", k_value=""):
    users = db.users
    if type == 0:
        users.update_one(
            {"user_id": id},
            {"$set": {"series_sub": True,
             "modified_date": datetime.now()
                      }
             }
        )

    else:
        users.update_one(
            {"user_id": id},
            {"$set":
                {"series_sub": True,
                 "custom": True,
                 "custom_username": username,
                 "custom_password": password,
                 "account_id": account_id,
                 "k_value": k_value,
                 "modified_date": datetime.now()
                 }
             }
        )


# unsubscribes user from TV-Show updates
def unsubscribe(id):
    users = db.users
    users.update_one(
        {"user_id": id},
        {"$set":
            {"series_sub": False,
             "custom": False,
             "modified_date": datetime.now()
             }
         }
    )


# gets user from redunant(backup) collection
def get_account(id):
    accounts = db.accounts
    return accounts.find_one({"username": f'screen_{id}'})


# add user to redunant(backup) collection
def add_account(id, account_id, k_value):
    accounts = db.accounts
    accounts.insert_one({
        "username": f'screen_{id}',
        "password": f'screen_{id}',
        "account_id": account_id,
        "k_value": k_value
    })


# get list of shows user is following
def get_following(user_id):
    users = db.users
    user = users.find_one({"user_id": user_id})
    try:
        return user['following']
    except KeyError:
        return []


# add show to users followings list
def add_following(user_id, show_id, show_name):
    users = db.users
    users.update_one(
        {"user_id": user_id},
        {
            "$addToSet": {
                "following": {"show_id": show_id, "show_name": show_name}
            }
        }
    )


# remove show from users followings list
def remove_following(user_id, show_id):
    users = db.users
    users.update_one(
        {"user_id": user_id},
        {
            "$pull": {
                "following": {"show_id": show_id}
            }
        }
    )


# check  if user following a particular show
def check_following(user_id, show_id):
    users = db.users
    user = users.find_one({"user_id": user_id})
    try:
        shows = user['following']
    except KeyError:
        return False
    for show in shows:
        if show['show_id'] == show_id:
            return True
    return False


# stores movies in db
def store_movies(data):
    movies = db.movies
    movies.delete_many({})
    movies.insert_many(data)


# get all movies in db
def get_movies_db():
    movies = db.movies
    data = list(movies.find())
    if not data:
        return []
    return data


# stores shows in db
def store_shows(data):
    shows = db.shows
    shows.delete_many({})
    shows.insert_many(data)


# get all shows in db
def get_shows_db():
    shows = db.shows
    data = list(shows.find())
    if not data:
        return []
    return data
