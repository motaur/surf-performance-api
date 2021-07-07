import time
import flask
from flask import request, jsonify, send_from_directory
import fitparse
import json
from json import JSONEncoder

from garminexport.garminclient import GarminClient
from garminexport.incremental_backup import incremental_backup
import os
from os import listdir, walk
from os.path import isfile, join

app = flask.Flask(__name__)
app.config["DEBUG"] = True


@app.route('/login', methods=['POST'])
def garmin_backup():
    login = request.json['login']
    password = request.json['password']
    activities = incremental_backup(username=login, password=password, backup_dir=os.path.join('.', login),
                                    export_formats=['fit'], ignore_errors=True)

    return _corsify_actual_response(jsonify(activities))


@app.route("/get_activities_parsed", methods=['GET'])
def get_activities_parsed():
    login = request.args['login']
    filenames: list = next(walk(login))[2]

    for filename in filenames:
        print(filename)
        try:
            fitfile = fitparse.FitFile(login + "/" + filename)
            for message in fitfile.messages:
                if(message.name == 'sport'):
                    for field in message.fields:

                        if(field.name == 'name'):
                            print('name: ' + field.raw_value)

                        if(field.name == 'sport'):
                            print('type: ' + field.value)

            fitfile.close()
        except:
            print('error parse .fit : ' + filename)

    return _corsify_actual_response(jsonify(filenames))


@app.route("/get_activity_file", methods=['GET'])
def get_activity_file():
    login = request.args['login']
    id = request.args['id']
    filenames: list = next(walk(login))[2]

    for filename in filenames:
        if(id in filename):
            try:
                # https://github.com/dtcooper/python-fitparse send to user already parsed fit?
                return _corsify_actual_response(send_from_directory(login, filename))
            except:
                return _corsify_actual_response('No id found')


def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


@app.route("/parse_activities", methods=['GET'])
def parse_downloaded_activities():
    login = request.args['login']
    filenames: list = next(walk(login))[2]

    activities: list = []

    for filename in filenames:
        try:
            fitfile = fitparse.FitFile(login + "/" + filename)
            activity = {
                'file_name': filename,
                'sport_name': '-',
                'sport_type': -1
            }

            for message in fitfile.messages:
                if(message.name == 'sport'):
                    for field in message.fields:

                        if(field.name == 'name'):
                            print('name: ', field.raw_value)
                            activity['sport_name'] = field.raw_value

                        if(field.name == 'sport'):
                            print('type: ', field.raw_value)
                            activity['sport_type'] = field.raw_value

            fitfile.close()
            activities.append(activity)
        except:
            print('error parse .fit : ' + filename)

    return _corsify_actual_response(jsonify(activities))


app.run()
