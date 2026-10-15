import os
from pathlib import Path

import joblib
import pandas as pd
import snowflake.connector
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

MODEL_PATH = PROJECT_ROOT / "ml" / "artifacts" / "churn_model.joblib"


def main():
    model = joblib.load(MODEL_PATH)

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
        cur = conn.cursor()
        cur.execute("""
            SELECT CUSTOMER_ID, PLAN_TYPE, MONTHLY_CHARGES,
                   CONTRACT_LENGTH, IS_ACTIVE, TOTAL_LOGINS,
                   TOTAL_API_CALLS, TOTAL_DATA_PROCESSED_GB,
                   TOTAL_FEATURES_USED, USAGE_REPORTED_SUPPORT_TICKETS,
                   TOTAL_SUPPORT_TICKETS, HIGH_PRIORITY_TICKETS,
                   OPEN_SUPPORT_TICKETS
            FROM CHURN_ANALYSIS.ML.CHURN_FEATURES
        """)
        columns = [item[0] for item in cur.description]
        df = pd.DataFrame(cur.fetchall(), columns=columns)
        cur.close()

        customer_ids = df["CUSTOMER_ID"]
        features = df.drop(columns=["CUSTOMER_ID"])
        probabilities = model.predict_proba(features)[:, 1]
        predictions = model.predict(features)

        results = pd.DataFrame({
            "CUSTOMER_ID": customer_ids,
            "PREDICTED_CHURN": predictions.astype(int),
            "CHURN_PROBABILITY": probabilities.astype(float),
        })

        cur = conn.cursor()
        try:
            cur.execute("BEGIN")
            cur.execute("""
                DELETE FROM CHURN_ANALYSIS.ML.CHURN_PREDICTIONS
                WHERE CUSTOMER_ID IN (
                    SELECT CUSTOMER_ID
                    FROM CHURN_ANALYSIS.ML.CHURN_FEATURES
                )
            """)
            cur.executemany("""
                INSERT INTO CHURN_ANALYSIS.ML.CHURN_PREDICTIONS
                    (CUSTOMER_ID, PREDICTED_CHURN, CHURN_PROBABILITY)
                VALUES (%s, %s, %s)
            """, list(results.itertuples(index=False, name=None)))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()

        print(f"Predictions saved: {len(results)}")
        print(results.sort_values(
            "CHURN_PROBABILITY", ascending=False
        ).to_string(index=False))

    finally:
        conn.close()


if __name__ == "__main__":
    main()
