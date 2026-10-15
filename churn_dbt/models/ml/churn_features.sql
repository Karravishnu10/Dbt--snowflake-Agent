{{ config(materialized='table') }}

SELECT
    c.CUSTOMER_ID,
    c.SIGNUP_DATE,
    DATEDIFF('day', c.SIGNUP_DATE, CURRENT_DATE())
        AS CUSTOMER_TENURE_DAYS,
    c.PLAN_TYPE,
    c.MONTHLY_CHARGES,
    c.CONTRACT_LENGTH,
    c.IS_ACTIVE,

    a.TOTAL_LOGINS,
    a.TOTAL_API_CALLS,
    a.TOTAL_DATA_PROCESSED_GB,
    a.TOTAL_FEATURES_USED,
    a.USAGE_REPORTED_SUPPORT_TICKETS,
    a.TOTAL_SUPPORT_TICKETS,
    a.HIGH_PRIORITY_TICKETS,
    a.OPEN_SUPPORT_TICKETS,

    c.CHURNED
FROM {{ ref('mart_customer_churn') }} AS c
LEFT JOIN {{ ref('mart_customer_activity') }} AS a
    ON c.CUSTOMER_ID = a.CUSTOMER_ID