# QuickServe (Redplate): Real-Time Food Ordering and Administrative Control Portal

CpE 411 Data Structures and Algorithms final project, Group 9, Batangas State University.

## Run it

```
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 (students) and http://127.0.0.1:5000/admin/login (staff).
The database file `quickserve.db` is created automatically; delete it to start fresh.

## How it works

The canteen has several **shops**. A student signs in, picks a shop, and orders from that shop's
menu. A sidebar on the right of the shop page shows the student's cart and orders and updates
without reloading the page. Each shop's staff sign in with **their own shop password** and can
only see and change their own shop. The **canteen manager** adds shops: adding a shop also creates
its login at the same time.

| Who | Where | Default login |
|---|---|---|
| Student | `/` (school Google account) | demo mode asks for a school email |
| Shop staff | `/admin/login`, pick the shop | every sample shop starts with `shop123` |
| Canteen manager | `/admin/login`, pick Canteen manager | `admin` account, password `admin123` |

Change the defaults before a real pilot: set `QUICKSERVE_ADMIN_PASSWORD` and
`QUICKSERVE_SHOP_PASSWORD` before the first run, and the manager can change any shop's password.

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
| Hash Table | shops, menu lookup by item id, one cart per student per shop, cart quantities |
| Stack | the Undo button in the cart (also the BST traversal) |
| Queue | each shop's normal pending orders, first come first served |
| Min-Heap | each shop's urgent orders ("I have class soon"), served before its queue |
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
