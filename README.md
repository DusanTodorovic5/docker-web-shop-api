# Web Shop API in Python using Docker

Web shop API made in Python Flask using Docker Swarm. [How to run](#Runing-the-server).

There are 3 types of accounts
 - admin
 - customer
 - storekeeper

## Admin
Admin can check statistics for given category or product. Admin can also delete the user from database.

## Customer
Customer has the ability to search for product, order the product and check the status of order.

## Storekeeper
Storekeeper can upload a file containing new products, thus adding products to database. Before the products are added to the database, they are sent to redis where daemon checks each product and updates the product if it exists or creates new product. Daemon then checks if there are unfulfilled orders waiting for added product, if there are some, daemon ads the product to their order.

## Requests

 - Authentication - Running on port 5000
    - /register [POST] - 
        Request example:
        ```json
        {
            "forename": ".....",
            "surname": ".....",
            "email": ".....",
            "password": ".....",
            "isCustomer": True
        }
        ```
    - /login [POST] - Request example:
        ```json
        {
        "email": ".....",
        "password": "....."
        }
        ```
    - /refresh [POST] - Request example:
        ```json
        {
        "Authorization": "Bearer <REFRESH_TOKEN>"
        }
        ```
    - delete [POST] - Request example:
        ```json
        {
            "email": "....."
        }
        ```
 - Storekeeper - Running on port 5001
    - /update [POST] - Request contains [file like this](https://github.com/DusanTodorovic5/docker-web-shop-api/blob/main/application/testing/temp.csv)
 - Daemon - Collecting updates from storekeeper in redis and updates database
 - Customer - Running on port 5003
    - /search?name=<PRODUCT_NAME>&category=<CATEGORY_NAME> [GET]
    - /order [POST] - Request example:
        ```json
        {
            "requests": [
                {
                    "id": 1,
                    "quantity":2
                },
                {
                    "id": 2,
                    "quantity":3
                }
            ]
        }
        ```
    - /status [GET]
 - Admin - Running on port 5004
    - /productStatistics [GET]
    - /categoryStatistics [GET]


# Runing the server

In order to run this web server, you will need docker. Create images from dockerfiles and run the following command in ``cmd/powershell`` or ``terminal``
```bash
docker swarm init --advertise-addr 127.0.0.1
docker stack deploy --compose-file <path_to_stack.yaml> <name_of_server>
```
In order to check if all the containers are running
```
docker service ls
```
In order to close the swarm
```bash
docker swarm leave --force
```

Database can be checked using adminer on ``localhost:8080`` adress.
Tests can be run with the following command in ``cmd/powershell`` or ``terminal``
```bash
python main.py --type all --with-authentication --authentication-address http://127.0.0.1:5000 --jwt-secret JWTSecretDevKey --roles-field roles --administrator-role 1 --customer-role 2 --warehouse-role 3 --customer-address http://127.0.0.1:5001 --warehouse-address http://127.0.0.1:5002 --administrator-address http://127.0.0.1:5003
```
For the specific test, you can run following commands
- Authentication test
```bash
python main.py --type authentication --authentication-address http://127.0.0.1:5000 --jwt-secret JWTSecretDevKey --roles-field roles --administrator-role 1 --customer-role 2 --warehouse-role 3
```
- Level 0 test
```bash
python main.py --type level0 --with-authentication --authentication-address http://127.0.0.1:5000 --customer-address http://127.0.0.1:5001 --warehouse-address http://127.0.0.1:5002
```
- Level 1 test
```bash
python main.py --type level1 --with-authentication --authentication-address http://127.0.0.1:5000 --customer-address http://127.0.0.1:5001 --warehouse-address http://127.0.0.1:5002
```
- Level 2 test
```bash
python main.py --type level2 --with-authentication --authentication-address http://127.0.0.1:5000 --customer-address http://127.0.0.1:5001 --warehouse-address http://127.0.0.1:5002
```
- Level 3 test
```bash
python main.py --type level3 --with-authentication --authentication-address http://127.0.0.1:5000 --customer-address http://127.0.0.1:5001 --warehouse-address http://127.0.0.1:5002 --administrator-address http://127.0.0.1:5003
```
