beer-api package
================

A beer-manager API including user reviews, favorites lists, and glass-styles. Built on Python3.3 with the Flask
microframework and SQLAlchemy.

Dependencies: Python3.3, SQLite3. Needed python packages are listed in **requirements.txt**, pass this to PIP for easy installation.

Installation Instructions
-------------------------
* Clone the GitHub repository                      `git clone https://github.com/binaryatrocity/beer-api.git`
* Move into the app's directory                    `cd beer-api`
* Create a Python3 virtual environment             `pyvenv-3.3 venv`
* Activate the new environment                     `source venv/bin/activate`
* Download easy_install setup file                 `wget https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py`
* Install easy_install into the venv               `venv/bin/python ez_setup.py`
* Use easy_install to setup PIP                    `venv/local/bin/easy_install pip`
* Let PIP handle requirements file                 `venv/local/bin/pip install -r requirements.txt`
* Cleanup some setup files                         `rm ez_setup.py; rm setuptools*.zip`
* Build SQLite3 database for operation             `./run.py --builddb`
* Run API with Flask development server            `./run.py`

This will run the application with the Flask development server, appropriate for testing. The API
will be available externally from http://YOURDOMAIN.tld:5000/beer/api/v0.1/. Additional instructions
for letting Apache serve the API are below.



Apache HTTPD WSGI Instructions (Untested with pyvenv3.3)
********************************************************

* Install mod_wsgi for Apache if needed            `pacman -S libapache2-mod-wsgi OR apt-get install libapache2-mod-wsgi`
                                                   `see http://code.google.com/p/modwsgi/wiki/QuickInstallationGuide for other installation methods`
* Create a new Apache VirtualHost for the API      `reference http://flask.pocoo.org/docs/deploying/mod_wsgi/#configuring-apache for example file`
* Enable the new Apache host                       `sudo a2ensite <virtualHostFilename>`
* Restart Apache httpd to enable new configuration


API Endpoint Routes
-------------------

.. automodule:: app.routes
    :members:
    :undoc-members:
    :show-inheritance:


Database Models
---------------

.. automodule:: app.models
    :members:
    :show-inheritance:
