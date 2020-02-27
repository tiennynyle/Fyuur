#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys
from flask_wtf.csrf import CSRFProtect
from datetime import datetime as dt
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app,db)
csrf = CSRFProtect(app)


# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    image_link = db.Column(db.String(500))
    genres = db.Column(db.ARRAY(db.String))
    contact_id = db.Column(db.Integer, db.ForeignKey('ContactInfo.id'))  

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    genres = db.Column(db.ARRAY(db.String))
    image_link = db.Column(db.String(500))
    contact_id = db.Column(db.Integer, db.ForeignKey('ContactInfo.id'))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
class Show(db.Model):
    __tablename__= 'Show'

    id = db.Column(db.Integer, primary_key = True)
    start_time = db.Column(db.DateTime)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)

class ContactInfo(db.Model):
    __tablename__='ContactInfo'

    id = db.Column(db.Integer, primary_key = True)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    
    # TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
db.create_all()
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  form = None 
  return render_template('pages/home.html' , form=form)

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data=[]
  venues = Venue.query.all()
  shows = Show.query.all()

  for show in shows:
    show_data = {
      'id': show.venue_id,
      'start_time': show.start_time
    }
  map = {}

  numUpcomingShows = 0
  for venue in venues: 
    showsAvail = Show.query.filter_by(venue_id=venue.id)
    numUpcomingShows = (showsAvail.filter(Show.start_time > dt.now())).count()
    venue_data= {
      'id':venue.id,
      'name': venue.name,
      "num_upcoming_shows" : numUpcomingShows
    }
    contactId = (venue.contact_id)
    contact = ContactInfo.query.get(contactId)
    city = contact.city 
    state = contact.state
    key = city + "*" + state
    if key not in map:
      map[key] = [venue_data]
    else:
      map[key].append(venue_data)
  for key, value in map.items():
    #print (key)    
    add = key.split("*")
    city = add[0]
    state = add[1]
    object = {
      "city": city, 
      "state": state,
      "venues": value
    }
    data.append(object)

  return render_template('pages/venues.html', areas=data, form=VenueForm())

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form.get('search_term')
  venues = Venue.query.filter(Venue.name.ilike('%{}%'.format(search_term))).all()
  data =[]

  for venue in venues:
    showsAvail = Show.query.filter_by(venue_id=venue.id)
    numUpcomingShows = (showsAvail.filter(Show.start_time > dt.now())).count()
    venue_data = {
      "id" : venue.id,
      'name' : venue.name,
      'num_upcoming_shows' : numUpcomingShows
    }
    data.append(venue_data)
    
  response={
    "count": len(data),
    "data": data
  }
  form = VenueForm()

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''), form=form)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  selectedVenue = Venue.query.get(venue_id)
  numShows = Show.query.filter_by(venue_id=selectedVenue.id).all()
  listOfPastShows = []
  listOfUpcomingShows = []

  for show in numShows:
    print(show.artist_id)
    artist = Artist.query.get(show.artist_id)
    print(artist)
    show_data = {
      'artist_id': show.artist_id,
      'artist_name': artist.name,
      'artist_image_link': artist.image_link,
      'start_time': str(show.start_time)
    }
    if show.start_time <= dt.now():
      listOfPastShows.append(show_data)
    else:
      listOfUpcomingShows.append(show_data)
  print(listOfPastShows, listOfUpcomingShows)
  venueInfo = ContactInfo.query.get(selectedVenue.contact_id)

  data = {
    "id": selectedVenue.id,
    "name": selectedVenue.name,
    "genres": selectedVenue.genres,
    "address": venueInfo.address,
    "city": venueInfo.city,
    "state": venueInfo.state,
    "phone": venueInfo.phone,
    "website": venueInfo.website,
    "facebook_link": venueInfo.facebook_link,
    "image_link": selectedVenue.image_link,
    "past_shows": listOfPastShows,
    "upcoming_shows": listOfUpcomingShows,
    "past_shows_count": len(listOfPastShows),
    "upcoming_shows_count": len(listOfUpcomingShows),
  }

  return render_template('pages/show_venue.html', venue=data, form=VenueForm())

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = None
  form = VenueForm(request.form)
  if not form.validate():
    flash('Bad Input, See Below')
    return render_template('forms/new_venue.html', form=form)

  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    facebook_link = request.form['facebook_link']
    image_link = request.form['image_link']
    website = request.form['website']
    contact = ContactInfo(city=city, state=state, address=address,phone=phone,facebook_link=facebook_link,website=website)
    db.session.add(contact)
    db.session.commit()
    contact_id = contact.id
    venue_created = Venue(name=name,genres=genres, image_link=image_link, contact_id=contact_id)
    if len(genres) > 5:
      flash('No more than 5 genres please')
      return redirect(url_for('create_venue_form'))
    db.session.add(venue_created)
    db.session.commit()
  except:
    db.session.rollback()
    print(sys.exc_info())
    error = True
  finally:
    db.session.close()
  if not error:
    print(ValidationError)
    flash('Venue ' + name + ' was successfully listed!')
  else:
    flash('An error occurred. Venue ' + name + ' could not be listed.')
    # return redirect(url_for('create_venue_form'))
  return render_template('pages/home.html', form=form) 
    
