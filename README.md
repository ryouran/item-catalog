# Item Catalog
Completed for [Udacity's Full Stack Web Developer Nanodegree program](https://www.udacity.com/course/full-stack-web-developer-nanodegree--nd004).

## Project Overview
This project is to develop a RESTful web application which provides a list of items within categories and allows users to perform CRUD (Create, Read, Update, and Delete) operations, as well as provide a third-party user authentication and authorization service.

## About this app

This application is called Homework Tracker. It stores homework items in user-defined subjects (e.g., Math) and allows users to manage them.  The user can log in using their Google or Facebook account to perform CRUD operations on subjects or homework items.

Users can view all subjects and homework items created without logging in, but they cannot edit or delete subjects or items if they are not the ones who created them.

### Requirements
  * [Python2.7.x](https://www.python.org/)
  * [SQLAlchemy 1.2.0 or higher](http://www.sqlalchemy.org/)
  * [Flask 0.12.2](http://flask.pocoo.org/)
  * [Vagrant](https://www.vagrantup.com/)
  * [VirtualBox](https://www.virtualbox.org/)
  * oauth2client
  * httplib2
  * requests

### Skills used for this project
  * Python
  * Jinja
  * Flask
  * SQLAlchemy
  * HTML
  * CSS
  * Bootstrap

### Set up the project
1. Install [VirtualBox](https://www.vagrantup.com/) and [Vagrant](https://www.vagrantup.com/).
	* Instructions for installing the Vagrant VM can be found [here](https://www.udacity.com/wiki/ud197/install-vagrant).
2. Download or clone [fullstack-nanodegree-vm](https://github.com/udacity/fullstack-nanodegree-vm) repository.
3. Go to the vagrant/catalog directory.
4. Download the project zip and unzip the file or clone this repository in the directory.
5. Type `vagrant up` to start your vagrant VM.
6. Type `vagrant ssh` to log into your VM.
7. Type `/vagrant/catalog` to navigate to the catalog directory.

### Get OAuth client credentials
This app uses Google and Facebook user authetication and authorization services.  In order to have users log in by using either their Google or Facebook account, you will need to get OAuth client credentials.

For Google, go to the
[Google Developers Console](https://console.developers.google.com/) to create your credentials.  Then place your client\_id, project\_id, and client\_secret in the `g_client_secrets.json` file or download a JSON file from the site which contains your credentials and replace the entire content in the `g_client_secrets.json` file.

For Facebook, go to [Facebook Login](https://developers.facebook.com/products/login) to create your credentials.  Then place your app\_id and app\_secret in the `fb_client_secrets.json` file.


### Run the Homework Tracker App
1. Start your vagrant VM and log in as described above if not running.
2. Type `/vagrant/catalog` to navigate to the catalog directory.
3. Type `python db_setup.py` to initialize the database.
4. Type `python homework_items.py` to populate the database with sample subject and homework items (Optional)
5. Type `python applicaiton.py` to run the Flask web server.  In your browser, go to `http://localhost:5000` to view the application.

### Shutting down the VM
Press `Ctrl-D` to log out of the VM and type `vagrant halt` to shut it down.


### JSON Endpoints
Catalog JSON: `/subject/JSON` - Show all subjects

Category JSON: `/subject/<int:subject_id>/item/JSON` - Show items for a specific category

Item JSON: `/subject/<int:subject_id>/item/<int:item_id>/JSON` - Show a specific item
