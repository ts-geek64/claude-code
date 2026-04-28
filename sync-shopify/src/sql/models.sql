-- ============================================================================
-- AU VODKA INTEGRATED SCHEMA
-- This file contains all AU Vodka related tables, types, and constraints.
-- ============================================================================

-- ============================================================================
-- TYPES Section
-- ============================================================================

DO $$ BEGIN
  CREATE TYPE integration_type AS ENUM ('shopify', 'meta', 'google', 'klaviyo', 'tiktok');
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE TYPE integration_health_status AS ENUM ('healthy', 'unhealthy');
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE TYPE customer_rfm_group AS ENUM (
    'ACTIVE',
    'ALMOST_LOST',
    'AT_RISK',
    'CHAMPIONS',
    'DORMANT',
    'LOYAL',
    'NEEDS_ATTENTION',
    'NEW',
    'PREVIOUSLY_LOYAL',
    'PROMISING',
    'PROSPECTS'
  );
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE TYPE order_status AS ENUM (
    'pending',
    'authorized',
    'partially_paid',
    'paid',
    'partially_refunded',
    'refunded',
    'voided',
    'cancelled'
  );
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE TYPE fulfillment_status AS ENUM (
    'fulfilled',
    'partial',
    'restocked',
    'unfulfilled',
    'null'
  );
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE TYPE financial_status AS ENUM (
    'pending',
    'authorized',
    'partially_paid',
    'paid',
    'partially_refunded',
    'refunded',
    'voided'
  );
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE TYPE product_status AS ENUM ('ACTIVE', 'ARCHIVED', 'DRAFT');
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

-- ============================================================================
-- EXTENSION Section
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================================
-- TABLE: au_integrations
-- ============================================================================

CREATE TABLE IF NOT EXISTS au_integrations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
  user_id UUID NOT NULL,
  integration_type integration_type NOT NULL,
  token TEXT NOT NULL,
  token_expires_at TIMESTAMPTZ,
  last_token_refresh_at TIMESTAMPTZ,
  refresh_token_threshold INTERVAL DEFAULT INTERVAL '1 hour',
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  health_status integration_health_status NOT NULL DEFAULT 'healthy',
  last_refreshed_at TIMESTAMPTZ,
  external_integration_id VARCHAR(255),
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_au_integrations_user_id ON au_integrations(user_id);
CREATE INDEX IF NOT EXISTS idx_au_integrations_integration_type ON au_integrations(integration_type);

ALTER TABLE au_integrations 
  ADD CONSTRAINT fk_au_integrations_user 
  FOREIGN KEY (user_id) 
  REFERENCES au_users(id) 
  ON DELETE CASCADE;

CREATE TRIGGER trigger_au_integrations_updated_at
  BEFORE UPDATE ON au_integrations
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- TABLE: au_shopify_integrations
-- ============================================================================

