import requests
import logging
import io
import json
import os
import base64
from flask import Flask, render_template, request
from matplotlib.figure import Figure
import const as const

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.FileHandler(const.LOG_FILENAME)
formatter = logging.Formatter("%(asctime)s %(name)-20s %(levelname)-8s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

app = Flask(__name__)


# Create a directories to store leagues and teams data
def create_data_dirs(dirs):
    for dir in dirs:
        if not os.path.exists(dir):
            os.makedirs(dir)
            logger.info(f"Directory {dir} has been created.")


create_data_dirs(const.DIRS)


# Get league infomation, return teams that participate
def get_league_info(league_id):
    league_folder = os.path.join(const.DATA_LEAGUES, str(league_id))
    league_file_path = f'league_info_{league_id}.json'
    if os.path.exists(league_folder):
        # Read data from file
        with open(os.path.join(league_folder, league_file_path), 'r') as file:
            data = json.load(file)
    else:
        # Make API call
        league_api_endpoint = const.BASE_URL + f"leagues-classic/{league_id}/standings/"
        response = requests.get(league_api_endpoint)

        if response.status_code == 200:
            data = response.json()
            # Create league folder
            os.mkdir(league_folder)
            # Store data in file
            with open(os.path.join(league_folder, league_file_path), 'w') as file:
                json.dump(data, file)
                logger.info(f"File {league_file_path} has been created.")
        else:
            logger.warning("[ERROR] Failed to get response.")
            return None

    teams_ids = {}

    for team in data['standings']['results']:
        team_id = team['entry']
        team_name = team['entry_name']
        teams_ids[team_id] = team_name

    logging.info(teams_ids)
    return teams_ids


# Get team data from file or via API call
def get_team_data(team_id):
    team_folder = os.path.join(const.DATA_TEAMS, str(team_id))
    team_folder_path = f'team_results_{team_id}.json'

    if os.path.exists(team_folder):
        # Read data from file
        with open(os.path.join(team_folder, team_folder_path), 'r') as file:
            data = json.load(file)
    else:
        # Make API call
        url = f"{const.BASE_URL}entry/{team_id}/history/"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            # Create team folder
            os.mkdir(team_folder)
            # Store data in file
            with open(os.path.join(team_folder, team_folder_path), 'w') as file:
                json.dump(data, file)
                logger.info(f"File {team_folder_path} has been created.")
        else:
            logger.warning(f"Failed to retrieve team results for team ID: {team_id}")
            return None
    return data


# Get team result by each round
def get_team_results(data):
    team_results = []
    for event in data['current']:
        event_id = event['event']
        total_points = event['total_points']
        team_results.append((event_id, total_points))

    # Sort teams by total points in each round
    team_results.sort(key=lambda x: x[1], reverse=True)

    return team_results


# Get team cost by each round
def get_team_cost(data):
    team_cost = []
    for event in data['current']:
        event_id = event['event']
        value = event['value'] / 10
        team_cost.append((event_id, value))

    return team_cost


# Return total points per round
def collect_team_results_by_each_round(teams):
    team_results_dict = {}

    for team_id, team_name in teams.items():
        team_data = get_team_data(team_id)
        team_results = get_team_results(team_data)
        if team_results is not None:
            team_results_dict[team_name] = team_results

    return team_results_dict


# Return team place per each round
def collect_team_place_by_each_round(team_results_dict):
    round_places_dict = {}

    # Create a dictionary to store the place of each team in each round
    for team_name, team_results in team_results_dict.items():
        for round_num, points in team_results:
            if round_num not in round_places_dict:
                round_places_dict[round_num] = {}
            round_places_dict[round_num][team_name] = points

    # Sort the teams in each round based on their points and assign the place
    for round_num, team_points in round_places_dict.items():
        sorted_teams = sorted(team_points.items(), key=lambda x: x[1], reverse=True)
        places = {team[0]: i + 1 for i, team in enumerate(sorted_teams)}
        round_places_dict[round_num] = places

    return round_places_dict


# Return team cost by each round
def collect_team_cost_by_each_round(teams):
    team_cost_dict = {}

    for team_id, team_name in teams.items():
        team_data = get_team_data(team_id)
        team_cost = get_team_cost(team_data)
        if team_cost is not None:
            team_cost_dict[team_name] = team_cost
    return team_cost_dict


# build a plot 'Team Result' based on data object
def plot_team_results(data):
    fig = Figure(figsize=(const.PLOT_SIZE_X, const.PLOT_SIZE_Y))
    ax = fig.add_subplot(111)

    for team_name, round_points in data.items():
        rounds = [round_num for round_num, _ in round_points]
        points = [points for _, points in round_points]

        ax.plot(rounds, points, label=team_name)

    ax.set_title('Team Result')
    ax.set_xlabel('Round', fontsize=const.AXE_FONT_SIZE_X)
    ax.set_ylabel('Points', fontsize=const.AXE_FONT_SIZE_Y)
    ax.legend()
    ax.minorticks_on()
    fig.tight_layout()
    ax.grid(True)
    return fig


# build a plot 'Team Cost per round' based on data
def plot_team_cost(data):
    fig = Figure(figsize=(const.PLOT_SIZE_X, const.PLOT_SIZE_Y))
    ax = fig.add_subplot(111)

    for team_name, round_points in data.items():
        rounds = [round_num for round_num, _ in round_points]
        cost = [cost for _, cost in round_points]

        ax.plot(rounds, cost, label=team_name)

    ax.set_title('Team Cost per round')
    ax.set_xlabel('Round', fontsize=const.AXE_FONT_SIZE_X)
    ax.set_ylabel('Cost', fontsize=const.AXE_FONT_SIZE_Y)
    ax.legend()
    ax.minorticks_on()
    fig.tight_layout()
    ax.grid(True)

    return fig


# build a plot 'Team place per round' based on data
def plot_team_place(team_places_dict):
    fig = Figure(figsize=(const.PLOT_SIZE_X, const.PLOT_SIZE_Y))
    ax = fig.add_subplot(111)

    teams = team_places_dict[38].keys()  # Get the team names from any round (38 in this case)

    for team in teams:
        places = [team_places_dict[round_num][team] for round_num in sorted(team_places_dict.keys())]
        ax.plot(range(1, len(places) + 1), places, label=team, linewidth=2)

    ax.set_xlabel('Round', fontsize=const.AXE_FONT_SIZE_X)
    ax.set_ylabel('Place', fontsize=const.AXE_FONT_SIZE_Y)
    ax.invert_yaxis()
    ax.set_title('Team Places by Round')
    ax.legend(bbox_to_anchor=(1.15, 1), loc='upper right', borderaxespad=1)
    ax.minorticks_on()
    fig.tight_layout()

    ax.grid(True)

    return fig


# Gets data, build figure, returns png image
def process_plot(fig):
    # Create a response with the PNG image
    image_stream = io.BytesIO()
    fig.savefig(image_stream, format='png')
    image_stream.seek(0)
    return base64.b64encode(image_stream.getvalue()).decode()


@app.route('/', methods=['GET'])
def load_page():
    return render_template(const.HOME_HTML)


@app.route('/', methods=['POST'])
def home():
    league_id = request.form.get('league_id')
    logger.info(league_id)

    if league_id is None:
        return render_template(const.HOME_HTML)

    teams = get_league_info(league_id)
    logger.info(teams)
    if teams is None:
        return render_template(const.HOME_HTML, error="Failed to retrieve league information.")

    # Build Plot #1
    team_results_dict = collect_team_results_by_each_round(teams)
    fig_1 = plot_team_results(team_results_dict)
    plot_image_1 = process_plot(fig_1)

    # Build plot #2
    team_cost = collect_team_cost_by_each_round(teams)
    fig_2 = plot_team_cost(team_cost)
    plot_image_2 = process_plot(fig_2)

    # Build plot #3
    places = collect_team_place_by_each_round(team_results_dict)
    fig_3 = plot_team_place(places)
    plot_image_3 = process_plot(fig_3)

    # Render html page
    return render_template(const.HOME_HTML, plot_image_1=plot_image_1, plot_image_2=plot_image_2,
                           plot_image_3=plot_image_3)


if __name__ == '__main__':
    logger.info("App started.")
    app.run(debug=False)