"""Shopify GraphQL query definitions."""

CUSTOMERS_QUERY = """
query getCustomers($first: Int!, $after: String, $query: String) {
  customers(first: $first, after: $after, query: $query) {
    nodes {
      id
      displayName
      firstName
      lastName
      defaultEmailAddress {
        emailAddress
        marketingState
      }
      defaultPhoneNumber {
        phoneNumber
        marketingState
      }
      amountSpent {
        amount
        currencyCode
      }
      numberOfOrders
      lastOrder {
        createdAt
      }
      note
      state
      tags
      verifiedEmail
      taxExempt
      taxExemptions
      locale
      statistics {
        predictedSpendTier
        rfmGroup
      }
      lifetimeDuration
      defaultAddress {
        id
        address1
        address2
        city
        province
        provinceCode
        country
        countryCodeV2
        zip
        phone
        company
        latitude
        longitude
        formatted
      }
      createdAt
      updatedAt
    }
    pageInfo {
      hasNextPage
      hasPreviousPage
      startCursor
      endCursor
    }
  }
}
"""


ORDERS_QUERY = """
query getOrders($first: Int!, $after: String, $query: String) {
  orders(first: $first, after: $after, query: $query) {
    nodes {
      id
      name
      createdAt
      updatedAt
      email
      phone
      customer {
        id
        defaultEmailAddress {
          emailAddress
        }
      }
      netPaymentSet {
      shopMoney {
        amount
      }
    }
    refunds(first: 10) {
        totalRefundedSet {
          shopMoney {
            amount
          }
      }
    }
      displayFinancialStatus
      displayFulfillmentStatus
      cancelledAt
      cancelReason
      closedAt
      confirmed
      test
      currencyCode
      currentTotalPriceSet {
        shopMoney {
          amount
        }
      }
      currentTotalDiscountsSet {
        shopMoney {
          amount
        }
      }
      totalTaxSet {
        shopMoney {
          amount
        }
      }
      totalShippingPriceSet {
        shopMoney {
          amount
        }
      }
      totalRefundedShippingSet {
        shopMoney {
          amount
          currencyCode
        }
      }
      customerJourneySummary {
        customerOrderIndex
        daysToConversion
        firstVisit {
          occurredAt
          source
          sourceType
          landingPage
          utmParameters {
            campaign
            medium
            source
            content
            term
          }
        }
        lastVisit {
          occurredAt
          source
          sourceType
          landingPage
          utmParameters {
            campaign
            medium
            source
            content
            term
          }
        }
      }
      discountCodes
      returnStatus
      transactions(first: 10) {
        gateway
      }
      lineItems(first: 250) {
        nodes {
          id
          title
          quantity
          variant {
            id
            title
            sku
            price
            product {
              id
            }
            inventoryItem {
              id
              unitCost {
                amount
                currencyCode
              }
            }
          }
          originalUnitPriceSet {
            shopMoney {
              amount
            }
          }
          discountedUnitPriceSet {
            shopMoney {
              amount
            }
          }
          totalDiscountSet {
            shopMoney {
              amount
            }
          }
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""

PRODUCTS_QUERY = """
query getProducts($first: Int!, $after: String, $query: String) {
  products(first: $first, after: $after, query: $query) {
    nodes {
      id
      title
      handle
      descriptionHtml
      productType
      vendor
      status
      tags
      publishedAt
      createdAt
      updatedAt
      seo {
        title
        description
      }
      featuredMedia {
        alt
        preview {
          image {
            altText
            url
          }
        }
      }
      media(first: 1) {
        nodes {
          preview {
            image {
              url
            }
          }
        }
      }
      totalInventory
      options {
        id
        name
        values
        position
      }
      variants(first: 100) {
        nodes {
          id
          title
          sku
          barcode
          price
          compareAtPrice
          inventoryQuantity
          inventoryPolicy
          position
          availableForSale
          inventoryItem {
            id
            unitCost {
              amount
              currencyCode
            }
          }
          selectedOptions {
            name
            value
          }
          createdAt
          updatedAt
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""
