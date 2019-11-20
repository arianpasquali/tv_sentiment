# standard imports
import json
import os
import uuid
import io
import time
import random
import requests

# third party imports
# import psycopg2
# from psycopg2 import sql
# import sqlalchemy
# from sqlalchemy import create_engine
import pandas as pd

from flask import Flask, render_template, jsonify, redirect, url_for
# from flask_sqlalchemy import SQLAlchemy
from db_models import db, Shows, Comments
from twitter_model import Twitter_Retrieve

db_name = os.environ['POSTGRES_DB']
db_user = os.environ['POSTGRES_USER']
db_password = os.environ['POSTGRES_PASSWORD']
host_addr = "database:5432"

# ml_addr = "ml_server:8008"
ml_addr = "192.168.1.135:8008"

app = Flask(__name__)

DB_URL = 'postgresql+psycopg2://{user}:{pw}@{url}/{db}'.format(user=db_user, pw=db_password, url=host_addr, db=db_name)

app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# db = SQLAlchemy(app)
db.init_app(app)

twitter = Twitter_Retrieve()


@app.route('/')
def show_all():
    return render_template('show_all.html', shows=Shows.query.all())


@app.route('/show_comments')
def show_comments():
    return render_template('show_comments.html', comments=Comments.query.all())


@app.route('/add')
def add():
    show = Shows('daybreak', 'netflix', True)
    db.session.add(show)
    db.session.commit()
    return render_template('show_all.html', shows=Shows.query.all())


@app.route('/predict_test')
def predict_test():
    url = f'http://{ml_addr}/api/v1/predict'
    response = requests.post(url, json={"text": "daybreak is amazing"})
    return jsonify(response.json())


@app.route('/run')
def run_model():
    url = f'http://{ml_addr}/api/v1/predict'
    comments = []

    # get shows
    shows = Shows.query.filter_by(active=True).all()

    for show in shows:
        # query twitter
        results = twitter.search(f'{show.name} {show.service}')

        # run results through model
        for res in results:
            display_res = {}
            response = requests.post(url, json={"text": res}).json()
            comments.append(Comments(show.id, res, response['label'], response['score']))

    db.session.add_all(comments)
    db.session.commit()

    # store results and messages
    return redirect(url_for('show_comments'))


if __name__ == '__main__':
    print("running my app")
    # db.drop_all()
    # db.create_all()
    app.run(debug=True, host='0.0.0.0', port=80)