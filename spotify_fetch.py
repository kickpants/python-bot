import requests
import base64
import json

api_url="https://accounts.spotify.com/api/token"

def get_auth_token(client_id, client_secret, api_url, refresh_token):
  response = requests.post(
    api_url,
    data = {
      "grant_type": "refresh_token",
      "refresh_token": refresh_token
    },
    auth = (client_id, client_secret)
  )

  return response.json()['access_token']

def get_playlist_items(token, url_string):
  start = url_string.find("playlist/") + len("playlist/")
  end = url_string.find("?")
  playlist_id = url_string[start:end]
  songList = []

  response = requests.get(
    f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?market=US",
    headers={
      "Authorization": "Bearer " + token
    }
  )
  
  for x in response.json()['items']:
    songList.append(x['track']['name'] + " " + x['track']['album']['artists'][0]['name'])

  for x in songList:
    print(f"{x}\n")

  return songList
