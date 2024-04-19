#"X-RapidAPI-Key": "78ccddaa7fmsh8fb20c7a86be36cp131949jsn72d75057e3a6",
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
import requests
import logging
from django.conf import settings


# Initialize a logger for the application
logger = logging.getLogger(__name__)


def fetch_top_artists():
    """Fetch the top artists from Spotify."""
    url = "https://spotify-scraper.p.rapidapi.com/v1/chart/artists/top"
    headers = {
        "X-RapidAPI-Key": settings.SPOTIFY_API_KEY,
        "X-RapidAPI-Host": settings.SPOTIFY_API_HOST,
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get('artists', [])
    except requests.RequestException as e:
        logger.error(f"Failed to fetch top artists: {e}")
        return []


def fetch_top_tracks():
    """Fetch the top tracks from Spotify."""
    url = "https://spotify-scraper.p.rapidapi.com/v1/chart/tracks/top"
    headers = {
        "X-RapidAPI-Key": settings.SPOTIFY_API_KEY,
        "X-RapidAPI-Host": settings.SPOTIFY_API_HOST,
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get('tracks', [])
    except requests.RequestException as e:
        logger.error(f"Failed to fetch top tracks: {e}")
        return []


def music(request, track_id):
    """Render the music details page."""
    url = f"https://spotify-scraper.p.rapidapi.com/v1/track/metadata?trackId={track_id}"
    headers = {
        "X-RapidAPI-Key": settings.SPOTIFY_API_KEY,
        "X-RapidAPI-Host": settings.SPOTIFY_API_HOST,
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        track_name = data.get("name", "")
        artists = data.get("artists", [])
        first_artist_name = artists[0].get("name", "") if artists else "No artist found"
        
        context = {
            'track_name': track_name,
            'artist_name': first_artist_name,
            'track_id': track_id,
        }
        return render(request, 'music.html', context)
    except requests.RequestException as e:
        logger.error(f"Failed to fetch music data for track ID {track_id}: {e}")
        return HttpResponse(status=500)


def profile(request, artist_id):
    """Render the artist profile page."""
    url = f"https://spotify-scraper.p.rapidapi.com/v1/artist/overview?artistId={artist_id}"
    headers = {
        "X-RapidAPI-Key": settings.SPOTIFY_API_KEY,
        "X-RapidAPI-Host": settings.SPOTIFY_API_HOST,
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        context = {
            'artist_name': data.get("name", ""),
            'monthly_listeners': data.get("stats", {}).get("monthlyListeners", 0),
            'header_url': data.get("visuals", {}).get("header", [{}])[0].get("url", ""),
            'top_tracks': data.get("discography", {}).get("topTracks", []),
        }
        return render(request, 'profile.html', context)
    except requests.RequestException as e:
        logger.error(f"Failed to fetch artist profile data for artist ID {artist_id}: {e}")
        return HttpResponse(status=500)


def login(request):
    """Handle user login."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user:
            auth_login(request, user)
            messages.success(request, 'Logged in successfully!')
            return redirect('/')
        else:
            messages.error(request, 'Invalid credentials.')
    
    return render(request, 'login.html')


def signup(request):
    """Handle user signup."""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        # Check if the passwords match
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'signup.html')
        
        # Check if the username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'signup.html')
        
        # Check if the email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'signup.html')
        
        # Create a new user
        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            auth_login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('/')
        except Exception as e:
            logger.error(f"Error during account creation: {e}")
            messages.error(request, 'Error creating account.')
            return render(request, 'signup.html')
    
    return render(request, 'signup.html')


def logout(request):
    """Handle user logout."""
    auth_logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('/login')


@login_required(login_url='/login')
def index(request):
    """Render the home page with top artists and top tracks."""
    top_artists = fetch_top_artists()
    top_tracks = fetch_top_tracks()
    
    # Organize top tracks into groups of six
    first_six_tracks = top_tracks[:6]
    second_six_tracks = top_tracks[6:12]
    third_six_tracks = top_tracks[12:18]
    
    context = {
        'top_artists': top_artists,
        'first_six_tracks': first_six_tracks,
        'second_six_tracks': second_six_tracks,
        'third_six_tracks': third_six_tracks,
    }
    
    return render(request, 'index.html', context)


def search(request):
    """Handle search requests and render search results."""
    if request.method == 'POST':
        search_query = request.POST.get('search_query')
        url = "https://spotify-scraper.p.rapidapi.com/v1/search"
        
        params = {
            "term": search_query,
            "type": "track"
        }
        
        headers = {
            "X-RapidAPI-Key": settings.SPOTIFY_API_KEY,
            "X-RapidAPI-Host": settings.SPOTIFY_API_HOST,
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            search_results = data.get("tracks", {}).get("items", [])
            
            context = {
                'search_query': search_query,
                'search_results': search_results,
            }
            
            return render(request, 'search.html', context)
        except requests.RequestException as e:
            logger.error(f"Failed to search for query '{search_query}': {e}")
            messages.error(request, 'Failed to search.')
            return redirect('/')
    
    return render(request, 'search.html')
