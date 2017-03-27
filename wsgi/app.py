#!flask/bin/python

from flask import (
    Flask,
    make_response)
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource


app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://gonzalorivero@localhost:5432/pdb'
db = SQLAlchemy(app)


class Pdb(db.Model):
    GIDBG = db.Column(db.Integer, primary_key=True)
    State = db.Column(db.Integer)
    State_name = db.Column(db.String(60))
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
        
    def get(self, bgid):
        lrs = Pdb.query.filter_by(username=bgid).first_or_404()
        return(make_response(lrs))

api.add_resource(PdbBlockgroup, '/minipdb/blockgroup')

if __name__ == '__main__':
    app.run(debug=True)
