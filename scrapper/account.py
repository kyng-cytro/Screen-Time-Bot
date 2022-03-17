import requests
import re


# creates an account on next-episode.net
def create_account(user_id):
    with requests.Session() as s:
        detail = f'screen_{user_id}'
        url = "https://next-episode.net/PAGES/misc/signup.php"
        params = f"username={detail}&pass1={detail}&pass2={detail}&email={f'{detail}@screentime.com'}&tz=1&reason=join_next_ep_button&allow_contact=false"
        s.get(url=url, params=params)
        account_id, k_value = get_info(user_id)
    return account_id, k_value


# gets user_id and k_value from next-episode.net
def get_info(user_id):
    with requests.Session() as s:
        login_info = {
            "username": f'screen_{user_id}',
            "password": f'screen_{user_id}'
        }
        s.post("https://next-episode.net/userlogin", data=login_info)
        page = s.get("https://next-episode.net/userlogin")
        try:
            account_id = re.findall(r'user_id=(\d*)', page.text)[0]
            k_value = re.findall(r'k=(.{32})', page.text)[0]
        except:
            return None, None
    return account_id, k_value


# add or remove show from watchlist on next-episode.net
def toggle_watchlist(user, show_id):
    with requests.Session() as s:
        url = "https://next-episode.net/PAGES/misc/toggle_watchlist.inc.php"
        params = f"k={user['k_value']}&user_id={user['account_id']}&show_id={show_id}"
        s.get(url=url, params=params)
