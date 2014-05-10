#!venv/bin/python
import argparse
from app import app

parser = argparse.ArgumentParser()
parser.add_argument("--builddb", help="build the database", action="store_true")

if __name__ == '__main__':
    args = parser.parse_args()
    if args.builddb:
        from app import db
        db.create_all()
        db.session.commit()
        print "Database created."
    else:
        app.run(host='0.0.0.0', debug=True)
        print "Starting development server..."
