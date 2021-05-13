# My Project 
This project is Nathans attempt at fda

# Creating venv and Running Docker and Postgres
First you want to set up your virtual environment by using this command 
and then activate the venv something as follows

python3 -m venv /path/to/new/virtual/environment
venv3/bin/activate

Then you want to install docker and make a
folder in a known location for yourself, run this line on the command line.

docker run -d --name dev-postgres -e POSTGRES_PASSWORD=password -v {known folder location}:/var/lib/postgresql/data -p 5432:5432 postgres

You can check if the container is running by entering 

docker ps

To enter Postgres to manage all the databases enter this into the command line,
and the password is going to be the POSTGRES_PASSWORD which is password in this case.

psql -h localhost -U postgres

# Link to the data set
Click on the link below and scroll to the bottom and on the 'Full download 
of All Data Types' and click on the first one which is April 2021 (CSV)

https://fdc.nal.usda.gov/download-datasets.html#bkmk-1

After you go into your downloads you can unzip them and place them in a 
folder called say 'foods' and grab the path of that by entering 

pwd

#Populate database
To populate the database enter this

python database.py --csv-data-path {path to the 'foods'}

NOTE: This is going to take a very long time because the amount of data it has to populate.
One table is over a million, and the biggest one is about 15 million.
Once data is loaded it will create the indexes

#Run the App
python app.py

Grab the link where it says it's running the app on and paste that URL into the search bar 
And there you go!

#Working the App
The User search bar is if you wanna save your excluded nutrients that you don't want then 
just enter in your name and whenever you click on the Excluded Nutrients table near the bottom 
in black. Unfortunately the remove bottom doesn't work as I was unable to figure out how to 
delete a dynamically allocated button.

The Foods search bar below the users one is where you can search up any food you want and it will 
update the list to you with a limited amount of foods with that search name in it. Once you click 
on the food you selected then if you scroll down towards the bottom it will show you the percentage 
of the different types of nutrients are in that food.

When you select on a excluded nutrient and go to search for a food then, that food is not going to 
have that nutrient that you deselected from it.


