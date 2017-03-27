#!flask/bin/python

from flask import (
    Flask,
    jsonify)
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource
from datetime import datetime

app = Flask(__name__)
api = Api(app)
URI = 'postgresql://gonzalorivero@localhost:5432/pdb'
app.config['SQLALCHEMY_DATABASE_URI'] = URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)


class Pdb(db.Model):
    GIDBG = db.Column(db.Integer, primary_key=True)
    State = db.Column(db.Integer)
    State_name = db.Column(db.String(60))
    County = db.Column(db.Integer)
    County_name = db.Column(db.String(120))
    Tract = db.Column(db.Integer)
    Block_Group = db.Column(db.Integer)
    Low_Response_Score = db.Column(db.Float)

    def __init__(self, GIDBG):
        self.GIDBG = GIDBG

    def __repr__(self):
        return '<Pdb %r>' % self.GIDBG


class PdbLRS(Resource):
    def __init__(self):
        self.headers = {'Content-Type': 'text/html'}

    def get(self, state, county=None, tract=None, blockgroup=None):
        queries = [Pdb.State == state]
        if county is not None:
            queries.append(Pdb.County == county)
            if tract is not None:
                queries.append(Pdb.Tract == tract)
                if blockgroup is not None:
                    queries.append(Pdb.Block_Group == blockgroup)
        lrs = (Pdb.query.
               filter(*queries).
               all())
        if lrs:
            datalist = []
            for i in lrs:
                data = {"state": i.State_name,
                        "state_id": i.State,
                        "county": i.County_name,
                        "county_id": i.County,
                        "tract": i.Tract,
                        "blockgroup": i.Block_Group,
                        "score": i.Low_Response_Score/100 if i.Low_Response_Score else None}
                datalist.append(data)
            res = {"data": datalist,
                   "response": 200,
                   "version": "v2015-07-28",
                   "timestamp": datetime.now()}
        else:
            attempt = {'state': state,
                       'county': county,
                       'tract': tract,
                       'blockgroup': blockgroup}
            res = {"error": {"message": "Resource {} not found".format(attempt)},
                   "response": 404,
                   "timestamp": datetime.now()}
        return(jsonify(res))


api.add_resource(
    PdbLRS,
    '/minipdb/<state>/',
    '/minipdb/<state>/<county>/',
    '/minipdb/<state>/<county>/<tract>/',
    '/minipdb/<state>/<county>/<tract>/<blockgroup>')


if __name__ == '__main__':
    app.run(debug=True)
