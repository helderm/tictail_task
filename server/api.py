# -*- coding: utf-8 -*-

from flask import Blueprint, current_app, jsonify

from shops import Shops

api = Blueprint('api', __name__)


def data_path(filename):
    data_path = current_app.config['DATA_PATH']
    return u"%s/%s" % (data_path, filename)


@api.route('/search', methods=['GET'])
def search():
    # lazily loads the data structures
    #  ideally this would be performed as a background task on init

    import pudb
    pu.db

    shops = Shops().load(data_path)
    products = shops.top_products(59.3330310094364,18.05724498771984, distance=0.02, tags=None)

    shop_ids = set([ product['sid'] for product in products ])
    shops_in_products = shops.get(shop_ids)
    return jsonify({'products': products, 'shops': shops_in_products})
