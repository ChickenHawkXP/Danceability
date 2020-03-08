import json
import requests
import base64
from urllib.parse import urlencode
import webbrowser
import sys
from flask import *

client = "b079374e3fdf4691a81109a7b2d94048"
secret = "3a7d0a4ecb67452693c42835df2235dd"

app = Flask(__name__)
code = ''
access_token = ""
provider_url = "https://accounts.spotify.com/authorize"

params = urlencode({
    'client_id': '%s'%client,
    'scope': 'user-top-read',
    'redirect_uri': 'http://127.0.0.1:5000/',
    'response_type': 'code'
})
urlx = provider_url + '?' + params
webbrowser.open(urlx)

@app.route("/")
def spotify_callback():
    #Flask function that get called when website is called
    global code
    global access_token
    rurl = str(request.url) # Some jank way to get the code ????
    scode = rurl.find("=")
    code = rurl[scode+1::]
    access_token = get_access_token()
    main()
    return "Thank you very much!"

def get_access_token():
    # Use code to retrieve access code from Spotify API
    codes = client+":"+secret
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
    return response.json()['access_token'] #Return access code

def get_user_artists(token):
    # Obtain user's (who confirmed website) top artists
    headers = {
    'Authorization': 'Bearer %s'%token,
    }
    response = requests.get('https://api.spotify.com/v1/me/top/artists', headers=headers)
    return response.json()

def get_user_tracks(token):
    # Precondition: A unique string access code, passed by Spotify endpoint
    # Obtain user's (who confirmed website) top tracks
    headers = {
    'Authorization': 'Bearer %s'%token,
    }
    response = requests.get('https://api.spotify.com/v1/me/top/tracks', headers=headers)
    return response.json()

def get_playlist(token,playlistid):
    headers = {
    'Authorization': 'Bearer %s'%token,
    }
    response = requests.get('https://api.spotify.com/v1/playlists/%s'%playlistid, headers=headers)
    return response.json()

def get_analysis(token,id):
    # Precondition: A unique string access code, passed by Spotify endpoint and a unqiue string belonging to each spotify track
    # Obtain Spotify's track analysis (Danceability mainly)
    headers = {
    'Authorization': 'Bearer %s'%token,
    }
    response = requests.get('https://api.spotify.com/v1/audio-features/%s'%id,headers=headers)
    return response.json()

def get_recommendations(token):
    headers = {
    'Authorization': 'Bearer %s'%token,
    }
    genres = 'guitar'
    dance = input('Enter your target dancibility: ')
    instrumental = input('Enter your target instrumentalness: ')
    response = requests.get('https://api.spotify.com/v1/recommendations?seed_genres=%s&target_danceability=%s&target_instrumentalness=%s'%(genres,dance,instrumental),headers=headers)
    return response.json()

def search_track(token):
    # Precondition: A unique string access code, passed by Spotify endpoint
    q = input("\nEnter a song name: ")
    if q == '-x-':
        return False
    q = q.replace(" ","%20")
    headers = {
    'Authorization': 'Bearer %s'%token,
    }
    response = requests.get('https://api.spotify.com/v1/search?q=%s&type=track'%q,headers=headers)
    for i in response.json()['tracks']['items']:
        id = i['id']
        for j in i['album']['artists']:
            dance = get_analysis(access_token,id)
            print(j['name'],"-",i['name'],"-",dance['danceability'],"- %.2f"%((i['duration_ms']/1000)/60),'mins')
    return True

def search_artist(token):
    q = input("\nEnter an artists name: ")
    if q == '-x-':
        return False
    q = q.replace(" ","%20")
    headers = {
    'Authorization': 'Bearer %s'%token,
    }
    response = requests.get('https://api.spotify.com/v1/search?q=%s&type=artist'%q,headers=headers)
    for i in response.json()['artists']['items']:
        print(i['name'],"-",i['followers']['total'],"followers -",i['genres'])
    return response.json()

def get_artist(token):
    q = input("\nEnter an artists name: ")
    if q == '-x-':
        return False
    q = q.replace(" ","%20")
    headers = {
    'Authorization': 'Bearer %s'%token,
    }
    response = requests.get('https://api.spotify.com/v1/search?q=%s&type=artist'%q,headers=headers)
    return response.json()

def main():
    headers = {
    'Authorization': 'Bearer %s'%access_token,
    }
    artists = get_user_artists(access_token)
    tracks = get_user_tracks(access_token)

    with open ("spotifylist.txt","w") as spotifyartists:
        spotifyartists.write("Top Artists:\tPopularity:\n")
        for artist in artists['items']:
            spotifyartists.write(artist['name']+'\t\t'+str(artist["popularity"])+"\n")

    with open ('spotifytracks.txt','w') as spotifytracks:
        spotifytracks.write("Top Songs:\tDanceability\n")
        for track in tracks['items']:
            ids = track['id']  
            dance = get_analysis(access_token,ids)
            name = track['name'].encode(sys.stdout.encoding, errors='replace') # Encode random symbols in certain song title
            new_name = str(name).replace('\\xe2\\x97\\x90','').replace('\\xe2\\x97\\x91','') # Replace the unknown characters with nothing
            spotifytracks.write(str(new_name).strip('b').strip('\'').strip('"')+'\t%f\n'%dance['danceability'])
    
    choice = 0
    while(choice != '5'):
        print("\n[1] Search by Track\n[2] Search by Artist\n[3] Get Playlist\n[4] Get Recommendations\n[5] Quit")
        choice = input("What would you like to do?: ")
        flag = True
        if choice == '1':
            while flag:
                print("Enter '-x-' to exit")
                flag = search_track(access_token)
        if choice == '2':
            while flag:
                print("Enter '-x-' to exit")
                flag = search_artist(access_token)
        if choice == '3':
            avg_dance = 0.0
            avg_count = 0
            playlist_id = input("Input the playlist uri: ")
            playlist_tracks = get_playlist(access_token,playlist_id[17::])
            next_call = playlist_tracks['tracks']['next']
            for i in playlist_tracks['tracks']['items']:
                ids = i['track']['id']
                dance = get_analysis(access_token,ids)
                avg_dance += float(dance['danceability'])
                avg_count += 1
                print(i['track']['name'],"-",dance['danceability']) 
            
            total_songs = playlist_tracks['tracks']['total']
            if next_call != None: #Gets next page of playlist, limit at 200
                next_page = requests.get(next_call,headers=headers)
                for i in next_page.json()['items']:
                    ids = i['track']['id']
                    dance = get_analysis(access_token,ids)
                    avg_dance += float(dance['danceability'])
                    avg_count += 1
                    print(i['track']['name'],"-",dance['danceability'])
            
            print('Total: %s songs'%total_songs)
            print("Danceability average of this playlist: %.2f"%(avg_dance/avg_count))
        if choice == '4':
            recommendations = get_recommendations(access_token)
            for i in recommendations['tracks']:
                ids = i['id']
                for j in i['artists']:
                    artist = j['name']
                    break
                dance = get_analysis(access_token,ids)
                print(artist,"-",i['name'],'-',dance['danceability'])
