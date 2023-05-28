import bs4
import requests
import time
import random as ran
import sys
import pandas as pd

import dash
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
from urllib.parse import quote


def scrape_movie_block(movie_block):
    movie_data = {}

    try:
        movie_data['name'] = movie_block.find('a').get_text()  # Name of the movie
    except:
        movie_data['name'] = None

    try:
        movie_data['year'] = str(movie_block.find('span', {'class': 'lister-item-year'}).contents[0][1:-1])  # Release year
    except:
        movie_data['year'] = None

    try:
        movie_data['rating'] = float(movie_block.find('div', {'class': 'inline-block ratings-imdb-rating'}).get('data-value'))  # Rating
    except:
        movie_data['rating'] = None

    try:
        movie_data['m_score'] = float(movie_block.find('span', {'class': 'metascore favorable'}).contents[0].strip())  # Metascore
    except:
        movie_data['m_score'] = None

    try:
        movie_data['votes'] = int(movie_block.find('span', {'name': 'nv'}).get('data-value'))  # Votes
    except:
        movie_data['votes'] = None

    return movie_data


def scrape_movie_page(movie_blocks):
    page_movie_data = []
    num_blocks = len(movie_blocks)

    for block in range(num_blocks):
        page_movie_data.append(scrape_movie_block(movie_blocks[block]))

    return page_movie_data


def scrape_movies(link, target_count):
    base_url = link
    current_movie_count_start = 0
    current_movie_count_end = 0
    remaining_movie_count = target_count - current_movie_count_end
    new_page_number = 1
    movie_data = []

    while remaining_movie_count > 0:
        url = base_url + str(new_page_number)
        source = requests.get(url).text
        soup = bs4.BeautifulSoup(source, 'html.parser')
        movie_blocks = soup.findAll('div', {'class': 'lister-item-content'})
        movie_data.extend(scrape_movie_page(movie_blocks))
        current_movie_count_start = int(soup.find("div", {"class": "nav"}).find("div", {"class": "desc"}).contents[1].get_text().split("-")[0])
        current_movie_count_end = int(soup.find("div", {"class": "nav"}).find("div", {"class": "desc"}).contents[1].get_text().split("-")[1].split(" ")[0])
        remaining_movie_count = target_count - current_movie_count_end
        print('\r' + "Currently scraping movies from: " + str(current_movie_count_start) + " - " + str(current_movie_count_end), "| Remaining count: " + str(remaining_movie_count), flush=True, end="")
        new_page_number = current_movie_count_end + 1
        time.sleep(ran.randint(0, 10))

    return movie_data


base_url = "https://www.imdb.com/search/title/?title_type=feature&num_votes=25000,&sort=user_rating,desc&start="

app = Dash(__name__)

# Scrape movies based on user input
@app.callback(
    Output("movie-data", "data"),
    [Input("scrape-button", "n_clicks")],
    prevent_initial_call=True
)
def update_movie_data(n_clicks):
    target_count = 100
    movie_data = scrape_movies(base_url, target_count)
    df = pd.DataFrame(movie_data)
    return df.to_json()


app.layout = html.Div(
    children=[
        html.H1("Top Rated Movies Dashboard"),
        dcc.Graph(id="movie-rating-graph"),
        dcc.Graph(id="movies-per-year-graph"),
        dcc.Graph(id="votes-scatter-graph"),
        dcc.Graph(id="m-score-scatter-graph"),
        html.Div(id="selected-movie-output")
    ]
)


@app.callback(
    Output("movie-rating-graph", "figure"),
    [Input("movie-data", "data")]
)
def update_movie_rating_graph(data):
    df = pd.read_json(data)
    figure = {
        "data": [
            {
                "x": df["name"],
                "y": df["rating"],
                "type": "bar",
                "marker": {"color": "purple"}  # Set the color of the bars to purple
            },
        ],
        "layout": {
            "title": "Top Rated Movies",
            "xaxis": {"title": "Movie"},
            "yaxis": {"title": "Rating"},
            "plot_bgcolor": "rgba(0,0,0,0)"  # Set the plot background color to transparent
        },
    }
    return figure


@app.callback(
    Output("movies-per-year-graph", "figure"),
    [Input("movie-data", "data")]
)
def update_movies_per_year_graph(data):
    df = pd.read_json(data)
    movies_per_year = df['year'].value_counts().sort_index()
    figure = {
        "data": [
            {
                "x": movies_per_year.index,
                "y": movies_per_year.values,
                "type": "bar",
                "marker": {"color": "blue"}  # Set the color of the bars to blue
            },
        ],
        "layout": {
            "title": "Number of Movies per Year",
            "xaxis": {"title": "Year"},
            "yaxis": {"title": "Count"},
            "plot_bgcolor": "rgba(0,0,0,0)"  # Set the plot background color to transparent
        },
    }
    return figure


@app.callback(
    Output("votes-scatter-graph", "figure"),
    [Input("movie-data", "data")]
)
def update_votes_scatter_graph(data):
    df = pd.read_json(data)
    figure = {
        "data": [
            {
                "x": df["rating"],
                "y": df["votes"],
                "mode": "markers",
                "marker": {
                    "size": 8,
                    "color": "red"  # Set the color of the scatter markers to red
                },
                "type": "scatter"
            }
        ],
        "layout": {
            "title": "Movie Votes vs. Rating",
            "xaxis": {"title": "Rating"},
            "yaxis": {"title": "Votes"},
            "plot_bgcolor": "rgba(0,0,0,0)"  # Set the plot background color to transparent
        }
    }
    return figure


@app.callback(
    Output("m-score-scatter-graph", "figure"),
    [Input("movie-data", "data")]
)
def update_m_score_scatter_graph(data):
    df = pd.read_json(data)
    figure = {
        "data": [
            {
                "x": df["rating"],
                "y": df["m_score"],
                "mode": "markers",
                "marker": {
                    "size": 8,
                    "color": "green"  # Set the color of the scatter markers to green
                },
                "type": "scatter"
            }
        ],
        "layout": {
            "title": "Movie Metascore vs. Rating",
            "xaxis": {"title": "Rating"},
            "yaxis": {"title": "Metascore"},
            "plot_bgcolor": "rgba(0,0,0,0)"  # Set the plot background color to transparent
        }
    }
    return figure


@app.callback(
    Output("selected-movie-output", "children"),
    [Input("movie-rating-graph", "clickData")]
)
def update_selected_movie_output(click_data):
    if click_data is not None:
        movie_name = click_data['points'][0]['x']
        return f"The selected movie is: {movie_name}"
    else:
        return ""


if __name__ == "__main__":
    app.run_server(debug=True)
