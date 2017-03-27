#!flask/bin/python

from flask import (
    Flask,
    jsonify,
    make_response)
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource


app = Flask(__name__)
api = Api(app)
URI = 'postgresql://gonzalorivero@localhost:5432/pdb'
app.config['SQLALCHEMY_DATABASE_URI'] = URI
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


class PdbBlockgroup(Resource):
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
        try:
            datalist = []
            for i in lrs:
                data = {"state": i.State_name,
                        "county": i.County_name,
                        "tract": i.Tract,
                        "blockgroup": i.Block_Group,
                        "score": i.Low_Response_Score}
                datalist.append(data)
            res = {"data": datalist,
                   "response": 200}
        except:
            res = {"error": {"message": "Not found"},
                   "response": 404}
        return(jsonify(res))


api.add_resource(
    PdbBlockgroup,
    '/minipdb',
    '/minipdb/<state>/',
    '/minipdb/<state>/<county>/',
    '/minipdb/<state>/<county>/<tract>/',
    '/minipdb/<state>/<county>/<tract>/<blockgroup>'
)

if __name__ == '__main__':
    app.run(debug=True)
