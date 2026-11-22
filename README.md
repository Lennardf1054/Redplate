# QuickServe (Redplate): Real-Time Food Ordering and Administrative Control Portal

CpE 411 Data Structures and Algorithms final project, Group 9, Batangas State University.

## Run it

```
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 (customers) and http://127.0.0.1:5000/admin/login (staff).
Default staff account: `admin` / `admin123` (set `QUICKSERVE_ADMIN_USER` and
`QUICKSERVE_ADMIN_PASSWORD` before the first run to use something else).
The database file `quickserve.db` is created automatically; delete it to start fresh.

## Where each data structure and algorithm is used (Back_End/service.py)

| Piece | Used for |
|---|---|
| Hash Table | menu lookup by item id, one cart per browser session, cart quantities |
| Stack | the Undo button in the cart (also the BST traversal) |
| Queue | normal pending orders, first come first served |
| Min-Heap | urgent orders ("I have class soon"), served before the queue |
| Binary Search Tree | record store of every order; sorted traversal |
| Binary search | finding an order by number in the sorted order list |
| Merge sort | menu sort, cart display, sales report |
| Linear search, bubble sort | only compared in benchmark.py |

The database only saves data. The structures live in memory and are loaded at startup.

## Tests and benchmark (run from this folder)

```
python -m tests.test_queue
python -m tests.test_stack
python -m tests.test_heap
python -m tests.test_hash_table
python -m tests.test_bst
python -m tests.test_algorithms
python -m tests.test_database
python -m tests.test_service
python -m tests.test_app
python benchmark.py
```
