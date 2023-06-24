import requests
import logging
import io
from flask import Flask, render_template, request, make_response
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
import const as const

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('app.log')
formatter = logging.Formatter("%(asctime)s %(name)-20s %(levelname)-8s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

app = Flask(__name__)


def get_league_info(league_id):
    league_api_endpoint = const.BASE_URL + f"leagues-classic/{league_id}/standings/"

    response = requests.get(league_api_endpoint)
    if response.status_code == 200:
        data = response.json()
        teams_ids = {}

        for team in data['standings']['results']:
            team_id = team['entry']
            team_name = team['entry_name']
            teams_ids[team_id] = team_name
    else:
        logger.warning("[ERROR] Failed to get response.")
        return None

    logging.debug(teams_ids)
    return teams_ids


# get team total result for each round
def get_team_results(team_id):
    url = f"https://fantasy.premierleague.com/api/entry/{team_id}/history/"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        team_results = []

        for event in data['current']:
            event_id = event['event']
            total_points = event['total_points']
            team_results.append((event_id, total_points))

        return team_results
    else:
        logger.warning(f"Failed to retrieve team results for team ID: {team_id}")
        return None


def collect_team_results_by_each_round(teams):
    team_results_dict = {}

    for team_id, team_name in teams.items():
        team_results = get_team_results(team_id)

        if team_results is not None:
            team_results_dict[team_name] = team_results

    return team_results_dict


# build a plot based on data object (list of dicts)
def plot_team_results(data):
    fig = Figure(figsize=(10, 6))
    canvas = FigureCanvasAgg(fig)

    ax = fig.add_subplot(111)

    for team_name, round_points in data.items():
        rounds = [round_num for round_num, _ in round_points]
        points = [points for _, points in round_points]

        ax.plot(rounds, points, label=team_name)

    ax.set_title('Team Results')
    ax.set_xlabel('Round')
    ax.set_ylabel('Points')
    ax.legend()
    ax.grid(True)

    canvas.draw()

    # Save the figure as PNG
    image_stream = io.BytesIO()
    canvas.print_png(image_stream)

    return image_stream.getvalue()


@app.route('/', methods=['GET'])
def load_page():
    return render_template('home.html')


@app.route('/', methods=['POST'])
def home():
    league_id = request.form.get('league_id')
    logger.info(league_id)
    if league_id is None:
        return render_template('home.html')

    teams = get_league_info(league_id)
    logger.info(teams)
    if teams is None:
        return render_template('home.html', error="Failed to retrieve league information.")

    team_results_dict = collect_team_results_by_each_round(teams)

    # Generate the plot and get the PNG image data
    image_data = plot_team_results(team_results_dict)

    # Create a response with the PNG image
    response = make_response(image_data)
    response.headers['Content-Type'] = 'image/png'

    logger.debug("Image size: %s", len(image_data))
    return response


if __name__ == '__main__':
    logger.info("App started.")
    app.run(debug=True)
