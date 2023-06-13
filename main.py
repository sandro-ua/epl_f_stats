import requests

import const as const


def get_league_info(league_id):
    our_league_url = const.BASE_URL + f"leagues-classic/{league_id}/standings/"

    response = requests.get(our_league_url)
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


def main():
    league_id = 650483  # Replace with your league ID
    teams = get_league_info(league_id)

    if teams is not None:
        team_results_dict = collect_team_results_by_each_round(teams)

        for team_name, team_results in team_results_dict.items():
            print(f"Team: {team_name}")
            for event, total_points in team_results.items():
                print(f"Round {event}: {total_points} points")
            print()


if __name__ == '__main__':
    main()
