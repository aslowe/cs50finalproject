import os
import requests
import csv
import sys

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required


# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///songs.db")
filename = "tracks_features.csv"

#code referenced from finance
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

#code referenced from finance
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()
    login = True
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html", login=login)

#code referenced from finance
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        again = request.form.get("confirmation")

        if len(db.execute("SELECT username FROM users WHERE username = ?", username)) > 0:
            return apology("Username already exists choose another")
        if username == "":
            return apology("Please input a username")
        if password != again:
            return apology("Passwords don't match")
        if password == "":
            return apology("Please input a password")

        hashed = generate_password_hash(password)
        db.execute("INSERT INTO users (username, hash, numbOfPlaylists) VALUES (?, ?, 0)", username, hashed)

        data = db.execute("SELECT * FROM users WHERE username = ?", username)
        session["user_id"] = data[0]["id"]
        return redirect("/")
    else:
        return render_template("register.html")

#code referenced from finance
@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

#code for the main page
@app.route("/")
@login_required
def index():
    #retrieves the users id and extracts the users username from the list and dictionary
    id = session["user_id"]
    user = db.execute("SELECT username FROM users WHERE id = ?", id)
    items = user[0]
    item = items['username']
    #passes the username into the page so it can be printed on the page
    return render_template("index.html", item=item)

#code for the make page
@app.route("/make", methods=["GET", "POST"])
@login_required
def make():
    #retrieves the users id and extracts the user's number of playlists from the list and dictionary
    id = session["user_id"]
    number = db.execute("SELECT numbOfPlaylists FROM users WHERE id = ?", id)
    playlistno = number[0]
    playlistnumb = playlistno['numbOfPlaylists']
    #initialises empty list so that a new playlist can be created
    list = []
    if request.method == "POST":
        #retrieves the sentence the user inputs and splits it into the words
        sentence = request.form.get("sentence")
        words = sentence.split()
        #initialises the i variable to be one which will later be used as the tracker for which word we are on
        i = 0
        #iterates through the words in the sentence
        for word in words:
            #sets the number of times the word appears in the sentence
            numb = 0
            #iterates through the words later on in the sentence to check for any repeats and tracks how many times it is repeated
            for x in range(i, len(words) - 1):
                if word == words[i]:
                    numb = numb + 1
            #opens the csv file in read and in dictionary form
            with open(filename, 'r') as data:
                for line in csv.DictReader(data):
                    #initialises empty list to get all the data for the song
                    list1 = []
                    #makes the song title in the database all lowercase so that capitalisation doesn't matter
                    wordCheck = str(line["name"])
                    #checks if the word entered (all lowercase) equals the song title of that line
                    if word.lower() == wordCheck.lower():
                        #if there are repeats then it skips the word and minuses one so that it knows that it has to skip only a certain amount of songs to guarantee no songs are the same
                        if numb > 0:
                            numb -= 1
                            continue
                        else:
                            #it appends the title of the song to be in the song data
                            list1.append(word)
                            #it gets the string of the name of the album of that line and appends it to the song data
                            album = str(line["album"])
                            list1.append(album)
                            #it gets the string of the name of the album of that line and then splits so that only the artist name is in it
                            artist = str(line["artists"])
                            #splits at the first instance of ' appearing beacsue the artists are stored as ['artist']
                            artists = artist.split("'", 1)
                            print(artists[1])
                            #splits at the last instance of ' in case the artist name as an apostrophe in it
                            finalArtist = artists[1].split("'", 1)
                            #it appends the artist of the song to be in the song data
                            list1.append(finalArtist[0])
                            #it appends the song list to the playlist list
                            list.append(list1)
                            #increments the value of i so that the repeat checker works properly
                            i+=1
                            #breaks the loop so that once a match is found it moves onto the next word
                            break
        #checks that the length of the list of songs equals the number of the words
        if (len(list) == len(words)):
            #increments the playlist number by 1
            playlistnumb +=1
            #sets n to be 0 so that it initialises what number song we are on in the playlist for the ID
            songno = 0
            #creates the playlist ID to be the number of the playlist-number of the song we are on-userid, so that it is unique
            newplaylistID = str(playlistnumb) + str("-") + str(songno) + str("-") + str(id)
            #updates user number of playlists
            db.execute("UPDATE users SET numbOfPlaylists = ? WHERE id = ?", playlistnumb, id)
            #iterates through the the songs in the playlist
            for item in list:
                #creates a new row in the table with the song data
                db.execute("INSERT INTO playlists(playlistID,userID,playlistName,song,album,artist) VALUES(?, ?, ?, ?, ?, ?)", newplaylistID, id, sentence, item[0], item[1], item[2])
                #removes part of the ID so that the number of the song can be incremented and the playlistID can be updated
                newplaylistID = newplaylistID[:(-1*len(str(songno))-1*len(str(id))-1)]
                songno += 1
                newplaylistID = str(newplaylistID) + str(songno) + str("-") + str(id)
            #returns the make template with valid being true
            return render_template("make.html", valid=True)
        else:
            #returns the make template with valid being false
            return render_template("make.html", valid=False)
    else:
        return render_template("make.html")

#code for the view page
@app.route("/view", methods=["GET", "POST"])
@login_required
def view():
    #retrieves the users id and extracts the user's number of playlists from the list and dictionary
    id = session["user_id"]
    number = db.execute("SELECT numbOfPlaylists FROM users WHERE id = ?", id)
    playlistno = number[0]
    playlistnumb = playlistno['numbOfPlaylists']
    #initialises empty list so that all of the users playlists can be added to it
    list = []
    #iterates starting from 1 to the number of playlists+1
    for x in range (1, (playlistnumb + 1)):
        #sets x to be the start of the playlistID e.g. "1-"
        x = str(x) + "-"
        #returns songs which start with the start of the playlistID and where the ID is the users ID
        playlists = db.execute("SELECT song, album, artist, playlistName FROM playlists WHERE userID = ? AND playlistID LIKE ?", id, x+'%')
        #edits the value of x to omit the end of the sentence and become an integer again
        x = int(x[0: len(x) - 1])
        #appends the playlist to the list of playlists
        list.append(playlists)
    #returns the view template with the list
    return render_template("view.html", list=list)
