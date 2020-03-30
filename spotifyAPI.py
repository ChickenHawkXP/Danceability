import base64
import requests
from urllib.parse import urlencode
class spotify_api():
    def __init__(self,client,secret):
        self.client = client
        self.secret = secret
        self.token = None
        self.headers = None

    def get_url(self):
        provider_url = "https://accounts.spotify.com/authorize"
        params = urlencode({
            'client_id': '%s'%self.client,
            'scope': 'user-top-read',
            'redirect_uri': 'http://127.0.0.1:5000/',
            'response_type': 'code'
        })
        urlx = provider_url + '?' + params
        return urlx

    def get_access_token(self,code):
        # Use code to retrieve access code from Spotify API
        codes = self.client+":"+self.secret
        encode = codes.encode('ascii')
        head = base64.b64encode(encode) # Client and secret codes need to be base64 encoded and passed to API

        headers = {
        'Authorization': 'Basic %s'%head.decode('ascii'),
        }   

        data = {
        'grant_type': 'authorization_code',
        'code': '%s'%code,
        'redirect_uri': 'http://127.0.0.1:5000/'
        }
        
        response = requests.post('https://accounts.spotify.com/api/token', headers=headers, data=data)
        try:
            response.json()['access_token']
        except:
            print(response.json())
            quit()
        self.token = response.json()['access_token']
        self.headers = {
        'Authorization': 'Bearer %s'%self.token,
            }
        return response.json()['access_token'] #Return access code

    def get_user_artists(self):
        # Obtain user's (who confirmed website) top artists
        response = requests.get('https://api.spotify.com/v1/me/top/artists', headers=self.headers)
        return response.json()

    def get_user_tracks(self):
        # Precondition: A unique string access code, passed by Spotify endpoint
        # Obtain user's (who confirmed website) top tracks
        response = requests.get('https://api.spotify.com/v1/me/top/tracks', headers=self.headers)
        return response.json()

    def get_analysis(self,ids):
        # Precondition: A unique string access code, passed by Spotify endpoint and a unqiue string belonging to each spotify track
        # Obtain Spotify's track analysis (Danceability mainly)
        csv = ""
        for i in ids:
            csv += i+","
        csv = csv.strip(",")
        response = requests.get('https://api.spotify.com/v1/audio-features/?ids=%s'%csv,headers=self.headers)
        return response.json()
