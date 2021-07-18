from flask import Flask, Response, request, jsonify
from flask_sqlalchemy import SQLAlchemy, BaseQuery
from flask_migrate import Migrate
from pathlib import Path
from datetime import datetime
import json
from marshmallow import Schema, fields, validate, validates, ValidationError
from webargs.flaskparser import use_args
from werkzeug.datastructures import ImmutableDict
from config import Config


app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
db.create_all()


class Producer (db.Model):
    __tablename__ = 'producers'
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(50), nullable=False)
    headquarters = db.Column(db.String(50), nullable=False)
    creation_date = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f'<{self.__class__.__name__}>: {self.company_name}'

    @staticmethod
    def get_schema_args(fields: str) -> dict:
        schema_args = {'many': True}
        if fields:
            schema_args['only'] = [field for field in fields.split (',') if field in Producer.__table__.columns]
        return schema_args

    @staticmethod
    def apply_order(query: BaseQuery, sort_keys: str) -> BaseQuery:
        if sort_keys:
            for key in sort_keys.split(','):
                desc = False
                if key.startswith('-'):
                    key = key[1:]
                    desc = True
                column_attr = getattr(Producer, key, None)
                if column_attr is not None:
                    query = query.order_by(column_attr.desc()) if desc else query.order_by(column_attr)
        return query

    @staticmethod
    def apply_filter(query: BaseQuery, params: ImmutableDict) -> BaseQuery:
        for param, value in params.items():
            if param not in {'fields', 'sort'}:
                column_attr = getattr(Producer, param, None)
                if column_attr is not None:
                    if param == 'creation_date':
                        try:
                            value = datetime.strptime(value, '%d-%m-%Y').date()
                        except ValueError:
                            continue
                    query = query.filter(column_attr == value)
        return query


class ProducerSchema(Schema):
    id = fields.Integer(dump_only=True)
    company_name = fields.String(required=True, validate=validate.Length(max=50))
    headquarters = fields.String(required=True, validate=validate.Length(max=50))
    creation_date = fields.Date('%d-%m-%Y', required=True)


@validates('creation_date')
def validate_creation_date(self, value):
    if value > datetime.now().date():
        raise ValidationError(f'Creation date must be lower than {datetime.now().date()}')


producer_schema = ProducerSchema()


@app.route('/api/v1/producers', methods=['GET'])
def get_producers():
    query = Producer.query
    schema_args = Producer.get_schema_args(request.args.get('fields'))
    query = Producer.apply_order(query, request.args.get('sort'))
    query = Producer.apply_filter(query, request.args)
    producers = query.all()
    producer_schema = ProducerSchema(**schema_args)
    return jsonify({
        'success': True,
        'data': producer_schema.dump(producers),
        'number_of_records': len(producers)
    })


@app.route('/api/v1/producers/<int:producer_id>', methods=['GET'])
def get_producer(producer_id: int):
    producer = Producer.query.get_or_404(producer_id, description=f'Producer with id {producer_id} not found')
    return jsonify({
        'success': True,
        'data': producer_schema.dump(producer)
    })


@app.route('/api/v1/producers', methods=['POST'])
@use_args(producer_schema, error_status_code=400)
def create_producer(args: dict):
    producer = Producer(**args)

    db.session.add(producer)
    db.session.commit()

    return jsonify({
        'success': True,
        'data': producer_schema.dump(producer)
    }), 201


@app.route('/api/v1/producers/<int:producer_id>', methods=['PUT'])
@use_args(producer_schema, error_status_code=400)
def update_producer(args: dict, producer_id: int):
    producer = Producer.query.get_or_404(producer_id, description=f'Producer with id {producer_id} not found')

    producer.company_name = args['company_name']
    producer.headquarters = args['headquarters']
    producer.creation_date = args['creation_date']

    db.session.commit()

    return jsonify({
        'success': True,
        'data': producer_schema.dump(producer)
    })


@app.route('/api/v1/producers/<int:producer_id>', methods=['DELETE'])
def delete_producer(producer_id: int):
    producer = Producer.query.get_or_404(producer_id, description=f'Producer with id {producer_id} not found')

    db.session.delete(producer)
    db.session.commit()

    return jsonify({
        'success': True,
        'data': f'Producer with id {producer_id} has been deleted'
    })


@app.cli.group()
def db_manage():
    """Database management commands"""
    pass


@db_manage.command()
def add_data():
    """Add sample data to database"""
    try:
        producers_path = Path(__file__).parent / 'samples' / 'producers.json'
        with open(producers_path) as file:
            data_json = json.load(file)
        for item in data_json:
            item["creation_date"] = datetime.strptime(item['creation_date'], '%d-%m-%Y').date()
            producer = Producer(**item)
            db.session.add(producer)
        db.session.commit()
        print('Data has been successfully added to database')
    except Exception as exc:
        print("Unexpected error: {}".format(exc))


@db_manage.command()
def remove_data():
    """Remove all data from database"""
    try:
        db.session.execute('TRUNCATE TABLE producers')
        db.session.commit()
        print('Data has been successfully remove from database')
    except Exception as exc:
        print("Unexpected error: {}".format(exc))


# ERRORS

class ErrorResponse:
    def __init__(self, message: str, http_status: int):
        self.payload = {
            'success': False,
            'message': message
        }
        self.http_status = http_status

    def to_response(self) -> Response:
        response = jsonify(self.payload)
        response.static_code = self.http_status
        return response


@app.errorhandler(404)
def not_found_error(err):
    return ErrorResponse(err.description, 404).to_response()


@app.errorhandler(400)
def bad_request_error(err):
    messages = err.data.get('messages', {}.get('json', {}))
    return ErrorResponse(messages, 400).to_response()


@app.errorhandler(415)
def unsupported_media_type_error(err):
    return ErrorResponse(err.description, 415).to_response()


@app.errorhandler(500)
def internal_server_error(err):
    db.session.rollback()
    return ErrorResponse(err.description, 500).to_response()
