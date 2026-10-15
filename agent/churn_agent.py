import os
from pathlib import Path

import snowflake.connector
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def main():
    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        database=os.environ["SNOWFLAKE_DATABASE"],
        schema="ML",
        role=os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
    )

    try:
        while True:
            print("\n=== Customer Churn Analysis Agent ===")
            print("1. Show highest-risk customers")
            print("2. Show prediction summary")
            print("3. Look up a customer")
            print("4. Exit")

            choice = input("Choose an option: ").strip()
            cur = conn.cursor()

            try:
                if choice == "1":
                    cur.execute("""
                        SELECT CUSTOMER_ID,
                               PREDICTED_CHURN,
                               ROUND(CHURN_PROBABILITY * 100, 1)
                                   AS RISK_PERCENT
                        FROM CHURN_ANALYSIS.ML.CHURN_PREDICTIONS
                        ORDER BY CHURN_PROBABILITY DESC
                        LIMIT 5
                    """)
                    print("\nHighest-risk customers:")
                    for row in cur.fetchall():
                        print(row)

                elif choice == "2":
                    cur.execute("""
                        SELECT COUNT(*) AS TOTAL_CUSTOMERS,
                               SUM(PREDICTED_CHURN) AS PREDICTED_CHURN
                        FROM CHURN_ANALYSIS.ML.CHURN_PREDICTIONS
                    """)
                    total, predicted_churn = cur.fetchone()
                    print(f"\nCustomers scored: {total}")
                    print(f"Predicted churn: {predicted_churn or 0}")
                    print(
                        "Note: These are demo predictions, "
                        "not validated real-world risk estimates."
                    )

                elif choice == "3":
                    customer_id = input(
                        "Enter customer ID (e.g. C005): "
                    ).strip().upper()

                    cur.execute("""
                        SELECT CUSTOMER_ID, PREDICTED_CHURN,
                               ROUND(CHURN_PROBABILITY * 100, 1)
                                   AS RISK_PERCENT,
                               SCORED_AT
                        FROM CHURN_ANALYSIS.ML.CHURN_PREDICTIONS
                        WHERE CUSTOMER_ID = %s
                    """, (customer_id,))

                    row = cur.fetchone()
                    if row:
                        print(row)
                    else:
                        print("Customer not found.")

                elif choice == "4":
                    print("Goodbye!")
                    break

                else:
                    print("Please choose 1, 2, 3, or 4.")

            finally:
                cur.close()

    finally:
        conn.close()


if __name__ == "__main__":
    main()
