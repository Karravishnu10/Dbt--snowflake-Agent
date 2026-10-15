import os
from pathlib import Path

import joblib
import pandas as pd
import snowflake.connector
from dotenv import load_dotenv
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

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
        cur = conn.cursor()
        cur.execute("""
            SELECT
                PLAN_TYPE,
                MONTHLY_CHARGES,
                CONTRACT_LENGTH,
                IS_ACTIVE,
                TOTAL_LOGINS,
                TOTAL_API_CALLS,
                TOTAL_DATA_PROCESSED_GB,
                TOTAL_FEATURES_USED,
                USAGE_REPORTED_SUPPORT_TICKETS,
                TOTAL_SUPPORT_TICKETS,
                HIGH_PRIORITY_TICKETS,
                OPEN_SUPPORT_TICKETS,
                CHURNED
            FROM CHURN_ANALYSIS.ML.CHURN_FEATURES
        """)
        columns = [item[0] for item in cur.description]
        df = pd.DataFrame(cur.fetchall(), columns=columns)
        cur.close()
    finally:
        conn.close()

    df = df.dropna(subset=["CHURNED"])
    X = df.drop(columns=["CHURNED"])
    y = df["CHURNED"].astype(int)

    categorical = X.select_dtypes(
        include=["object", "bool"]
    ).columns.tolist()
    numeric = X.select_dtypes(
        include=["number"]
    ).columns.tolist()

    preprocessing = ColumnTransformer([
        (
            "numeric",
            Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
            ]),
            numeric,
        ),
        (
            "categorical",
            Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("encoder", OneHotEncoder(handle_unknown="ignore")),
            ]),
            categorical,
        ),
    ])

    model = Pipeline([
        ("preprocess", preprocessing),
        ("classifier", RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            class_weight="balanced",
        )),
    ])

    model.fit(X, y)

    output_dir = PROJECT_ROOT / "ml" / "artifacts"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "churn_model.joblib"
    joblib.dump(model, output_path)

    print("Training pipeline: SUCCESS")
    print(f"Training rows: {len(df)}")
    print(f"Churned rows: {int(y.sum())}")
    print(f"Not churned rows: {int((y == 0).sum())}")
    print(f"Model saved to: {output_path}")
    print("Note: Training fit is not a measure of model performance.")


if __name__ == "__main__":
    main()
