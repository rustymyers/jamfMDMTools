MDM Tools
=========

This python + flask script provides a web service to easily send wipe and lock commands to macOS devices enrolled in your jamf server. It lists all systems that are enrolled and their MDM status. Checking the box next to them allows you to send a wipe, or lock, with a custom six digit passcode.
The tool was written to provide a simple method to send wipe commands to many systems at once.

Setup
-----

Setup requires configuring the config file. Running the code once without a config file will generate one for you. This is an example of the config file:

```
[server]
sercretkey = None
grouppass = None

[jss]
username = None
password = None
server = None
```

1. Currently the app uses [flask sessions] to restrict access. The first setting is the secretkey used with sessions to encrypt cookies. Set this to a long, complex, random string of ASCII. 
2. The second setting is the grouppass. The grouppass is the passcode that will be used by anyone accessing the web service. Usernames are also used to login, but are not checked against anything. They serve only the function of logging who did what. *Obvious problems are evident, this should be replaced.
3. The username and password settings under jss are the jamf api account you created for this. Be sure to give the account API access and lock it down to only the systems it should have access to.
4. The server is the url to your JSS. I.E.: https://myjss.com:8443

When setting these variables, quotes are not required and can break some of them. Don't use quotes.

Running
-------

The mdmtools.py script can be run through the terminal for testing. Once started it will create a web service on http://127.0.0.1:5002
This is good for testing purposes, but other [flask deployment options] are best for production.

Feedback
--------

As always, feedback is welcome. Please open GitHub issues and pull requests. Thanks!

[flask deployment options]: http://flask.pocoo.org/docs/0.11/deploying/
[flask sessions]: https://pythonhosted.org/Flask-Session/