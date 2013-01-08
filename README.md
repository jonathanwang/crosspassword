crosspassword
=============

Alternative password input method



To see a running version of the code, go to:
crosspassword.herokuapp.com


To run the code locally:
First install virtualenv (http://www.virtualenv.org/en/latest/) and pip (http://www.pip-installer.org/en/latest/). virtualenv allows the creation of a virtual environment so that code can be executed in identically configured virtual environments across multiple systems regardless of the actual environment on those systems. pip is a package installer, and it allows fast and easy installation of different modules required for program execution.

After the virtualenv and pip have been installed, setup the virtual environment by running:

$ virtualenv venv --distribute

This creates a virtual environment in the 'venv' directory.
Then activate the virtual environment (needs to be repeated every time a new command line window is opened):

$ source venv/bin/activate

If the virtual environment has been successfully activated, the command line prompt will be preceded by '(venv)'.

Install the necessary packages into the virtual environment by using pip and providing it the requirements.txt file, which lists all of the dependencies of the application:

$ pip install -r requirements.txt

Finally, run the main.py Python file (other than activating the virtual environment as described above, this is the only step that needs to be repeated when running the program again):

$ python main.py
