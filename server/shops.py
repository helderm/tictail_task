# -*- coding: utf-8 -*-

from scipy.spatial import KDTree
import numpy as np
from copy import copy

class Shops(object):

    def __init__(self):
        self.shops = {}
        self.idxs2sids = {}

        self.kdtree = None
        self.coords = []

    def load(self, data_path):
        """ loads shop info """

        assert(len(self.shops) == 0)

        shops_path = data_path('shops.csv')
        products_path = data_path('products.csv')
        tags_path = data_path('tags.csv')
        taggings_path = data_path('taggings.csv')

        # load shops
        with open(shops_path, 'r') as f:
            for idx, line in enumerate(f):
                # skip header line
                if idx == 0:
                    continue

                # split the line record
                aux = line.rstrip().split(',')
                sid = aux[0]
                lat = float(aux[-2])
                lon = float(aux[-1])
                name = ','.join(aux[1:-2])

                # separate the coords struct as to build the KDTree
                self.coords.append(self._to_cartesian(lat, lon))

                # store the shop object
                shop = { 'name': name, 'sid': sid, 'products': [],
                            'tags': set(), 'coords': (lat, lon) }
                self.shops[sid] = shop

                # store the coord_idx to store_id mapping
                self.idxs2sids[idx-1] = sid

        self.kdtree = KDTree(self.coords)

        # load products
        with open(products_path, 'r') as f:
            for idx, line in enumerate(f):
                if idx == 0:
                    continue

                # split the line record
                aux = line.rstrip().split(',')
                pid = aux[0]
                sid = aux[1]
                quantity = int(aux[-1])
                popularity = float(aux[-2])
                name = ','.join(aux[2:-2])

                assert(sid in self.shops)

                product = { 'pid': pid, 'quantity': quantity,
                            'name': name }

                # insert products in increasing order of popularity
                shop = self.shops[sid]
                self._reverse_insort(shop['products'], (popularity, product))

        # load tags
        tags = {}
        with open(tags_path, 'r') as f:
            for idx, line in enumerate(f):
                if idx == 0:
                    continue

                # split the line record
                aux = line.rstrip().split(',')
                tid = aux[0]
                name = aux[1]

                tags[tid] = name

        # load tagging
        with open(taggings_path, 'r') as f:
            for idx, line in enumerate(f):
                if idx == 0:
                    continue

                # split the line record
                aux = line.rstrip().split(',')
                tid = aux[2]
                sid = aux[1]

                assert(sid in self.shops and tid in tags)

                # add the tags to the set of tags of the shop
                name = tags[tid]
                shop = self.shops[sid]
                shop['tags'].add(name)

        return self

    def get(self, shop_ids):
        """ returns a copy of the shops info for each shop id available """

        res = []
        fetched_shops = [ self.shops[sid] for sid in shop_ids ]
        for fetched_shop in fetched_shops:
            shop = copy(fetched_shop)

            # transforms set into list for later json serialization
            shop['tags'] = list(shop['tags'])

            # removes products, leave only basic shop info
            del shop['products']

            res.append(shop)

        return res

    def nearest(self, lat, lon, limit=100, distance=10, tags=None):
        """ returns the `num` nearest shop ids at maximum of `distance` km """
        assert(self.kdtree != None)

        # query the kdtree for the nearest shops around lat/lon
        dists, idxs = self.kdtree.query(self._to_cartesian(lat, lon), k=limit,
                        distance_upper_bound=distance)

        # create the shop_ids list together with its distance
        sids = [ (self.idxs2sids[idx], dist) for idx, dist in zip(idxs, dists) if idx in self.idxs2sids ]

        if not tags or len(tags) == 0:
            return sids

        # filter shops out by tags
        user_tags = set(tags)
        sids = [ (sid, dist) for sid, dist in sids if not self.shops[sid]['tags'].isdisjoint(user_tags) ]

        return sids

    def top_products(self, lat, lon, distance, limit=0, tags=None):
        """ returns a list of the most popular products from shops aroud the area """

        # fetch the nearest shops
        shops_nearby = self.nearest(lat, lon, distance=distance, tags=tags)

        # fetch the k sorted lists of products
        lists = [ (sid, self.shops[sid]['products']) for sid, _ in shops_nearby ]

        # merge the products in order of popularity
        return self._merge_products_lists(lists, limit=limit)

    def _to_cartesian(self, lat, lon):
        """ convert a lat / lon coordinates from degrees to cartesian """
        # convert coordinates to radians
        lat_rad = lat * 2*np.pi / 360
        lon_rad = lon * 2*np.pi / 360

        # convert to cartesian (ECEF = earth-centered, earth-fixed)
        R = 6367 # radius of Earth
        x = R * np.cos(lat_rad) * np.cos(lon_rad)
        y = R * np.cos(lat_rad) * np.sin(lon_rad)
        z = R * np.sin(lat_rad)

        return [x, y, z]

    def _reverse_insort(self, a, x, lo=0, hi=None):
        """ insert item x in list a, and keep it reverse-sorted assuming a
        is reverse-sorted.

        borrowed from python's `bisect` module
        """
        if lo < 0:
            raise ValueError('lo must be non-negative')
        if hi is None:
            hi = len(a)
        while lo < hi:
            mid = (lo+hi)//2
            if x > a[mid]: hi = mid
            else: lo = mid+1
        a.insert(lo, x)

    def _merge_products_lists(self, lists, limit=0):
        """ merge k sorted lists together """

        res = []
        heap = []

        # store the top product from each list
        for sid, products in lists:
            if products:
                top = products[0][1]
                popularity = products[0][0]
                self._reverse_insort(heap, (popularity, top, sid, products[1:]))

        while heap:
            # pop the top product from all lists
            largest = heap[0]
            product = largest[1]
            sid = largest[2]
            product['popularity'] = largest[0]
            product['sid'] = sid
            res.append(product)

            if limit and len(res) >= limit:
                break

            heap = heap[1:]
            # push the next top element of this list back to the heap
            if largest[3]:
                products = largest[3]
                top = products[0][1]
                popularity = products[0][0]

                self._reverse_insort(heap, (popularity, top, sid, products[1:]))

        return res

