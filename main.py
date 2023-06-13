import requests

import const as const

if __name__ == '__main__':
    our_league_url = const.BASE_URL + "leagues-classic/650483/standings/"

    response = requests.get(our_league_url)
    if response.status_code == 200:
        data = response.json()

        teams = {}

        for team in data['standings']['results']:
            team_id = team['entry']
            team_name = team['entry_name']
            teams[team_id] = team_name

        print(teams)

    else:
        print("[ERROR] Failed to get response.")

