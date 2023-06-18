import requests
import matplotlib.pyplot as plt

import const as const


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
        print("[ERROR] Failed to get response.")
        return None

    print(teams_ids)
    return teams_ids


def get_team_results(team_id):
    url = f"https://fantasy.premierleague.com/api/entry/{team_id}/history/"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        team_results = {}

        for event in data['current']:
            event_id = event['event']
            total_points = event['total_points']
            team_results[event_id] = total_points

        return team_results
    else:
        print(f"Failed to retrieve team results for team ID: {team_id}")
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
    plt.figure(figsize=(10, 6))  # Set the size of the plot

    for team_name, round_points in data.items():
        rounds = [round_num for round_num, _ in round_points]
        points = [points for _, points in round_points]

        plt.plot(rounds, points, label=team_name)  # Plot the line for each team

    plt.xlabel('Round')
    plt.ylabel('Points')
    plt.title('Team Results')
    plt.legend()  # Show the team names in the legend
    plt.grid(True)  # Add gridlines to the plot
    plt.show()


def main():
    league_id = 650483  # Replace with your league ID
    teams = get_league_info(league_id)

    if teams:
        team_results_dict = collect_team_results_by_each_round(teams)

        data = {}  # Data object to store team results

        for team_name, team_results in team_results_dict.items():
            round_points = [(round_num, points) for round_num, points in team_results.items()]
            data[team_name] = round_points
            #
            # print(f"Team: {team_name}")
            # for event, total_points in team_results.items():
            #     print(f"Round {event}: {total_points} points")
            # print()

        # Print the data object
        #print(data)

        #build a plot
        plot_team_results(data)


if __name__ == '__main__':
    main()
