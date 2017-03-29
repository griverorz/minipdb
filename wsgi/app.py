#!flask/bin/python

from flask import (
    Flask,
    request)
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource
from datetime import datetime
from config import Config, Prod
from marshmallow import (
    Schema,
    fields,
    post_load,
    validates_schema,
    ValidationError)


class RequestSchema(Schema):
    state = fields.Integer(required=True,
                           error_messages={'required': "State is required"})
    county = fields.Integer()
    tract = fields.Integer()
    blockgroup = fields.Integer()

    @post_load
    def make_object(self, data):
        if "blockgroup" in data:
            if "tract" not in data:
                raise ValidationError("Schema not nested")
        if "tract" in data:
            if "county" not in data:
                raise ValidationError("Schema not nested")
        return(data)

    @validates_schema(pass_original=True)
    def check_unknown_fields(self, data, original_data):
        unknown = set(original_data) - set(self.fields)
        if unknown:
            raise ValidationError('Unknown field', unknown)


app = Flask(__name__)
api = Api(app)
app.config.from_object('config.Config')
URISTR = 'postgresql://{dbuser}@{dbhost}:{dbport}/{dbname}'
URI = URISTR.format(dbuser=Config.DBUSER,
                    dbhost=Config.DBHOST,
                    dbport=Config.DBPORT,
                    dbname=Config.DBNAME)
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


def build_query(state, county=None, tract=None, blockgroup=None):
    queries = [Pdb.State == state]
    if county is not None:
        queries.append(Pdb.County == county)
        if tract is not None:
            queries.append(Pdb.Tract == tract)
            if blockgroup is not None:
                queries.append(Pdb.Block_Group == blockgroup)
    res = Pdb.query.filter(*queries).all()
    return(res)


def parse_results(data):
    res = [{"state": i.State_name,
            "state_id": i.State,
            "county": i.County_name,
            "county_id": i.County,
            "tract": i.Tract,
            "blockgroup": i.Block_Group,
            "score": i.Low_Response_Score/100 if i.Low_Response_Score else None}
           for i in data]
    return(res)
        

def process_query(data):
    lrs = build_query(**data)
    if lrs:
        query_res = parse_results(lrs)
        res = {"data": query_res,
               "version": "v2015-07-28",
               "timestamp": str(datetime.now())}
        statuscode = 200
    else:
        res = {"error":
               {"message": "Resource {} not found".format(data)},
               "timestamp": str(datetime.now())}
        statuscode = 404
    return(res, statuscode)


class PdbLRS(Resource):
    def __init__(self):
        self.headers = {'Content-Type': 'text/html'}

    def post(self):
        try:
            inputdata = request.get_json()
        except:
            res = {"error": {"message": "Malformed request"},
                   "timestamp": str(datetime.now())}
            statuscode = 400
            return(res, statuscode)
        try:
            data = RequestSchema(strict=True).load(inputdata).data
        except ValidationError as e:
            res = {"error": {"message": str(e)},
                   "timestamp": str(datetime.now())}
            statuscode = 400
            return(res, statuscode)
        res, statuscode = process_query(data)
        return(res, statuscode)

api.add_resource(PdbLRS, '/minipdb')


if __name__ == '__main__':
    app.run(debug=Config.DEBUG)
