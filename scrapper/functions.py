import requests
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import InputMediaPhoto


# scrapes and return tv shows
def search_show(show):
    results = []
    with requests.Session() as s:
        url = "https://next-episode.net/search/"
        params = f"name={show}"
        page = s.get(url=url, params=params, allow_redirects=False)
        html = BeautifulSoup(page.text, "html.parser")
        items = html.findAll("div", {"class": "item"})
        if not items:
            return []

        items = items[:3] if(len(items) > 3) else items

        for item in items:
            header = item.find("span", {"class": "headlinehref"})
            if not header:
                continue
            try:
                show_id = header.find("a").get("id").split('_')[1]
                show_image = header.find("img").get(
                    "src").replace("//", "https://")
                show_link = header.find("a").get("href").replace(
                    "/", "https://next-episode.net/")

                show_name = header.find("a").text

                summary = item.find(
                    "div", {"class": "summary"}).text.replace('\n', '')

                show_summary = summary[:200] + \
                    "..." if (len(summary) > 200) else summary

            except:
                continue

            data = {
                "show_id": show_id,
                "image": show_image,
                "link": show_link,
                "name": show_name,
                "summary": show_summary
            }
            results.append(data)

    return results


# scrapes and returns user followings
def get_shows(username="", password=""):

    with requests.Session() as s:

        if username != "" and password != "":

            login_info = {
                'username': username,
                'password':  password
            }

            s.post("https://next-episode.net/userlogin", data=login_info)

        page = s.get("https://next-episode.net/calendar/")

        html = BeautifulSoup(page.text, "html.parser")

        todays_list = html.find("td", {"class": "highlighteddayboxes2"})

        Series = []

        Names = todays_list.find_all("a")

        for name in Names:

            if not name.get('title'):
                continue

            series_name = name.get('title')

            series_link = name.get('href').replace("//", "https://")

            content = s.get(series_link)

            content_html = BeautifulSoup(content.text, "html.parser")

            series_image = content_html.find("img", {"id": "big_image"}).get(
                'src').replace("//", "https://")

            series_summary = content_html.find(
                "div", {"id": "summary"}).text.strip()

            data = {

                "link": series_link,

                "image": series_image,

                "name": series_name,

                "summary": ((series_summary[:150] + '..') if len(series_summary) > 150 else series_summary),

                "date": f"{datetime.now().strftime('%B')} {datetime.now().day}, {datetime.now().year}"

            }

            Series.append(data)

    return Series


# scrapes and returns latest movies
def get_movies():

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
    }

    with requests.Session() as s:
        movies = []
        url = "https://www.metacritic.com/browse/movies/release-date/theaters/date?view=detailed&ttype=1"
        page = s.get(url, headers=headers)
        html = BeautifulSoup(page.text, "html.parser")
        trs = html.find_all("tr")
        movie_soups = []
        for tr in trs:
            if not tr.get("class"):
                movie_soups.append(tr)

        for soup in movie_soups:
            link = soup.find('a').get('href')
            movie_link = f"https://www.metacritic.com{link}"
            movie_image = soup.find("img").get("src")
            movie_title = soup.find("h3").text
            movie_date = soup.find("span").text
            movie_summary = soup.find("div", {"class": "summary"}).text.strip()
            movie_summary = movie_summary[:200] + \
                "..." if(len(movie_summary) > 200) else movie_summary
            movie = {
                "movie_link": movie_link,
                "movie_image": movie_image,
                "movie_title": movie_title,
                "movie_date": movie_date,
                "movie_summary": movie_summary
            }
            movies.append(movie)

    return movies


# helps split list into chunks
def chunkalize(data):
    if len(data) <= 4:
        chunks = [data[x:x+2] for x in range(0, len(data), 2)]

    elif len(data) <= 9:
        chunks = [data[x:x+3] for x in range(0, len(data), 3)]

    else:
        chunks = [data[x:x+4] for x in range(0, len(data), 4)]

    return chunks


# constructs caption for shows
def create_shows_caption(chunk):
    caption = ""
    for show in chunk:
        caption = caption + \
            f"\n\n*{show['name']}*\n{show['summary']}\n_{show['date']}_\n[👀 Read More]({show['link']})"

    return caption


# constructs caption for movies
def create_movie_caption(chunk):
    caption = ""
    for movie in chunk:
        caption = caption + \
            f"\n\n*{movie['movie_title']}*\n{movie['movie_summary']}\n_{movie['movie_date']}_\n[👀 Read More]({movie['movie_link']})"

    return caption


# create group of shows using caption
def create_media_group_shows(chunk, caption):
    media_group = []
    for id, show in enumerate(chunk):
        media_group.append(
            InputMediaPhoto(
                show['image'],
                caption=caption if(id == 0) else '', parse_mode="Markdown"
            )
        )
    return media_group


# create group of movies using caption
def create_media_group_movies(chunk, caption):
    media_group = []
    for id, movie in enumerate(chunk):
        media_group.append(
            InputMediaPhoto(
                movie['movie_image'],
                caption=caption if(id == 0) else '', parse_mode="Markdown"
            )
        )
    return media_group
