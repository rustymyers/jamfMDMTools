import os
import urllib2
import base64
import socket
import logging
import ConfigParser
import xml.etree.ElementTree as ET
from flask import Flask, request, render_template, session, redirect, url_for, escape

# API functions:
# https://myjss.com:8443/api/

# Parse Config File
config = ConfigParser.RawConfigParser()
# If file exists
if os.path.exists('mdmtools.cfg'):
    # Logging config
    config.read('mdmtools.cfg')
    secretkey = config.get('server', 'sercretkey')
    grouppass = config.get('server', 'grouppass')
    username = config.get('jss', 'username')
    password = config.get('jss', 'password')
    server = config.get('jss', 'server')

else:
    # Creating new configuration file
    config.add_section("server")
    config.set('server',"sercretkey")
    config.set('server',"grouppass")
    config.add_section('jss')
    config.set('jss',"username")
    config.set('jss',"password")
    config.set('jss',"server")
    with open('mdmtools.cfg', 'wb') as configfile:
        config.write(configfile)
    print "Config File Created. Please edit mdmtools.cfg and run again."
    exit(0)


# https://fangpenlin.com/posts/2012/08/26/good-logging-practice-in-python/
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# create a file handler
handler = logging.FileHandler('action.log')
handler.setLevel(logging.INFO)
# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(handler)

# Set flask app object
app = Flask(__name__)

# Function to create a dict of key:values for table rendering
def createTableTemplate(computerlist,search):
    # Lists for table rendering
    selectboxes = []
    computernames = []
    computerid = []
    mdmcapable = []
    site = []
    
    # For each computer in the list
    for computer in computerlist:
        # Try to get the Name
        name = computer.find('name')
        # If the name exists, it is a computer
        if name != None:
            # Get the computer name
            copmname = name.text
            # Find the computer ID
            compid = computer.find('id')
            # Set computer ID as text
            compid = compid.text
            # Check if computer ID is MDM capable, Get XML response from JAMF
            responsexml = jamfcall('https://' + server + '/JSSResource/computers/id/' + compid, username, password, method='GET')
            # If the computer XML shows it is mdm_capable = true
            if responsexml.findtext("general/mdm_capable") == "true":
                mdmcapablebool = "true"
            # If the copmuter is not mdm_capable
            else:
                mdmcapablebool = "false"
            computersiteID = responsexml.findtext("general/site/id")
            computersiteName = responsexml.findtext("general/site/name")
            
            print computersiteName
            # If we are not running a search, add computer record
            if search == "":
                # Add computer to lists
                selectboxes.append(compid)
                computernames.append(copmname)
                computerid.append(compid)
                mdmcapable.append(mdmcapablebool)
                site.append(computersiteName)
            else:
                # Only add computer to list if it matches our search term in lowercase
                if search.lower() in name.text.lower():
                    # Add computer to lists
                    selectboxes.append(compid)
                    computernames.append(copmname)
                    computerid.append(compid)
                    mdmcapable.append(mdmcapablebool)
                    site.append(computersiteName)

    # Send lists as dict for table
    table_data = {'selectboxes':selectboxes, 'computernames':computernames, 'computerid':computerid, 'mdmcapable':mdmcapable, 'site':site}
    # return render_template('table.html', table_data=table_data, action='/actioncomputers', method='POST')
    return table_data


# https://bryson3gps.wordpress.com/2014/03/30/the-jss-rest-api-for-everyone/
# Function to communicate with jamf
def jamfcall(resource, username, password, method = '', data = None):
    # create a new request object with resource URL
    request = urllib2.Request(resource)
    # Add auth header
    request.add_header('Authorization', 'Basic ' + base64.b64encode(username + ':' + password))
    # add get_method if request is a post, put, or delete
    if method.upper() in ('POST', 'PUT', 'DELETE'):
        request.get_method = lambda: method
    # add content type if request is post, put and there is data
    if method.upper() in ('POST', 'PUT') and data:
        # Add in content type header
        request.add_header('Content-Type', 'text/xml')
        # send request with data and return results
        reponse = urllib2.urlopen(request, data)
        # Convert response to text
        computerxml = response.read()
        # Create new Element Tree with computer xml
        root = ET.fromstring(computerxml)
        return root
    else:
        # send request and return results
        response = urllib2.urlopen(request)
        # Convert response to text
        computerxml = response.read()
        # Create new Element Tree with computer xml
        root = ET.fromstring(computerxml)
        return root

# route and function for home page
@app.route('/')
def index():
    # If we have a user logged in
    if 'username' in session:
        # return home with welcome
        return render_template('home.html', username=str(escape(session['username'])), welcome="true")
    # else return home with login page
    return render_template('home.html', login="true")

# route and function for 404 errors
@app.errorhandler(404)
def page_not_found(error):
    # If we have a user logged in
    if 'username' in session:
        # return 404 without login form
        return render_template('home.html', error="true", username=str(escape(session['username']))), 404
    # return 404 with login form
    return render_template('home.html', error="true", login="true"), 404

