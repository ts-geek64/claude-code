# Shopify Synchronization Pipeline

Python pipeline for syncing Shopify customers and orders to PostgreSQL using GraphQL API. This service is designed to be deployed as a Google Cloud Function.

## Features

- **Multi-Tenant Support**: Dynamic tenant context handling via `tenant_id`
- **Incremental Sync**: Cursor-based pagination for efficient updates
- **On-Demand Sync**: Support for syncing specific integrations via `integration_ids`
- **Batch Processing**: Explicit transactions with batched database writes
- **Rate Limit Handling**: Smart exponential backoff for Shopify API limits
- **Security**: Fernet encryption for sensitive tokens
- **Robust Architecture**: Connection pooling, comprehensive error handling, and structured logging

## Architecture

```
project_root/
├── config/
│   └── settings.py           # Configuration management
├── src/
│   ├── database/
│   │   ├── database_context.py       # Connection pool manager
│   │   └── repositories/
│   │       ├── integration_repository.py
│   │       ├── customer_repository.py
│   │       └── order_repository.py
│   ├── data_processor/
│   │   └── processor.py      # GraphQL response normalizer
│   ├── services/
│   │   ├── customer_sync_service.py
│   │   ├── order_sync_service.py
│   │   └── sync_orchestrator.py
│   ├── utils/
│   │   ├── encryption.py     # Token encryption
│   │   └── tenant_context.py # Tenant context management
│   └── http.py               # HTTP client with retry
├── main.py                   # Cloud Function entry point
└── requirements.txt
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and update values:

```bash
cp .env.example .env
```

**Required Variables**:

- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- `FERNET_KEY`: Generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`

### 3. Database Setup

Ensure your PostgreSQL database has the required schema. The system supports multi-tenancy, so ensure tenant-specific tables (if applicable) or identifiers are in place.

## Running Locally

Since this project uses `functions-framework`, run it using the following command:

```bash
functions-framework --target=sync_shopify --port=8080
```

The service will start on `http://localhost:8080`.

## Usage & Triggering

The function expects a JSON payload via HTTP POST.

### 1. Sync All Integrations for a Tenant

```bash
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "your-tenant-id"
  }'
```

### 2. Sync Specific Integrations

```bash
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "your-tenant-id",
    "integration_ids": [
      "123e4567-e89b-12d3-a456-426614174000",
      "987fcdeb-51a2-43d7-9012-345678901234"
    ]
  }'
```

### Response Format

**Success Response:**

```json
{
  "status": "success",
  "total_integrations": 2,
  "successful": 2,
  "failed": 0,
  "results": [
    {
      "status": "success",
      "integration_id": "123e4567-e89b-12d3-a456-426614174000",
      "shop_name": "My Store",
      "customers_synced": 150,
      "orders_synced": 320
    }
  ]
}
```

**Error Response:**

```json
{
  "status": "error",
  "code": "ERR_MISSING_TENANT",
  "message": "tenant_id is required in request body"
}
```

## Configuration Reference

| Variable                  | Default   | Description                      |
| ------------------------- | --------- | -------------------------------- |
| `DB_HOST`                 | localhost | Database host                    |
| `DB_POOL_MIN`             | 2         | Min connection pool size         |
| `DB_POOL_MAX`             | 10        | Max connection pool size         |
| `SHOPIFY_BATCH_SIZE`      | 250       | Records per page (batch)         |
| `SHOPIFY_REQUEST_TIMEOUT` | 30        | Request timeout (seconds)        |
| `MAX_RETRIES`             | 3         | Max retry attempts for API calls |
| `LOG_LEVEL`               | INFO      | Logging level                    |

## Troubleshooting

### "ERR_MISSING_TENANT"

The `tenant_id` field is mandatory in the request body. Make sure you are sending a valid JSON payload with this field.

### "Invalid Fernet key"

Ensure `FERNET_KEY` in `.env` matches the key used to encrypt the tokens in the database.

### "Health check failed"

- Verify the Shopify access token in the database is valid.
- Ensure the Shopify store is active.

## Deployment

Deploy to Google Cloud Functions (2nd Gen recommended):

```bash
gcloud functions deploy sync-shopify \
  --gen2 \
  --runtime=python310 \
  --region=us-central1 \
  --source=. \
  --entry-point=sync_shopify \
  --trigger-http
```
