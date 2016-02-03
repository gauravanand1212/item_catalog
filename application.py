from flask import Flask, render_template, request
from database_setup import Base, Category, Items

from flask import session as login_session, g
from flask import make_response, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc, MetaData
from sqlalchemy.orm import sessionmaker

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import random
import string
import requests
import urllib2
import datetime
import requests


# Connect to Database and create database session
engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine
meta = MetaData()

DBSession = sessionmaker(bind=engine)
session = DBSession()

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog App"


# Set Global variable to be used in header.html to determine
# text of the login button based on user logged status
@app.before_request
def before_request():
    g.logged = False
    if 'username' in login_session:
        g.logged = True


# Login page with request token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# Module to connect as Google user
@app.route('/gconnect', methods=['GET', 'POST'])
def gconnect():
    # Validate state token

    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
                                'Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token
    print 'logged in ' + credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'
    flash("You are now logged in as %s" % login_session['username'])

    return 'success'


# Logout as Google user
@app.route('/gdisconnect', methods=['GET'])
def gdisconnect():
    credentials = login_session.get('credentials')
# Check if the user is connected
    if credentials is None:
        response = make_response(json.dumps(
                                'Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = ('https://accounts.google.com/o/oauth2/revoke?token=%s'
           % credentials)
    print url
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        response = make_response(json.dumps('Disconnect successful'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        print "errored"
        login_session.clear()
        response = make_response(json.dumps('Unable to revoke token'), 400)
        response.headers['Content-Type'] = 'application/json'
        return redirect(url_for('showCategories'))


# Module to connect as Facebook user
@app.route('/fbconnect', methods=['GET', 'POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?'
    url += 'grant_type=fb_exchange_token&client_id=%s' % app_id
    url += '&client_secret=%s' % app_secret
    url += '&fb_exchange_token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.4/me"
    # strip expire tag from access token
    token = result.split("&")[0]

    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session to properly logout,
    # let's strip out the information before the equals sign in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.4/me/picture?%s' % token
    url += '&redirect=0&height=200&width=200'
    print url
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]
    flash("You are now logged in as %s" % login_session['username'])
    return "success"


# Logout as Facebook user
@app.route('/fbdisconnect', methods=['GET'])
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' \
          % (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "logged out"


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            login_session.clear()
            flash("You have successfully been logged out.")
            return "success"
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            login_session.clear()
            flash("You have successfully been logged out.")
            return "success"
    else:
        flash("You were not logged in")
        return redirect(url_for('showCategories'))


# Show Item based on a item_id
@app.route('/item/<item_id>')
def showItem(item_id):
    item = session.query(Items).filter_by(id=item_id).one()
    return render_template('showItem.html', item=item)


# Edit Item based on item_id
@app.route('/item/<item_id>/edit', methods=['GET', 'POST'])
def editItem(item_id):
    # Ensure only authenticated users can edit item
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(Items).filter_by(id=item_id).one()
    if request.method == 'POST':
        if request.form['title']:
            editedItem.name = request.form['title']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['categories']:
            editedItem.categories[:] = []
            category_ids = request.form.getlist('categories')
            print category_ids[0]
            for cat_id in category_ids:
                category = session.query(Category).filter_by(id=cat_id).one()
                print category.name
                editedItem.categories.append(category)
        editedItem.updated = datetime.datetime.utcnow()
        session.add(editedItem)
        session.commit()
        flash("Item changed !!")
        return redirect(url_for('showCategories'))
    else:
        categories = session.query(Category).all()
        item = session.query(Items).filter_by(id=item_id).one()
        return render_template('editItem.html', item=item,
                               categories=categories)


# Delete a selected Item
@app.route('/item/<item_id>/delete', methods=['GET', 'POST'])
def deleteItem(item_id):
    # Ensure only authenticated users can delete item
    if 'username' not in login_session:
        return redirect('/login')
    item = session.query(Items).filter_by(id=item_id).one()
    if request.method == 'POST':
        if 'delete' in request.form:
            session.delete(item)
            session.commit()
            flash("Item deleted !!")
        return redirect(url_for('showCategories'))
    else:
        return render_template('deleteItem.html', item=item)


# Display items with the selected category
@app.route('/categories/<int:category_id>')
def showCategory(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    categories = session.query(Category).all()
    return render_template('showCategory.html', categories=categories,
                           category=category)


# Add Item in a category
@app.route('/categories/<int:category_id>/addItem', methods=['GET', 'POST'])
def addItem(category_id):
    # Ensure only authenticated users can add item
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        newItem = Items(name=request.form['title'],
                        description=request.form['description'])
        newItem.categories.append(category)
        session.add(newItem)
        session.commit()
        flash("Item Added !!")
        return redirect(url_for('showCategories'))
    else:
        return render_template('addItem.html', category=category)


# Display all catgeories and items
@app.route('/')
@app.route('/categories')
def showCategories():
    categories = session.query(Category).all()
    items = session.query(Items).all()
    return render_template('categories.html', categories=categories,
                           items=items)


# JSON endpoint
@app.route('/json')
def catalogJSON():
    categories = session.query(Category).all()
    return jsonify(Categories=([(i.serialize) for i in categories]))


# API functions to load data from Udacity API as well as
# test and delete any previously loaded data
# API functions : Populate database
@app.route('/api_load', methods=['GET'])
def api_load():
    url = 'https://www.udacity.com/public-api/v0/courses'
    response = urllib2.urlopen('https://www.udacity.com/public-api/v0/courses')
    json_response = json.loads(response.read())
    categories = session.query(Category).all()
    for category in categories:
        try:
            category.items[:] = []
        except:
            continue
    session.query(Items).delete()
    session.query(Category).delete()

    for track in json_response['tracks']:
        try:
            test = session.query(Category).filter_by(name=track['name']).one()
        except:
            category = Category(name=track['name'])
            session.add(category)

    for course in json_response['courses']:
        try:
            test = session.query(Items).filter_by(name=course['title']).one()
        except:
            item = Items(name=course['title'], description=course['summary'])
            session.add(item)
        for track in course['tracks']:
            category = session.query(Category).filter_by(name=track).one()
            if item not in category.items:
                category.items.append(item)
    session.commit()
    return 'Data Loaded'


# API functions : check if database populated
@app.route('/api_test')
def api_test():
    response = ''
    categories = session.query(Category).all()
    for category in categories:
        for item in category.items:
            response += '<p>' + category.name + '-' + item.name + '</p>'
    return '<html><head></head><body>' + response + '</body></html>'


# API functions : clear database
@app.route('/api_clear')
def api_clear():
    session.query(Items).delete()
    session.query(Category).delete()

    con = engine.connect()

    for tbl in reversed(meta.sorted_tables):
        engine.execute(tbl.delete())
        tbl.drop(engine)
    session.expire_all()
    session.commit()
    return 'Cleared'


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
