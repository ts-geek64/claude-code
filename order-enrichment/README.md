# Order Enrichment Cron Job

This Cloud Function processes order data from Neo4j, enriches it with attribution sources and UTM parameters, and stores the results in PostgreSQL.

## Features

- Fetches online orders from Neo4j database
- Resolves JWT-encoded landing pages
- Detects attribution sources (Meta, Google, Klaviyo, Snapchat, etc.)
- Extracts UTM parameters and campaign data
- Stores enriched data in PostgreSQL with tenant isolation
- Supports batch processing for performance
- Multi-tenant architecture with proper context isolation

## Architecture

```
order-enrichment/
├── main.py                    # Cloud Function entry point
├── src/
│   ├── http.py               # HTTP request handler
│   ├── config/settings.py    # Configuration management
│   ├── database/
│   │   ├── database_context.py       # PostgreSQL connection pool
│   │   └── repositories/
│   │       ├── neo4j_repository.py   # Neo4j data access
│   │       └── enrichment_repository.py # PostgreSQL data storage
│   ├── services/
│   │   └── enrichment_service.py     # Main orchestrator
│   ├── data_processor/
│   │   └── enrichment_processor.py   # Core enrichment logic
│   └── utils/
│       ├── tenant_context.py         # Multi-tenant context
│       └── logger.py                # Logging setup
├── scripts/deploy.sh         # Deployment script
├── requirements.txt          # Python dependencies
└── .env.example             # Environment variables template
```

## Setup

1. **Environment Variables**: Copy `.env.example` to `.env` and fill in your values:
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials and settings
   ```

2. **Dependencies**: Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. **Deploy**: Run the deployment script:
   ```bash
   ./scripts/deploy.sh
   ```

## API Usage

### Enrich Orders by Month
```bash
curl -X POST "https://REGION-PROJECT.cloudfunctions.net/order-enrichment" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "au_vodka",
    "year": 2025,
    "month": 9
  }'
```

### Enrich Orders by Date Range
```bash
curl -X POST "https://REGION-PROJECT.cloudfunctions.net/order-enrichment" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "au_vodka",
    "start_date": "2025-09-01T00:00:00-04:00",
    "end_date": "2025-09-30T23:59:59-04:00"
  }'
```

### Get Statistics
```bash
curl -X POST "https://REGION-PROJECT.cloudfunctions.net/order-enrichment" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "au_vodka",
    "action": "stats"
  }'
```

## Supported Tenants

- `au_vodka` (prefix: `au`)
- `milam_and_greene` (prefix: `milam`) 
- `omnigrowthos` (prefix: `omnigrowthos`)

## Attribution Sources Detected

- **Meta**: Facebook, Instagram campaigns
- **Google**: Google Ads, Search campaigns
- **Klaviyo**: Email campaigns
- **Snapchat**: Snapchat Ads
- **TikTok**: TikTok Ads
- **Pinterest**: Pinterest Ads
- **Bing**: Microsoft Advertising
- **Klarna**: Klarna campaigns
- **Shop Pay**: Shopify Shop Pay

## Data Flow

1. **Fetch**: Retrieve orders from Neo4j based on date criteria
2. **Process**: For each order:
   - Decode JWT landing pages if present
   - Detect attribution sources from URL patterns
   - Extract UTM parameters and campaign IDs
3. **Store**: Batch insert/update enriched data in PostgreSQL
4. **Report**: Return processing statistics

## Error Handling

- Robust error handling with transaction rollbacks
- Graceful handling of JWT decode failures
- Batch processing continues even if individual records fail
- Comprehensive logging for debugging

## Monitoring

Check Cloud Function logs for:
- Processing statistics
- Error messages
- Performance metrics
- Tenant context operations