import json
import requests
import base64
import pandas as pd
from urllib.parse import urlencode
import webbrowser
import sys
import spotifyAPI as API
from flask import *
from parseJSON import parse_json as parser

client = ""
secret = ""

spotify = API.spotify_api(client,secret)
app = Flask(__name__)
code = ''
access_token = ""
provider_url = "https://accounts.spotify.com/authorize"

urlx = spotify.get_url()
webbrowser.open(urlx)

@app.route("/")
def spotify_callback():
    #Flask function that get called when website is called
    global code
    global access_token
    rurl = str(request.url) # Some jank way to get the code ????
    scode = rurl.find("=")
    code = rurl[scode+1::]
    access = spotify.get_access_token(code)
    main()
    return "Thank you very much!"

def get_playlist(token,playlistid):
    headers = {
    'Authorization': 'Bearer %s'%token,
    }
    response = requests.get('https://api.spotify.com/v1/playlists/%s'%playlistid, headers=headers)
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
    artist_name = []
    song_name = []
    dancibility = []
    song_duration = []
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
            artist_name.append(j['name'])
            song_name.append(i['name'])
            dancibility.append(dance['danceability'])
            mins = i['duration_ms']/1000/60
            song_duration.append(mins)
            #print(j['name'],"-",i['name'],"-",dance['danceability'],"- %.2f"%((i['duration_ms']/1000)/60),'mins')
    tracks = pd.DataFrame({'Artist':artist_name,
                           'Song Name':song_name,
                           'Dancibility':dancibility,
                           'Duration':song_duration})
    print(tracks)
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
    
    write_to_txt()

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

def write_to_txt(): 

    track_name = []

    artists = spotify.get_user_artists()
    tracks = spotify.get_user_tracks()

    with open ("spotifylist.txt","w") as spotifyartists:
        artist_name = parser.extract_values(artists,'name')
        artist_popularity = parser.extract_values(artists,'popularity')

        top_artists = pd.DataFrame({"Top Artists:":artist_name,         # Use panda's to organize data better
                                    "Popularity":artist_popularity})  
        spotifyartists.write(top_artists.to_string())

    with open ('spotifytracks.txt','w') as spotifytracks:
        for track in tracks['items']:
            name = track['name'].encode(sys.stdout.encoding, errors='replace') # Encode random symbols in certain song title
            new_name = str(name).replace('\\xe2\\x97\\x90','').replace('\\xe2\\x97\\x91','') # Replace the unknown characters with nothing
            track_name.append(str(new_name).strip('b').strip('\'').strip('"'))

        track_ids = parser.extract_values(tracks,'id')
        dance = spotify.get_analysis(track_ids)
        danceability = parser.extract_values(dance,'danceability')

        track_list = pd.DataFrame({"Track Name":track_name,
                                       "Danceability:":danceability})

        spotifytracks.write(track_list.to_string())