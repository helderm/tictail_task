# -*- coding: utf-8 -*-

from flask import Blueprint, current_app, jsonify, request
from werkzeug.exceptions import BadRequest
from shops import Shops

api = Blueprint('api', __name__)


def data_path(filename):
    data_path = current_app.config['DATA_PATH']
    return u"%s/%s" % (data_path, filename)


@api.route('/search', methods=['GET'])
def search():
    args = fetch_and_validate_args()

    shops = Shops().load(data_path)

    # fetch the top products around the area
    products = shops.top_products(args.lat, args.lon, distance=args.dist/1000.0, tags=args.tags, limit=args.limit)

    # fetch the shop info for all shops in the products list
    shop_ids = set([ product['sid'] for product in products ])
    shops_in_products = shops.get(shop_ids)
    return jsonify({'products': products, 'shops': shops_in_products})


def fetch_and_validate_args():
    """ fetch args from query string and validate its values """

    class objectview(object):
        def __init__(self, d):
            self.__dict__ = d

    args = {}
    try:
        args['lat'] = float(request.args['lat'])
        args['lon'] = float(request.args['lon'])

        if args['lat'] > 90.0 or args['lat'] < -90.0 \
            or args['lon'] > 180.0 or args['lon'] < -180.0:

            raise ValueError()

    except (KeyError, ValueError):
        raise BadRequest(description='"lat" and "lon" keys are required and must be float values between valid ranges')

    try:
        args['dist'] = int(request.args.get('dist', default=500))
        args['limit'] = int(request.args.get('limit', default=0))

        if args['dist'] < 0 or args['limit'] < 0:
            raise ValueError()

    except ValueError:
        raise BadRequest(description='"dist" and "limit" keys must be positive integer values')

    args['tags'] = request.args.getlist('tag')
    if not all(isinstance(item, unicode) for item in args['tags']):
        raise BadRequest(description='All "tag" keys must be string values')

    return objectview(args)