# route and function for login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    # If the page is loading with a post
    if request.method == 'POST':
        # Check post form password to see if it matches
        if request.form['password'] == grouppass:
            # Create new session with form username
            session['username'] = request.form['username']
            # Log the user login
            logger.info("Logging In: " + str(escape(session['username'])))
            # Return to index
            return redirect(url_for('index'))
        else:
            # Return home with failed login when password is incorrect
            return render_template('home.html', login="failed")
    # Return home page when loaded with get
    return render_template('home.html', login="true")

@app.route('/logout')
def logout():
    # Log the log out
    logger.info("Logging Out: " + str(escape(session['username'])))
    # remove the username from the session if it's there
    session.pop('username', None)
    # Return home page
    return redirect(url_for('index'))

# Use urllib to get computers, only returns name and id
@app.route('/listcomputers', methods=['GET'])
def list_computers_func():
    # If we have a user logged in
    if 'username' in session:
        # Get response from jamf to list all computers
        responsexml = jamfcall('https://' + server + '/JSSResource/computers', username, password, method='GET')
        # create table from xml
        computerstable = createTableTemplate(responsexml,"")
        # render home with form and table for action from computerstable
        return render_template('home.html', table_data=computerstable, action='/actioncomputers', method='POST', username=str(escape(session['username'])))
    else:
        # Return home with login form
        return render_template('home.html', login="true")

# Retreive computer IDs from form and send locl command using urllib
@app.route('/actioncomputers', methods=['GET','POST'])
def action_computers():
    # Empty arrays for computer table
    computernames = []
    computerid = []
    # If we have a user logged in
    if 'username' in session:
        # If the page is loading with a post
        if request.method == 'POST':
            # Get command from form
            command = request.form['command']
            # Add commmand to url
            commandurl = 'https://' + server + '/JSSResource/computercommands/command/' + command
            # Commands other than BlankPush need passcode
            if command != "BlankPush":
                # Get passcode from form, set to default if blank
                passcode = request.form['passcode']
                # If no passcode was specified
                if passcode == "":
                    # Set passcode to 000000
                    passcode = "000000"
                # If password from form is not 6 digits
                if len(passcode) != 6:
                    # Return to home with passcode fail
                    return render_template('home.html', passcode="true", username=str(escape(session['username'])))
                # Add passcode to command url
                commandurl = commandurl + '/passcode/' + passcode
            # Create comma seperated list of computer IDs from form
            computerlist = ",".join(request.form.getlist('computerform'))
            # Add computer id list, comma seperated, to the command url
            commandurl = commandurl + '/id/' + computerlist
            # Get response from jamf call
            responsexml = jamfcall(commandurl, username, password, method='POST')
            # For all the computer IDs in the form
            for compid in request.form.getlist('computerform'):
                # Gather Computer Data from jamf
                responsexml = jamfcall('https://' + server + '/JSSResource/computers/id/' + compid, username, password, method='GET')
                # Get computer name from xml
                compname = responsexml.findtext("general/name")
                # Add computer name to list
                computernames.append(compname)
                # Add computer id to list
                computerid.append(compid)
        else:
            # Return empty lists for blank page
            computernames.append("none")
            # Return empty lists for blank page
            computerid.append("none")
        # Build table dictionary
        table_data = {'computernames':computernames, 'computerid':computerid}
        # Log user, action, and computers selected
        logger.info(str(escape(session['username'])) + " (" + command + "): " + ','.join(str(p) for p in computernames))
        # Return computer list and comand
        return render_template('home.html', results_data=table_data, results="true", command=command, username=str(escape(session['username'])))
    else:
        # Return home with login form
        return render_template('home.html', login="true")

# Function to search computers
@app.route('/search', methods=['GET','POST'])
def search_video():
    # If we have a user logged in
    if 'username' in session:
        # If the page is loading with a post
        if request.method == 'POST':
            # Get search term from form
            search_computer_name = request.form['name']
            # Retreive all copmuters
            responsexml = jamfcall('https://' + server + '/JSSResource/computers', username, password, method='GET')
            # Build response table with matching computer names
            allcomputers = createTableTemplate(responsexml,search_computer_name)
            # Return search page and computer list
            return render_template('home.html', search="true", table_data=allcomputers, action='/actioncomputers', method='POST', username=str(escape(session['username'])))
        else:
            # Return search page
            return render_template('home.html', search="true", username=str(escape(session['username'])))
    else:
        # Return home with login form
        return render_template('home.html', login="true")

# Do the work
if __name__ == '__main__':
    # set the secret key.  keep this really secret:
    app.secret_key = secretkey
    # Set Debug to true
    app.debug = True
    # Run app
    app.run(host='0.0.0.0', port=5002)