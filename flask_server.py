
import os
from flask import Flask, render_template, request, jsonify
import requests
from main import search_movies, get_movie_details, get_yts_torrents, get_1337x_torrents
import asyncio

app = Flask(__name__)

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Movie Search</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            .search-container {
                margin-bottom: 20px;
            }
            input[type="text"] {
                padding: 10px;
                width: 70%;
                font-size: 16px;
            }
            button {
                padding: 10px 20px;
                font-size: 16px;
                background-color: #4CAF50;
                color: white;
                border: none;
                cursor: pointer;
            }
            .movie-card {
                border: 1px solid #ddd;
                padding: 15px;
                margin-bottom: 15px;
                border-radius: 5px;
            }
            .movie-title {
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 5px;
            }
            .movie-info {
                margin-bottom: 10px;
                color: #666;
            }
            .download-links {
                margin-top: 10px;
            }
        </style>
    </head>
    <body>
        <h1>Movie Search</h1>
        <div class="search-container">
            <input type="text" id="movie-search" placeholder="Enter movie name...">
            <button onclick="searchMovie()">Search</button>
        </div>
        <div id="results"></div>

        <script>
            async function searchMovie() {
                const movieName = document.getElementById('movie-search').value;
                if (!movieName) return;
                
                document.getElementById('results').innerHTML = '<p>Searching...</p>';
                
                try {
                    const response = await fetch(`/search?movie=${encodeURIComponent(movieName)}`);
                    const data = await response.json();
                    
                    let resultsHtml = '';
                    if (data.movies && data.movies.length > 0) {
                        data.movies.forEach(movie => {
                            resultsHtml += `
                                <div class="movie-card">
                                    <div class="movie-title">${movie.title} (${movie.year})</div>
                                    <div class="movie-info">Rating: ${movie.rating}</div>
                                    <p>${movie.overview}</p>
                                    <button onclick="getMovieDetails('${movie.id}')">Get Details</button>
                                </div>
                            `;
                        });
                    } else {
                        resultsHtml = '<p>No movies found.</p>';
                    }
                    
                    document.getElementById('results').innerHTML = resultsHtml;
                } catch (error) {
                    document.getElementById('results').innerHTML = '<p>Error searching for movies.</p>';
                    console.error(error);
                }
            }
            
            async function getMovieDetails(movieId) {
                document.getElementById('results').innerHTML = '<p>Loading movie details...</p>';
                
                try {
                    const response = await fetch(`/movie/${movieId}`);
                    const data = await response.json();
                    
                    let detailsHtml = `
                        <div class="movie-card">
                            <div class="movie-title">${data.title}</div>
                            <p>${data.overview}</p>
                            ${data.poster ? `<img src="${data.poster}" alt="${data.title}" style="max-width: 200px;">` : ''}
                            
                            <div class="download-links">
                                <h3>Download Links:</h3>
                    `;
                    
                    if (data.yts_links) {
                        detailsHtml += `<h4>YTS Links:</h4>${formatLinks(data.yts_links)}`;
                    }
                    
                    if (data.x1337_links) {
                        detailsHtml += `<h4>1337x Links:</h4>${formatLinks(data.x1337_links)}`;
                    }
                    
                    if (!data.yts_links && !data.x1337_links) {
                        detailsHtml += '<p>No download links found.</p>';
                    }
                    
                    detailsHtml += `
                            </div>
                            <button onclick="searchMovie()">Back to Results</button>
                        </div>
                    `;
                    
                    document.getElementById('results').innerHTML = detailsHtml;
                } catch (error) {
                    document.getElementById('results').innerHTML = '<p>Error fetching movie details.</p>';
                    console.error(error);
                }
            }
            
            function formatLinks(links) {
                // Convert markdown links to HTML
                return links.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank">$1</a>').replace(/\n/g, '<br>');
            }
        </script>
    </body>
    </html>
    '''

@app.route('/search')
def search():
    movie_name = request.args.get('movie', '')
    if not movie_name:
        return jsonify({'error': 'No movie name provided'})
    
    # Use the async function in a sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    movies, total_pages = loop.run_until_complete(search_movies(movie_name))
    
    return jsonify({
        'movies': movies,
        'total_pages': total_pages
    })

@app.route('/movie/<movie_id>')
def movie_details(movie_id):
    # Use the async function in a sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    title, overview, poster = loop.run_until_complete(get_movie_details(movie_id))
    
    if title:
        yts_links = loop.run_until_complete(get_yts_torrents(title))
        x1337_links = loop.run_until_complete(get_1337x_torrents(title))
        
        return jsonify({
            'title': title,
            'overview': overview,
            'poster': poster,
            'yts_links': yts_links,
            'x1337_links': x1337_links
        })
    
    return jsonify({'error': 'Movie not found'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
