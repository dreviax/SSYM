import os
import tempfile
import re
from sclib import SoundcloudAPI, Track, Playlist
import subprocess
import shutil
from yandex_music import Client
from urllib.parse import urlparse

# SORT FILENAME
def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)

# SOUNDCLOUD FUNC
def download_soundcloud_url(url):
    api = SoundcloudAPI()
    resource = api.resolve(url)

    if isinstance(resource, Track):
        filename = f"{sanitize_filename(resource.artist)} - {sanitize_filename(resource.title)}.mp3"
        with open(filename, 'wb+') as file:
            resource.write_mp3_to(file)
        return [filename]  # Возвращаем список с одним файлом

    elif isinstance(resource, Playlist):
        temp_dir = tempfile.mkdtemp(prefix=f"soundcloud_{sanitize_filename(resource.title)}_")
        file_paths = []
        
        for track in resource.tracks:
            filename = f"{sanitize_filename(track.artist)} - {sanitize_filename(track.title)}.mp3"
            filepath = os.path.join(temp_dir, filename)
            with open(filepath, 'wb+') as file:
                track.write_mp3_to(file)
            file_paths.append(filepath)
            
        return file_paths

    else:
        return False

# SPOTIFY FUNC
def download_spotify_url(url):
    # Создаем временную директорию с именем плейлиста
    temp_dir = tempfile.mkdtemp(prefix="spotify_playlist_")
    
    try:
        subprocess.run(
            ['spotdl', url, '--output', temp_dir],
            check=True)
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при загрузке: {e}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return False

    file_paths = [
        os.path.join(temp_dir, f) for f in os.listdir(temp_dir)
        if f.lower().endswith('.mp3')
    ]

    if not file_paths:
        print("Не удалось найти загруженные файлы.")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return False
        
    return file_paths

# YANDEX MUSIC FUNC
def download_yandex_music_url(url):
    try:
        client = Client("YOUR CLIENT ID").init()
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')

        if 'track' in path_parts:
            track_id = path_parts[-1]
            track = client.tracks([track_id])[0]
            filename = f"{sanitize_filename(track.artists[0].name)} - {sanitize_filename(track.title)}.mp3"
            with open(filename, 'wb') as f:
                f.write(track.download_bytes())
            return [filename]

        elif 'album' in path_parts:
            album_id = path_parts[-1]
            album = client.albums_with_tracks(album_id)
            temp_dir = tempfile.mkdtemp(prefix=f"yandex_album_{sanitize_filename(album.title)}_")
            file_paths = []
            
            for volume in album.volumes:
                for track in volume:
                    try:
                        filename = f"{sanitize_filename(track.artists[0].name)} - {sanitize_filename(track.title)}.mp3"
                        filepath = os.path.join(temp_dir, filename)
                        with open(filepath, 'wb') as f:
                            f.write(track.download_bytes())
                        file_paths.append(filepath)
                    except Exception as e:
                        print(f"Ошибка загрузки трека {track.title}: {e}")
                        continue
                        
            return file_paths if file_paths else False

        elif 'users' in path_parts and 'playlists' in path_parts:
            try:
                user_index = path_parts.index('users') + 1
                playlist_index = path_parts.index('playlists') + 1
                user_id = path_parts[user_index]
                playlist_id = path_parts[playlist_index]
                
                playlist = client.users_playlists(user_id, playlist_id)
                if not playlist:
                    raise Exception("Плейлист не найден или недоступен")
                
                temp_dir = tempfile.mkdtemp(prefix=f"yandex_playlist_{sanitize_filename(playlist.title)}_")
                file_paths = []
                
                for track_short in playlist.tracks:
                    try:
                        track = track_short.track
                        filename = f"{sanitize_filename(track.artists[0].name)} - {sanitize_filename(track.title)}.mp3"
                        filepath = os.path.join(temp_dir, filename)
                        with open(filepath, 'wb') as f:
                            f.write(track.download_bytes())
                        file_paths.append(filepath)
                    except Exception as e:
                        print(f"Ошибка загрузки трека {track.title if hasattr(track, 'title') else 'unknown'}: {e}")
                        continue
                        
                return file_paths if file_paths else False

            except Exception as e:
                print(f"Ошибка загрузки плейлиста: {e}")
                return False

        else:
            return False

    except Exception as e:
        print(f"Общая ошибка Яндекс.Музыки: {e}")
        return False