This application is used to display Udacity course tracks
and the courses within the tracks as a Catalog. It also allows
a logged-in user to add, edit and delete courses in the catalog

The zip file contains the following files:
-----------------------------------------
------| application.py
------| database_setup.py
------| client_secrets.json
------| fb_client_secrets.json
------| README.md
static
----------| styles.css
templates
----------| login.html
----------| main.html
----------| categories.html
----------| header.html
----------| showCategory.html
----------| showItem.html
----------| addItem.html
----------| editItem.html
----------| deleteItem.html
vagrant
----------| Vagrantfile
----------| pg_config.sh


How to run the application:
------------------------------------------
- You need to have Python 2.7 installed on your machine
- You also need a virtual machine (Vagrant) to run the database and
the commands (please see online documentation for vagrant to run Vagrant VM)
- Once you have logged into your vagrant VM (vagrant file included), 
navigate to the folder containing application.py
- Run the file database_setup.py to create the database and tables.
- Run the file application.py using command 'python application.py'
to start the local server

|---------- Populating the database using API -----------|
- To populate tracks and courses information from Udacity API,
enter url localhost:8080/api_load
- To verify that the database has been populated, navigate to url
localhost:8080/api_test to see the track-course relationships
- Incase of error or to retest, clear the database using url
localhost:8080/api_clear

|------------- Application core functions --------------|

- Navigating to home page on localhost:8080 will provide a list 
of categories and courses along with the relationships
- Clicking on a category will narrow down the course list to 
only that track
- Clicking on a course will allow user to view course details
including description and tracks which the course is a part of
- Navigating to localhost:8080/json will provide you the API 
endpoint to get all catalog information in json format
- Users can log in using Google and Facebook credentials. Logging
in provides additional functionality listed below:

|---------------- Logged in functions ------------------|
- Navigating to a category will allow user to add new course to the
category via the Add Item button. Users can then link that course
to other tracks/categories by clicking on the course in the main page
and entering edit mode
- Clicking on a course in main page or category page will provide
Edit and Delete functionality on the View Course page. Edit allows changes
in Course Name, description and tracks it is a part of. Delete allows 
user to delete a course. Track relationships will be deleted automatically



Copyright: XXX
Author: Gaurav Anand
Date: 12/30