@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = []
  artists = Artist.query.all()
  for artist in artists:
    artist_data= {
      'id': artist.id,
      'name': artist.name,
    }
    data.append(artist_data)
  form = ArtistForm()
  return render_template('pages/artists.html', artists=data,form=form)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form.get('search_term')
  artists = Artist.query.filter(Artist.name.ilike('%{}%'.format(search_term))).all()
  data =[]

  for artist in artists:
    showsAvail = Show.query.filter_by(artist_id=artist.id)
    numUpcomingShows = (showsAvail.filter(Show.start_time > dt.now())).count()
    artist_data = {
      "id" : artist.id,
      'name' : artist.name,
      'num_upcoming_shows' : numUpcomingShows
    }
    data.append(artist_data)
    
  response={
    "count": len(data),
    "data": data
  }
  form = ArtistForm()
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''), form=form)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  data = []
  selectedArtist = Artist.query.get(artist_id)
  artistInfo = ContactInfo.query.get(selectedArtist.contact_id)
  
  numShows = Show.query.filter_by(artist_id=selectedArtist.id).all()
  listOfPastShows = []
  listOfUpcomingShows = []

  for show in numShows:
    print(show.venue_id)
    venue = Venue.query.get(show.venue_id)
    print(venue)
    show_data = {
      'venue_id': show.venue_id,
      'venue_name': venue.name,
      'venue_image_link': venue.image_link,
      'start_time': str(show.start_time)
    }
    if show.start_time <= dt.now():
      listOfPastShows.append(show_data)
    else:
      listOfUpcomingShows.append(show_data)
  print(listOfPastShows, listOfUpcomingShows)
  data = {
    "id": selectedArtist.id,
    "name": selectedArtist.name,
    "genres": selectedArtist.genres,
    "city": artistInfo.city,
    "state": artistInfo.state,
    "phone": artistInfo.phone,
    'website': artistInfo.website,
    "facebook_link": artistInfo.facebook_link,
    "image_link": selectedArtist.image_link,
    "past_shows": listOfPastShows, 
    "upcoming_shows":listOfUpcomingShows,
    "past_shows_count": len(listOfPastShows),
    "upcoming_shows_count": len(listOfUpcomingShows),
  }
  
  return render_template('pages/show_artist.html', artist=data,form = ArtistForm())

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = {}
  form = ArtistForm()
  selectedArtist = Artist.query.get(artist_id)
  artistInfo = ContactInfo.query.get(selectedArtist.contact_id)

  form.name.data = selectedArtist.name
  form.genres.data = selectedArtist.genres
  form.image_link.data = selectedArtist.image_link
  form.city.data = artistInfo.city
  form.state.data = artistInfo.state
  form.facebook_link.data = artistInfo.facebook_link
  form.website.data = artistInfo.website
  form.phone.data = artistInfo.phone
  
  artist = {
    "id": selectedArtist.id,
    "name": selectedArtist.name
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  error = None
  form = ArtistForm(request.form)
  if not form.validate():
    flash('Bad Input, See Below')
    return render_template('forms/edit_artist.html', form=form)
  try:
    selectedArtist = Artist.query.get(artist_id)
    artistInfo = ContactInfo.query.get(selectedArtist.contact_id)
    selectedArtist.name = request.form['name']
    artistInfo.city = request.form['city']
    artistInfo.state = request.form['state']
    artistInfo.phone = request.form['phone']
    selectedArtist.genres = request.form.getlist('genres')
    artistInfo.facebook_link = request.form['facebook_link']
    selectedArtist.image_link = request.form['image_link']
    artistInfo.website = request.form['website']
    
    db.session.commit()

  except:
    db.session.rollback()
    print(sys.exc_info())
    error = True
  finally:
    db.session.close()
  if not error:
    flash('Artist ' + request.form['name'] + ' was successfully edited!')
  else:
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be edited.')

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  selectedVenue = Venue.query.get(venue_id)
  venueInfo = ContactInfo.query.get(selectedVenue.contact_id)

  form.name.data = selectedVenue.name
  form.genres.data = selectedVenue.genres
  form.image_link.data = selectedVenue.image_link
  form.address.data = venueInfo.address
  form.city.data = venueInfo.city
  form.state.data = venueInfo.state
  form.facebook_link.data = venueInfo.facebook_link
  form.website.data = venueInfo.website
  form.phone.data = venueInfo.phone
  venue = {
    "id": selectedVenue.id,
    "name": selectedVenue.name,
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  error = None
  form = VenueForm(request.form)
  if not form.validate():
    flash('Bad Input, See Below')
    return render_template('forms/edit_venue.html', form=form)
  try:
    selectedVenue = Venue.query.get(venue_id)
    venueInfo = ContactInfo.query.get(selectedVenue.contact_id)
    selectedVenue.name = request.form['name']
    venueInfo.address = request.form['address']
    venueInfo.city = request.form['city']
    venueInfo.state = request.form['state']
    venueInfo.phone = request.form['phone']
    selectedVenue.genres = request.form.getlist('genres')
    venueInfo.facebook_link = request.form['facebook_link']
    selectedVenue.image_link = request.form['image_link']
    venueInfo.website = request.form['website']
    
    db.session.commit()

  except:
    db.session.rollback()
    print(sys.exc_info())
    error = True
  finally:
    db.session.close()
  if not error:
    flash('Venue ' + request.form['name'] + ' was successfully edited!')
  else:
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be edited.')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = None
  form = ArtistForm(request.form)
  if not form.validate():
    flash('Bad Input, See Below')
    return render_template('forms/new_artist.html', form=form)
  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    facebook_link = request.form['facebook_link']
    image_link = request.form['image_link']
    website = request.form['website']
    contact = ContactInfo(city=city, state=state, phone=phone,facebook_link=facebook_link,website=website)
    db.session.add(contact)
    db.session.commit()
    contact_id = contact.id
    artist_created = Artist(name=name, genres=genres, image_link = image_link, contact_id=contact_id)
    db.session.add(artist_created)
    db.session.commit()
  except:
    db.session.rollback()
    print(sys.exc_info())
    error = True
  finally:
    db.session.close()
  if not error:
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  else:
      flash('An error occurred. Artist ' + name + ' could not be listed.')
  return render_template('pages/home.html', form=form)


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data = []
  shows = Show.query.all()
  
  for show in shows:
    # Adding the first to query the actual object 
    # See https://flask-sqlalchemy.palletsprojects.com/en/2.x/queries/
    venue = Venue.query.filter_by(id=show.venue_id).first()
    print(venue.name)
    artist = Artist.query.filter_by(id=show.artist_id).first()
    print(artist.name, artist.image_link)
    show_data = {
      'venue_id': show.venue_id,
      'venue_name': venue.name,
      'artist_id': show.artist_id,
      'artist_name': artist.name,
      'artist_image_link': artist.image_link,
      'start_time': str(show.start_time)
    }
    data.append(show_data)
  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  error = False
  form = ShowForm()
  try:
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    start_time = request.form['start_time']
    show_created = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
    db.session.add(show_created)
    db.session.commit()
  except:
    db.session.rollback()
    print(sys.exc_info())
    # flash('An error occurred. Show could not be listed.')
    error = True
  finally:
    db.session.close()
  if not error:
    # on successful db insert, flash success
    flash('Show was successfully listed!') 
  else:
    flash('An error occurred. Show could not be listed.')
  # TODO: on unsuccessful db insert, flash an error instead.
  return render_template('pages/home.html', form=form)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()
    csrf.init_app(app)

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
