# -*- coding: utf-8 -*-

from server.shops import Shops
from mock import mock_open, patch
import pytest as pyt
import uuid

class TestShops(object):
    def setUp(self):
        self.shops = Shops()

    def test_load_shops(self):
        shops = Shops()

        # test file does not exits
        with pyt.raises(IOError):
            shops.load_shops('/anypath')

        # test empty file
        m = mock_open(read_data='')
        with patch('server.shops.open', m, create=True):
            with pyt.raises(Exception):
                shops.load_shops('/anypath')
            m.assert_called_with('/anypath', 'r')

        # test happy case
        shop1 = { 'sid': 'sid1', 'name': 'Super Cool Shop', 'coords': (0.0, 0.0) }
        shop2 = { 'sid': 'sid2', 'name': 'Not as Cool Shop', 'coords': (10.0, 0.0) }
        shop3 = { 'sid': 'sid3', 'name': 'Lame Shop', 'coords': (0.0, 10.0) }

        file_data = self._shops_file_data([shop1, shop2, shop3])
        m = self._mock_open([file_data])
        with patch('server.shops.open', m, create=True):
            shops.load_shops('/anypath')

        # assert ids
        assert(shop1['sid'] in shops.shops)
        assert(shop2['sid'] in shops.shops)
        assert(shop3['sid'] in shops.shops)

        # assert names
        assert(shop1['name'] == shops.shops[shop1['sid']]['name'])
        assert(shop2['name'] == shops.shops[shop2['sid']]['name'])
        assert(shop3['name'] == shops.shops[shop3['sid']]['name'])

        # assert coords
        assert(shop1['coords'] == shops.shops[shop1['sid']]['coords'])
        assert(shop2['coords'] == shops.shops[shop2['sid']]['coords'])
        assert(shop3['coords'] == shops.shops[shop3['sid']]['coords'])

    def test_load_products(self):
        """ test loading products"""
        # this would be similar to test_load_shops
        pass

    def test_nearest(self):
        """ test nearest shops """

        # load test obj
        shops = Shops()
        shop1 = { 'sid': 'sid1', 'name': 'Super Cool Shop', 'coords': (59.33344130421325, 18.06072430751509), 'tags': set(['tag1']) }
        shop2 = { 'sid': 'sid2', 'name': 'Not as Cool Shop', 'coords': (59.33325394854872, 18.060152076730212), 'tags': set(['tag3']) }
        shop3 = { 'sid': 'sid3', 'name': 'Lame Shop', 'coords': (59.5, 18.6), 'tags': set(['tag1', 'tag2']) }

        file_data = self._shops_file_data([shop1, shop2, shop3])
        m = self._mock_open([file_data])
        with patch('server.shops.open', m, create=True):
            shops.load_shops('/anypath')

        # test distance
        nearby = shops.nearest(59.33344130421325, 18.06072430751509, distance=0.001)
        assert(len(nearby) == 1 and nearby[0][0] == shop1['sid'])
        nearby = shops.nearest(59.33344130421325, 18.06072430751509, distance=0.04)
        assert(len(nearby) == 2 and nearby[1][0] == shop2['sid'])
        nearby = shops.nearest(59.33344130421325, 18.06072430751509, distance=40)
        assert(len(nearby) == 3 and nearby[2][0] == shop3['sid'])

        # test tags
        tag_file_data, taggings_file_data = self._tags_taggings_file_data([shop1, shop2, shop3])
        m = self._mock_open([tag_file_data, taggings_file_data])
        with patch('server.shops.open', m, create=True):
            shops.load_tags('/anypath', '/anypath')

        nearby = shops.nearest(59.33344130421325, 18.06072430751509, distance=40, tags=['tag1'])
        assert(len(nearby) == 2)
        assert('tag1' in shops.shops[nearby[0][0]]['tags'])
        assert('tag1' in shops.shops[nearby[1][0]]['tags'])

        nearby = shops.nearest(59.33344130421325, 18.06072430751509, distance=40, tags=['tag3'])
        assert(len(nearby) == 1)
        assert('tag3' in shops.shops[nearby[0][0]]['tags'])

    def test_top_products(self):

        # load test obj
        shops = Shops()
        prods1 = [(1.0, {'pid': 'pid1', 'name': 'Much cool product', 'quantity': 1}),
                  (0.6, {'pid': 'pid2', 'name': 'An ok product', 'quantity': 1}),
                  (0.2, {'pid': 'pid3', 'name': 'Lame product', 'quantity': 10})]

        prods2 = [(0.9, {'pid': 'pid4', 'name': 'Super nice product', 'quantity': 1}),
                  (0.5, {'pid': 'pid5', 'name': 'Another regular product', 'quantity': 1})]

        shop1 = { 'sid': 'sid1', 'name': 'Super Cool Shop', 'coords': (0.0, 0.0), 'products': prods1 }
        shop2 = { 'sid': 'sid2', 'name': 'Not as Cool Shop', 'coords': (0.01, 0.01), 'products': prods2 }

        file_data = self._shops_file_data([shop1, shop2])
        m = self._mock_open([file_data])
        with patch('server.shops.open', m, create=True):
            shops.load_shops('/anypath')

        file_data = self._products_file_data([shop1, shop2])
        m = self._mock_open([file_data])
        with patch('server.shops.open', m, create=True):
            shops.load_products('/anypath')

        with patch("server.shops.Shops") as m:
            # mock the nearest method (we already tested that)
            m().nearest.return_value = [(shop1['sid'], 0.0), (shop2['sid'], 0.0)]

            # test order
            top_prods = shops.top_products(0.0, 0.0, distance=10)
            assert(len(top_prods) == 5)
            assert(top_prods == sorted(top_prods, key=lambda k: k['popularity'], reverse=True))

            # test limit
            top_prods = shops.top_products(0.0, 0.0, distance=10, limit=2)
            assert(len(top_prods) == 2)
            assert(top_prods[0]['pid'] == prods1[0][1]['pid'])
            assert(top_prods[1]['pid'] == prods2[0][1]['pid'])

    def _mock_open(self, file_datas):
        """ workaround for mock_open not working with iterators (http://bugs.python.org/issue21258) """

        mo = mock_open(read_data=file_datas[0])
        mo.return_value.__iter__ = lambda self : iter(self.readline, '')
        handlers = [mo.return_value]

        for file_data in file_datas[1:]:
            m = mock_open(read_data=file_data)
            m.return_value.__iter__ = lambda self : iter(self.readline, '')
            handlers.append(m.return_value)

        mo.side_effect = handlers
        return mo

    def _shops_file_data(self, shops):
        file_data = 'header\r\n'
        for shop in shops:
            file_data += '{},{},{},{}\r\n'.format(shop['sid'], shop['name'], shop['coords'][0], shop['coords'][1])

        return file_data

    def _tags_taggings_file_data(self, shops):
        tags_file_data = 'header\r\n'
        taggings_file_data = 'header\r\n'
        tags = {}
        for shop in shops:
            for tag_name in shop['tags']:
                if tag_name not in tags:
                    tid = str(uuid.uuid4())
                    tags[tag_name] = tid

                tid = tags[tag_name]
                taggings_file_data += 'anyid,{},{}\r\n'.format(shop['sid'], tid)

        for tag_name, tid in tags.iteritems():
            tags_file_data += '{},{}\r\n'.format(tid, tag_name)

        return tags_file_data, taggings_file_data

    def _products_file_data(self, shops):
        file_data = 'header\r\n'
        for shop in shops:
            for popularity, product in shop['products']:
                file_data += '{},{},{},{},{}\r\n'.format(product['pid'], shop['sid'], product['name'], popularity, product['quantity'])

        return file_data

