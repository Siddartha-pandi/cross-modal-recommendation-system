# Platzi Fake Store API (Postman + cURL)

## Postman collection import

1. Install Postman: https://www.postman.com/downloads/
2. Download the collection JSON:
   - https://fakeapi.platzi.com/json/postman.json
3. Open Postman and click Import.
4. Select the downloaded JSON file.
5. In the collection variables or environment, set:
   - API_URL = https://api.escuelajs.co

You can now run the requests in the collection.

## cURL examples

Base URL: https://api.escuelajs.co/api/v1

List products:

```bash
curl -s "https://api.escuelajs.co/api/v1/products"
```

List products with pagination:

```bash
curl -s "https://api.escuelajs.co/api/v1/products?limit=10&offset=0"
```

Get a single product:

```bash
curl -s "https://api.escuelajs.co/api/v1/products/1"
```

List categories:

```bash
curl -s "https://api.escuelajs.co/api/v1/categories"
```

Search products by title (client-side filter):

```bash
curl -s "https://api.escuelajs.co/api/v1/products" | findstr /I "shirt"
```

Notes:
- The API is public and does not require auth.
- For more endpoints, open the Postman collection and review available requests.