CREATE TABLE IF NOT EXISTS au_shopify_integrations (
  integration_id UUID PRIMARY KEY,
  
  -- Shop Details
  shop_name TEXT NOT NULL,
  myshopify_domain TEXT NOT NULL,
  domain TEXT NOT NULL,
  shop_owner TEXT,
  email TEXT,
  customer_email TEXT,
  
  -- Configuration
  plan_name VARCHAR(255),
  currency VARCHAR(3),
  primary_locale TEXT,
  timezone TEXT,
  iana_timezone TEXT,
  has_taxes_included BOOLEAN DEFAULT false,
  
  -- Location
  country_code VARCHAR(2),
  country_name VARCHAR(255),
  province_code VARCHAR(2),
  province TEXT,
  city TEXT,
  zip TEXT,
  address_line_1 TEXT,
  address_line_2 TEXT,
  phone_number TEXT,
  geo_location GEOGRAPHY(Point, 4326),
  
  -- Timestamps
  shop_created_at TIMESTAMPTZ,
  shop_updated_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_au_shopify_integrations_domain ON au_shopify_integrations(domain);
CREATE INDEX IF NOT EXISTS idx_au_shopify_integrations_shop_name ON au_shopify_integrations(shop_name);
CREATE INDEX IF NOT EXISTS idx_au_shopify_integrations_geo_location ON au_shopify_integrations USING GIST (geo_location);

ALTER TABLE au_shopify_integrations
  ADD CONSTRAINT uk_au_shopify_integrations_integration
  UNIQUE (integration_id);

ALTER TABLE au_shopify_integrations
  ADD CONSTRAINT fk_au_shopify_integrations_integration
  FOREIGN KEY (integration_id)
  REFERENCES au_integrations(id)
  ON DELETE CASCADE;

CREATE TRIGGER trigger_au_shopify_integrations_updated_at
  BEFORE UPDATE ON au_shopify_integrations
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- TABLE: au_customers
-- ============================================================================

CREATE TABLE IF NOT EXISTS au_customers (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
  shopify_integration_id UUID NOT NULL,
  shopify_customer_id TEXT NOT NULL,
  
  -- Basic Information
  display_name VARCHAR(255),
  email VARCHAR(255),
  first_name VARCHAR(100),
  last_name VARCHAR(100),
  phone VARCHAR(50),
  locale VARCHAR(10),
  
  -- Marketing Consent
  has_accepted_marketing BOOLEAN DEFAULT false,
  marketing_opt_in_level VARCHAR(50),
  email_marketing_state VARCHAR(50),
  sms_marketing_state VARCHAR(50),
  
  -- Financial & Analytics
  total_spent DECIMAL(12, 2) DEFAULT 0.00,
  orders_count INTEGER DEFAULT 0,
  predicted_spend_tier VARCHAR(50),
  rfm_group customer_rfm_group NOT NULL DEFAULT 'NEW',
  lifetime_duration VARCHAR(100),
  rfm_score INTEGER NOT NULL DEFAULT -1,
  
  -- Account Status
  is_email_verified BOOLEAN DEFAULT false,
  is_tax_exempt BOOLEAN DEFAULT false,
  tax_exemptions JSONB,
  state VARCHAR(50),
  
  -- Additional Data
  tags TEXT,
  note TEXT,
  default_address_id TEXT,
  designated_market_areas_id UUID,
  census_id UUID,

  -- Address
  company VARCHAR(255),
  address1 VARCHAR(255),
  address2 VARCHAR(255),
  city VARCHAR(100),
  province VARCHAR(100),
  province_code VARCHAR(10),
  country VARCHAR(100),
  country_code VARCHAR(10),
  zip VARCHAR(20),
  geo_location GEOGRAPHY(Point, 4326),
  formatted TEXT,
  
  -- Timestamps
  shopify_created_at TIMESTAMPTZ,
  shopify_updated_at TIMESTAMPTZ,
  last_geocoded_at TIMESTAMPTZ,
  last_census_synced_at TIMESTAMPTZ,
  last_dma_synced_at TIMESTAMPTZ,
  last_synced_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_purchased_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_au_customers_shopify_integration_id ON au_customers(shopify_integration_id);
CREATE INDEX IF NOT EXISTS idx_au_customers_shopify_customer_id ON au_customers(shopify_customer_id);
CREATE INDEX IF NOT EXISTS idx_au_customers_email ON au_customers(email);
CREATE INDEX IF NOT EXISTS idx_au_customers_rfm_group ON au_customers(rfm_group);
CREATE INDEX IF NOT EXISTS idx_au_customers_rfm_score ON au_customers(rfm_score);
CREATE INDEX IF NOT EXISTS idx_au_customers_geo_location ON au_customers USING GIST (geo_location);
CREATE INDEX IF NOT EXISTS idx_au_customers_designated_market_areas_id ON au_customers(designated_market_areas_id);
CREATE INDEX IF NOT EXISTS idx_au_customers_census_id ON au_customers(census_id);

ALTER TABLE au_customers
  ADD CONSTRAINT uk_au_customers_shopify_integration_customer
  UNIQUE (shopify_integration_id, shopify_customer_id);

ALTER TABLE au_customers
  ADD CONSTRAINT fk_au_customers_shopify_integrations
  FOREIGN KEY (shopify_integration_id)
  REFERENCES au_shopify_integrations(id)
  ON DELETE CASCADE;

ALTER TABLE au_customers
  ADD CONSTRAINT fk_au_customers_designated_market_areas
  FOREIGN KEY (designated_market_areas_id)
  REFERENCES designated_market_areas(id)
  ON DELETE SET NULL;

ALTER TABLE au_customers
  ADD CONSTRAINT fk_au_customers_census_data
  FOREIGN KEY (census_data_id)
  REFERENCES census_data(id)
  ON DELETE SET NULL;

CREATE TRIGGER trigger_au_customers_updated_at
  BEFORE UPDATE ON au_customers
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- TABLE: au_orders
-- ============================================================================

CREATE TABLE IF NOT EXISTS au_orders (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
  shopify_integration_id UUID NOT NULL,
  shopify_order_id TEXT NOT NULL,
  customer_id UUID,

  -- Basic Information
  order_number INTEGER NOT NULL,
  order_name VARCHAR(50),
  email VARCHAR(255),
  phone VARCHAR(50),

  -- Status Fields
  financial_status financial_status,
  fulfillment_status fulfillment_status,
  order_status order_status DEFAULT 'pending',
  return_status VARCHAR(50),

  -- Flags
  is_confirmed BOOLEAN DEFAULT true,
  is_test_order BOOLEAN DEFAULT false,

  -- Financial Data
  currency VARCHAR(3) DEFAULT 'USD',
  total_tax DECIMAL(12, 2) DEFAULT 0.00,
  total_discounts DECIMAL(12, 2) DEFAULT 0.00,
  total_shipping DECIMAL(12, 2) DEFAULT 0.00,
  total_price DECIMAL(12, 2) DEFAULT 0.00,
  total_refunded_shipping DECIMAL(12, 2) DEFAULT 0.00,
  total_refunded_amount DECIMAL(12, 2) DEFAULT 0.00,
  net_payment_amount DECIMAL(12, 2) DEFAULT 0.00,

  -- Additional Data
  note TEXT,
  tags TEXT,
  discount_codes JSONB,
  payment_gateway_names TEXT[],

  -- Last Visit Data
  last_landing_page TEXT,
  last_utm_source TEXT,
  last_utm_medium TEXT,
  last_utm_campaign TEXT,
  last_utm_content TEXT,
  last_utm_term TEXT,
  last_utm_id TEXT,

  -- Original Raw Data (Last Visit)
  last_original_landing_page TEXT,
  last_original_utm_source TEXT,

  -- First Visit Data
  first_landing_page TEXT,
  first_utm_source TEXT,
  first_utm_medium TEXT,
  first_utm_campaign TEXT,
  first_utm_content TEXT,
  first_utm_term TEXT,
  first_utm_id TEXT,
  first_original_landing_page TEXT,
  first_original_utm_source TEXT,

  -- Timestamps
  cancelled_at TIMESTAMPTZ,
  cancel_reason VARCHAR(100),
  closed_at TIMESTAMPTZ,
  shopify_created_at TIMESTAMPTZ,
  shopify_updated_at TIMESTAMPTZ,
  last_synced_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_au_orders_shopify_integration_id ON au_orders(shopify_integration_id);
CREATE INDEX IF NOT EXISTS idx_au_orders_shopify_order_id ON au_orders(shopify_order_id);
CREATE INDEX IF NOT EXISTS idx_au_orders_customer_id ON au_orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_au_orders_financial_status ON au_orders(financial_status);
CREATE INDEX IF NOT EXISTS idx_au_orders_fulfillment_status ON au_orders(fulfillment_status);

ALTER TABLE au_orders
  ADD CONSTRAINT uk_au_orders_shopify_integration_order
  UNIQUE (shopify_integration_id, shopify_order_id);

ALTER TABLE au_orders
  ADD CONSTRAINT fk_au_orders_shopify_integrations
  FOREIGN KEY (shopify_integration_id)
  REFERENCES au_shopify_integrations(id)
  ON DELETE CASCADE;

ALTER TABLE au_orders
  ADD CONSTRAINT fk_au_orders_customers
  FOREIGN KEY (customer_id)
  REFERENCES au_customers(id)
  ON DELETE CASCADE;

CREATE TRIGGER trigger_au_orders_updated_at
  BEFORE UPDATE ON au_orders
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- TABLE: au_products
-- ============================================================================

CREATE TABLE IF NOT EXISTS au_products (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
  shopify_integration_id UUID NOT NULL,
  shopify_product_id TEXT NOT NULL,
  
  -- Basic Information
  title VARCHAR(500) NOT NULL,
  handle VARCHAR(500),
  description_html TEXT,
  product_type VARCHAR(255),
  vendor VARCHAR(255),
  status product_status DEFAULT 'ACTIVE',
  
  -- Pricing (from first variant)
  price DECIMAL(12, 2),
  compare_at_price DECIMAL(12, 2),
  unit_cost_amount DECIMAL(12, 2),
  unit_cost_currency_code VARCHAR(10),
  
  -- Inventory (aggregated from variants)
  total_inventory INTEGER DEFAULT 0,
  
  -- Organization
  tags TEXT,
  
  -- SEO
  seo_title VARCHAR(255),
  seo_description TEXT,
  
  -- Publishing
  published_at TIMESTAMPTZ,
  
  -- Featured Media
  featured_media_alt TEXT,
  featured_media_url TEXT,
  
  -- Additional Media
  media_url TEXT,
  media_count INTEGER DEFAULT 0,
  
  -- Variants count
  variants_count INTEGER DEFAULT 0,
  
  -- Options (stored as JSONB for flexibility)
  options JSONB,
  
  -- Timestamps
  shopify_created_at TIMESTAMPTZ,
  shopify_updated_at TIMESTAMPTZ,
  last_synced_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_au_products_shopify_integration_id ON au_products(shopify_integration_id);
CREATE INDEX IF NOT EXISTS idx_au_products_shopify_product_id ON au_products(shopify_product_id);
CREATE INDEX IF NOT EXISTS idx_au_products_status ON au_products(status);
CREATE INDEX IF NOT EXISTS idx_au_products_vendor ON au_products(vendor);

ALTER TABLE au_products
  ADD CONSTRAINT uk_au_products_shopify_integration_product UNIQUE (shopify_integration_id, shopify_product_id);
ALTER TABLE au_products
  ADD CONSTRAINT fk_au_products_shopify_integrations FOREIGN KEY (shopify_integration_id) REFERENCES au_shopify_integrations(id) ON DELETE CASCADE;

CREATE TRIGGER trigger_au_products_updated_at BEFORE UPDATE ON au_products FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- TABLE: au_product_variants
-- ============================================================================

CREATE TABLE IF NOT EXISTS au_product_variants (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
  product_id UUID NOT NULL,
  shopify_variant_id TEXT NOT NULL,
  shopify_product_id TEXT NOT NULL,
  
  -- Basic Information
  title VARCHAR(500),
  sku VARCHAR(255),
  barcode VARCHAR(255),
  
  -- Pricing
  price DECIMAL(12, 2) NOT NULL,
  compare_at_price DECIMAL(12, 2),
  unit_cost_amount DECIMAL(12, 2),
  unit_cost_currency_code VARCHAR(10),
  
  -- Inventory
  inventory_quantity INTEGER DEFAULT 0,
  inventory_policy VARCHAR(50),
  
  -- Variant Position
  position INTEGER,
  
  -- Options (option1, option2, option3)
  option1 VARCHAR(255),
  option2 VARCHAR(255),
  option3 VARCHAR(255),
  
  -- Availability
  is_available_for_sale BOOLEAN DEFAULT TRUE,
  
  -- Timestamps
  shopify_created_at TIMESTAMPTZ,
  shopify_updated_at TIMESTAMPTZ,
  last_synced_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_au_product_variants_product_id ON au_product_variants(product_id);
CREATE INDEX IF NOT EXISTS idx_au_product_variants_shopify_variant_id ON au_product_variants(shopify_variant_id);

ALTER TABLE au_product_variants
  ADD CONSTRAINT uk_au_product_variants_shopify_variant UNIQUE (product_id, shopify_variant_id);
ALTER TABLE au_product_variants
  ADD CONSTRAINT fk_au_product_variants_products FOREIGN KEY (product_id) REFERENCES au_products(id) ON DELETE CASCADE;

CREATE TRIGGER trigger_au_product_variants_updated_at BEFORE UPDATE ON au_product_variants FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- TABLE: au_order_line_items
-- ============================================================================

CREATE TABLE IF NOT EXISTS au_order_line_items (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
  order_id UUID NOT NULL,
  product_id UUID,
  product_variant_id UUID,
  shopify_line_item_id TEXT NOT NULL,
  shopify_product_id TEXT,
  shopify_variant_id TEXT,
  
  -- Product Information (denormalized for historical accuracy)
  product_title VARCHAR(500),
  variant_title VARCHAR(500),
  sku VARCHAR(255),
  
  -- Pricing
  quantity INTEGER NOT NULL,
  price DECIMAL(12, 2) NOT NULL,
  total_discount DECIMAL(12, 2) DEFAULT 0.00,
  
  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_au_order_line_items_order_id ON au_order_line_items(order_id);
CREATE INDEX IF NOT EXISTS idx_au_order_line_items_product_id ON au_order_line_items(product_id);

ALTER TABLE au_order_line_items
  ADD CONSTRAINT uk_au_order_line_items_order_line UNIQUE (order_id, shopify_line_item_id);
ALTER TABLE au_order_line_items
  ADD CONSTRAINT fk_au_order_line_items_orders FOREIGN KEY (order_id) REFERENCES au_orders(id) ON DELETE CASCADE;
ALTER TABLE au_order_line_items
  ADD CONSTRAINT fk_au_order_line_items_products FOREIGN KEY (product_id) REFERENCES au_products(id) ON DELETE SET NULL;
ALTER TABLE au_order_line_items
  ADD CONSTRAINT fk_au_order_line_items_product_variants FOREIGN KEY (product_variant_id) REFERENCES au_product_variants(id) ON DELETE SET NULL;

CREATE TRIGGER trigger_au_order_line_items_updated_at BEFORE UPDATE ON au_order_line_items FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- SHARED STORED PROCEDURES
-- ============================================================================
-- These are schema-agnostic: the caller passes the target table name.
-- Called from Python (product_repository.py)

CREATE OR REPLACE FUNCTION upsert_variant_cost_history(
  p_history_table   TEXT,
  p_variant_id      UUID,
  p_product_id      UUID,
  p_cost_amount     DECIMAL(12,2),
  p_currency_code   VARCHAR(10),
  p_source          VARCHAR(50)
) RETURNS void AS $$
BEGIN
  -- Close the currently-active record (if any)
  EXECUTE format(
    'UPDATE %I
     SET effective_end_at = CURRENT_TIMESTAMP,
         updated_at       = CURRENT_TIMESTAMP
     WHERE product_variant_id = $1
       AND effective_end_at IS NULL',
    p_history_table
  ) USING p_variant_id;

  -- Insert a fresh active record
  EXECUTE format(
    'INSERT INTO %I
       (product_variant_id, product_id, cost_amount, currency_code,
        effective_start_at, updated_by_source)
     VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP, $5)',
    p_history_table
  ) USING p_variant_id, p_product_id, p_cost_amount, p_currency_code, p_source;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION upsert_variant_cost_history(TEXT, UUID, UUID, DECIMAL, VARCHAR, VARCHAR) IS
  'Atomically closes the current open cost history record for a variant and inserts a new active record. Pass the tenant-prefixed table name as p_history_table.';

-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION upsert_variant_price_history(
  p_history_table   TEXT,
  p_variant_id      UUID,
  p_product_id      UUID,
  p_price_amount    DECIMAL(12,2),
  p_compare_at      DECIMAL(12,2),
  p_source          VARCHAR(50)
) RETURNS void AS $$
BEGIN
  -- Close the currently-active record (if any)
  EXECUTE format(
    'UPDATE %I
     SET effective_end_at = CURRENT_TIMESTAMP,
         updated_at       = CURRENT_TIMESTAMP
     WHERE product_variant_id = $1
       AND effective_end_at IS NULL',
    p_history_table
  ) USING p_variant_id;

  -- Insert a fresh active record
  EXECUTE format(
    'INSERT INTO %I
       (product_variant_id, product_id, price_amount, compare_at_price,
        effective_start_at, updated_by_source)
     VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP, $5)',
    p_history_table
  ) USING p_variant_id, p_product_id, p_price_amount, p_compare_at, p_source;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION upsert_variant_price_history(TEXT, UUID, UUID, DECIMAL, DECIMAL, VARCHAR) IS
  'Atomically closes the current open price history record for a variant and inserts a new active record. Pass the tenant-prefixed table name as p_history_table.';

-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION fn_close_old_variant_history() 
RETURNS TRIGGER AS $$
BEGIN
  -- Close any existing active record for this variant just before inserting a new one.
  -- TG_TABLE_NAME is the name of the table that fired the trigger.
  EXECUTE format(
    'UPDATE %I 
     SET effective_end_at = $1, 
         updated_at       = CURRENT_TIMESTAMP
     WHERE product_variant_id = $2 
       AND effective_end_at IS NULL',
    TG_TABLE_NAME
  ) USING NEW.effective_start_at, NEW.product_variant_id;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION fn_close_old_variant_history() IS 
  'Trigger function to automatically close (set effective_end_at) any active history record for a variant before a new record is inserted.';


-- ============================================================================
-- AU VODKA TENANT
-- ============================================================================

-- ----------------------------------------------------------------------------
-- au_product_variant_cost_history
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS au_product_variant_cost_history (
  id                   UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
  product_variant_id   UUID NOT NULL,
  product_id           UUID NOT NULL,

  -- The cost value for this version
  cost_amount          DECIMAL(12, 2) NOT NULL,
  currency_code        VARCHAR(10),

  -- Version-control window
  -- effective_end_at IS NULL  →  this record is currently active
  effective_start_at   TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  effective_end_at     TIMESTAMPTZ,

  -- Source of the update for audit trail
  -- Values: 'shopify' | 'admin_panel'
  updated_by_source    VARCHAR(50) NOT NULL DEFAULT 'shopify',

  created_at           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- FK constraints
ALTER TABLE au_product_variant_cost_history
  ADD CONSTRAINT fk_au_cost_hist_variant
  FOREIGN KEY (product_variant_id)
  REFERENCES au_product_variants(id)
  ON DELETE CASCADE;

ALTER TABLE au_product_variant_cost_history
  ADD CONSTRAINT fk_au_cost_hist_product
  FOREIGN KEY (product_id)
  REFERENCES au_products(id)
  ON DELETE CASCADE;

-- No-overlap: at most one open (effective_end_at IS NULL) record per variant
CREATE UNIQUE INDEX IF NOT EXISTS uq_au_variant_cost_open
  ON au_product_variant_cost_history (product_variant_id)
  WHERE effective_end_at IS NULL;

-- Range lookup: fetch history ordered by most-recent first
CREATE INDEX IF NOT EXISTS idx_au_variant_cost_hist_lookup
  ON au_product_variant_cost_history (product_variant_id, effective_start_at DESC);

-- Trigger to auto-maintain updated_at
CREATE TRIGGER trigger_au_variant_cost_history_updated_at
  BEFORE UPDATE ON au_product_variant_cost_history
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to auto-close previous active record
CREATE TRIGGER trigger_au_variant_cost_history_close_old
  BEFORE INSERT ON au_product_variant_cost_history
  FOR EACH ROW EXECUTE FUNCTION fn_close_old_variant_history();

-- ----------------------------------------------------------------------------
-- au_product_variant_price_history
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS au_product_variant_price_history (
  id                   UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
  product_variant_id   UUID NOT NULL,
  product_id           UUID NOT NULL,

  -- The price value for this version
  price_amount         DECIMAL(12, 2) NOT NULL,
  compare_at_price     DECIMAL(12, 2),

  -- Version-control window
  effective_start_at   TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  effective_end_at     TIMESTAMPTZ,

  -- Source of the update for audit trail
  updated_by_source    VARCHAR(50) NOT NULL DEFAULT 'shopify',

  created_at           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE au_product_variant_price_history
  ADD CONSTRAINT fk_au_price_hist_variant
  FOREIGN KEY (product_variant_id)
  REFERENCES au_product_variants(id)
  ON DELETE CASCADE;

ALTER TABLE au_product_variant_price_history
  ADD CONSTRAINT fk_au_price_hist_product
  FOREIGN KEY (product_id)
  REFERENCES au_products(id)
  ON DELETE CASCADE;

CREATE UNIQUE INDEX IF NOT EXISTS uq_au_variant_price_open
  ON au_product_variant_price_history (product_variant_id)
  WHERE effective_end_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_au_variant_price_hist_lookup
  ON au_product_variant_price_history (product_variant_id, effective_start_at DESC);

CREATE TRIGGER trigger_au_variant_price_history_updated_at
  BEFORE UPDATE ON au_product_variant_price_history
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_au_variant_price_history_close_old
  BEFORE INSERT ON au_product_variant_price_history
  FOR EACH ROW EXECUTE FUNCTION fn_close_old_variant_history();

-- ----------------------------------------------------------------------------
-- Snapshot columns on au_order_line_items
-- Written once at order-sync time; never overwritten.
-- ----------------------------------------------------------------------------

ALTER TABLE au_order_line_items
  ADD COLUMN IF NOT EXISTS cost_snapshot       DECIMAL(12, 2),
  ADD COLUMN IF NOT EXISTS price_snapshot      DECIMAL(12, 2),
  ADD COLUMN IF NOT EXISTS margin_snapshot_pct DECIMAL(8, 4);

-- Partial index for efficient profitability queries on orders with snapshots
CREATE INDEX IF NOT EXISTS idx_au_order_line_items_cost_snapshot
  ON au_order_line_items (order_id)
  WHERE cost_snapshot IS NOT NULL;


-- ============================================================================
-- AU VODKA TENANT
-- ============================================================================

CREATE OR REPLACE FUNCTION au_customers_all_time_profit(c au_customers)
RETURNS NUMERIC AS $$
  SELECT COALESCE(SUM(
    o.net_payment_amount
    - ROUND((o.total_tax * (1 - (o.total_refunded_amount / NULLIF(o.total_price, 0))))::NUMERIC, 2)
    - ROUND((o.total_shipping - COALESCE(o.total_refunded_shipping, 0))::NUMERIC, 2)
    - ROUND((COALESCE(product_cost.cost, 0) * (1 - (o.total_refunded_amount / NULLIF(o.total_price, 0))))::NUMERIC, 2)
    - CASE WHEN COALESCE(item_count.total_qty, 0) <= 1 THEN 40 ELSE 20 END
  ), 0)
  FROM au_orders o
  LEFT JOIN LATERAL (
    SELECT COALESCE(SUM(
      CASE 
        WHEN li.cost_snapshot IS NOT NULL THEN li.cost_snapshot * li.quantity
        ELSE COALESCE(pv.unit_cost_amount, p.unit_cost_amount, 0.00) * li.quantity
      END
    ), 0) AS cost
    FROM au_order_line_items li
    LEFT JOIN au_product_variants pv ON pv.id = li.product_variant_id
    LEFT JOIN au_products p ON p.id = li.product_id
    WHERE li.order_id = o.id
  ) product_cost ON true
  LEFT JOIN LATERAL (
    SELECT COALESCE(SUM(li.quantity), 0) AS total_qty
    FROM au_order_line_items li
    WHERE li.order_id = o.id
  ) item_count ON true
  WHERE o.customer_id = c.id
    AND o.financial_status IN ('paid', 'partially_refunded')
    AND o.order_status NOT IN ('refunded', 'voided', 'cancelled')
    AND (o.fulfillment_status IS NULL OR o.fulfillment_status != 'restocked')
    AND o.net_payment_amount > 0
    AND o.is_test_order = false;
$$ LANGUAGE sql STABLE;

-- -------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION au_orders_profit(o au_orders)
RETURNS NUMERIC AS $$
  SELECT
    o.net_payment_amount
    - ROUND((o.total_tax * (1 - (o.total_refunded_amount / NULLIF(o.total_price, 0))))::NUMERIC, 2)
    - ROUND((o.total_shipping - COALESCE(o.total_refunded_shipping, 0))::NUMERIC, 2)
    - ROUND((COALESCE(product_cost.cost, 0) * (1 - (o.total_refunded_amount / NULLIF(o.total_price, 0))))::NUMERIC, 2)
    - CASE WHEN COALESCE(item_count.total_qty, 0) <= 1 THEN 40 ELSE 20 END
  FROM (
    SELECT COALESCE(SUM(
      CASE 
        WHEN li.cost_snapshot IS NOT NULL THEN li.cost_snapshot * li.quantity
        ELSE COALESCE(pv.unit_cost_amount, p.unit_cost_amount, 0.00) * li.quantity
      END
    ), 0) AS cost
    FROM au_order_line_items li
    LEFT JOIN au_product_variants pv ON pv.id = li.product_variant_id
    LEFT JOIN au_products p ON p.id = li.product_id
    WHERE li.order_id = o.id
  ) product_cost,
  (
    SELECT COALESCE(SUM(li.quantity), 0) AS total_qty
    FROM au_order_line_items li
    WHERE li.order_id = o.id
  ) item_count;
$$ LANGUAGE sql STABLE;