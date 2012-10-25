======
Fianzo
======

Fianzo is a simple inventory and lending web application originaly intended
for the use of a computer lab. It heavily relies on having an ldap server.

Deployment
==========

For deploying information, refer to the Flask docs, especialy 
http://flask.pocoo.org/docs/deploying/.

Dependences
===========
* Flask 0.8
* Flask-SQLAlchemy >0.16
* WTForms
* python-ldap

And python bindings to the database engine of your choice

Configuration
=============

Configuration is read from the file indicated by the FIANZO_SETTINGS envar,
and has the following fields:

SQLALCHEMY_DATABASE_URI
    SQLAlchemy URL to the database
DEBUG
    Flask variable to set debugging. Set to off in production enviroments
LDAP_URI
    LDAP url
LDAP_SEARCH_ATTR
    Attribute to use when refering to users. Most likely should be 'uid'
LDAP_BASEDN
    Base DN to search users on
SECRET_KEY
    Random string of characters for security
ADMINS
    set (a list works too) of users (specified by their LDAP_SEARCH_ATTR) that
    are allowed to get in the systems. Any users on the ldap Base DN can have
    items lended to them.
IGNORE_AUTH
    Debug Flag, leave it off unless you want to let every page open (and you
    don't want to do that).

Licensing
=========

Fianzo is licensed under the terms of the GPLv3 license.
