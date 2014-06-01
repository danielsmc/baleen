Baleen casts a wide net for interesting links on twitter. It follows the people that the people you follow follow, and shows you the stories that everyone's talking about. There will be a web interface, but it's not built yet. I hope you like reading JSON.

This project owes a major conceptual debt to the Nieman Journalism Lab's [Fuego](http://www.niemanlab.org/2013/07/introducing-openfuego-your-very-own-heat-seeking-twitter-bot/).

Installation steps:

	Install packages for: python27, mysql, libxml2, libxslt (and git to pull down the repo)
	For ubuntu 14:
	$ sudo apt-get install -y mysql-server libmysqlclient-dev git python-pip python-dev libxml2-dev libxslt1-dev
	$ sudo pip install virtualenv

    $ virtualenv ve
    $ . ve/bin/activate
    $ pip install -r requirements.txt

    In mysql, create a user and db

    $ mysql -u <user> -p -D <database> < schema.sql

    Install or create config.json

    $ python load_impact.py

    load_impact will take quite a while (~1 minute for every account you follow on twitter)

    $ nohup python -u forever.py &