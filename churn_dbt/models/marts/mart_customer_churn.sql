{{ config(materialized='table') }}

SELECT
    c.CUSTOMER_ID,
    c.FIRST_NAME,
    c.LAST_NAME,
    c.EMAIL,
    c.SIGNUP_DATE,
    c.PLAN_TYPE,
    c.MONTHLY_CHARGES,
    c.CONTRACT_LENGTH,
    c.IS_ACTIVE,
    l.CHURNED,
    l.CHURN_DATE,
    l.LAST_ACTIVE_DATE
FROM {{ ref('stg_customers') }} AS c
LEFT JOIN {{ ref('stg_churn_labels') }} AS l
    ON c.CUSTOMER_ID = l.CUSTOMER_ID