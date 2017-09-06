### Solution Details
* To find the top products around an area, I first find the **shops** near the requested area, and then **join** the products of each shop in descending order of popularity 
* I make use of [K-d trees](https://en.wikipedia.org/wiki/K-d_tree) for storing the coordinates of shops and to search the nearest neighbors.  
  * O(log n) for search
* Then I do a [K-way merge](https://en.wikipedia.org/wiki/K-Way_Merge_Algorithms) between the sorted product lists to generate the result by using a heap-like structure  
  * O(n log k) time complexity
* The [Shops](https://github.com/helderm/tictail_task/blob/master/server/shops.py) class stores the shops information and the two main methods of this task  
  * `nearest()` returns the nearest shops around a latitude/longitude, filtering by tags
  * `top_products()` returns the top products around an area
* A sample of a shop object follows:
```python 
{'name': 'Super Cool Shop',  
'sid': 'sid1',  
'coords': (0.0, 0.0),  
'tags': set(['kids']),  
'products': [(1.0, {'pid': 'pid1', 'name': 'Much cool product', 'quantity': 1}),  
             (0.6, {'pid': 'pid2', 'name': 'An ok product', 'quantity': 1})]}
```
