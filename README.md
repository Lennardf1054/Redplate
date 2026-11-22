# QuickServe (Redplate): Real-Time Food Ordering and Administrative Control Portal

CpE 411 Data Structures and Algorithms final project, Group 9, Batangas State University.

## Run it

```
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 (students) and http://127.0.0.1:5000/admin/login (staff).
Default staff account: `admin` / `admin123` (set `QUICKSERVE_ADMIN_USER` and
`QUICKSERVE_ADMIN_PASSWORD` before the first run to use something else).
The database file `quickserve.db` is created automatically; delete it to start fresh.

## Student sign-in (school Google account)

Students sign in with a `@g.batstate-u.edu.ph` Google account. Only the email is kept, so a
student can see their own orders. Nothing is stored about names or phone numbers.

Without any setup the site starts in **demo mode**: the login page asks for a school email and
accepts it without Google. To use real Google sign-in, create an OAuth client in Google Cloud
Console (type: Web application) with these redirect URIs:

```
http://127.0.0.1:5000/auth/google/callback
http://localhost:5000/auth/google/callback
```

then set these in the same PowerShell window before `python app.py` (never put them in a file
that is shared or committed):

```
$env:QUICKSERVE_GOOGLE_CLIENT_ID = "your-client-id"
$env:QUICKSERVE_GOOGLE_CLIENT_SECRET = "your-client-secret"
$env:QUICKSERVE_ALLOWED_DOMAIN = "g.batstate-u.edu.ph"
```

When the client ID and secret are set, demo mode switches off by itself
(`QUICKSERVE_DEMO_LOGIN=1` turns it back on).

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
