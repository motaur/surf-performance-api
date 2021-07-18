import time
import flask
from flask import request, jsonify, send_from_directory
import fitparse
import json
from json import JSONEncoder
import datetime
from garminexport.garminclient import GarminClient
from garminexport.incremental_backup import incremental_backup
import os
from os import listdir, walk
from os.path import isfile, join
import json

app = flask.Flask(__name__)
app.config["DEBUG"] = True


@app.after_request
def allow_cross_domain(response: flask.Response):
    """Hook to set up response headers."""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'content-type'
    return response


@app.route('/backup', methods=['POST'])
def garmin_backup():
    login = request.json['login']
    password = request.json['password']
    activities: set = incremental_backup(username=login, password=password, backup_dir=os.path.join('.', 'activities/' + login),
                                         export_formats=['fit'], ignore_errors=True)

    if(activities.__len__ != 0):
        parse_downloaded_activities()

    return corsify_response(jsonify(activities))
# incremental backup then parse


@app.route("/get_activities_parsed", methods=['GET'])
def get_activities_parsed():
    login = request.args['login']
    return corsify_response(send_from_directory('activities/' + login, 'activities.json'))


@app.route("/get_activity_file", methods=['GET'])
def get_activity_file():
    login = request.args['login']
    id = request.args['id']
    filenames: list = next(walk('activities/' + login))[2]

    for filename in filenames:
        if(id in filename[26:36]):
            try:
                # https://github.com/dtcooper/python-fitparse send to user already parsed fit?
                return corsify_response(send_from_directory('activities/' + login, filename))
            except:
                return corsify_response('No id found')


def corsify_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


@app.route("/parse_activities", methods=['GET'])
def parse_downloaded_activities():
    login = request.args['login']
    filenames: list = next(walk('activities/' + login))[2]

    activities: list = []

    for filename in filenames:
        try:
            fitfile = fitparse.FitFile(
                'activities/' + login + '/' + filename)
            activity = {
                'id': filename[26:36],
                'file_size_bytes': fitfile._filesize,
                'date_time': fitfile.messages[0].get_values()['time_created'].strftime("%c")
            }

            # for i in range(5, 20):
            #     sport_message = fitfile.messages[i]
            #     if(sport_message.name == 'sport'):
            #         activity['sport_name'] = sport_message.get_values()['name']
            #         activity['sport_type'] = sport_message.get_values()[
            #             'sport']

            for message in fitfile.messages:
                if(message.name == 'sport'):
                    for field in message.fields:
                        if(field.name == 'name'):
                            activity['sport_name'] = field.raw_value

                        if(field.name == 'sport'):
                            activity['sport_type'] = field.value

            fitfile.close()
            print(filename, 'parsed succesfully')
            activities.append(activity)
        except:
            print('error parse : ' + filename)
    f = open('activities/' + login + "/activities.json", "w")
    f.write(json.dumps(activities))
    f.close()
    return corsify_response(send_from_directory('activities/' + login, 'activities.json'))


app.run()
