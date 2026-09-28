import os
import pandas as pd
from sqlalchemy import create_engine, text

#CONFIGURATION ---

DB_USER = "root"
DB_PASSWORD = "your password"
DB_HOST = "localhost"
DB_PORT = "3306"
DB_NAME = "campuse_db"

CSV_PATH = r"C:\Users\Neetu\OneDrive\Desktop\project_data\indian_engineering_placement_2026.csv"

# MySQL connection URLs
DEFAULT_DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/mysql"
)

DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


#---- CREATE DATABASE -----

def ensure_database():
    """Create the target database if it does not exist."""

    default_engine = create_engine(DEFAULT_DATABASE_URL)

    with default_engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`"))
        conn.commit()
   
    default_engine.dispose()


#  LOAD CSV INTO MYSQL ----

def init_db(csv_path=CSV_PATH):

    # Check CSV file
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    # Read CSV
    df = pd.read_csv(csv_path)

    print("CSV loaded successfully!")
    print("Rows:", len(df))
    print("Columns:", list(df.columns))


    # -------- Handle missing values --------

    if "open_sourse_contribution" in df.columns:
        df["open_sourse_contribution"] = (
            df["open_sourse_contribution"]
            .fillna(df["open_sourse_contribution"].median())
        )

    if "linkedin_activity_score" in df.columns:
        df["linkedin_activity_score"] = (
            df["linkedin_activity_score"]
            .fillna(df["linkedin_activity_score"].median())
        )


    # -------- Connect to database --------

    engine = create_engine(DATABASE_URL)

    # -------- Write dataframe to MySQL --------

    df.to_sql(
        "students",
        con=engine,
        if_exists="replace",
        index=False
    )

    print("Data successfully loaded into MySQL!")


    # -------- Create indexes --------

    with engine.connect() as conn:

        # Only create indexes if these columns exist
        if "college_tier" in df.columns:
            conn.execute(
                text(
                    "ALTER TABLE students "
                    "ADD INDEX idx_tier (college_tier(50))"
                )
            )

        if "Branch" in df.columns:
            conn.execute(
                text(
                    "ALTER TABLE students "
                    "ADD INDEX idx_branch (Branch(50))"
                )
            )

        if "Placement_status" in df.columns:
            conn.execute(
                text(
                    "ALTER TABLE students "
                    "ADD INDEX idx_placement (Placement_status(20))"
                )
            )

        if "cgpa" in df.columns:
            conn.execute(
                text(
                    "ALTER TABLE students "
                    "ADD INDEX idx_cgpa (cgpa)"
                )
            )

        if "dsa_problem_solved" in df.columns:
            conn.execute(
                text(
                    "ALTER TABLE students "
                    "ADD INDEX idx_dsa (dsa_problem_solved)"
                )
            )

        conn.commit()

    engine.dispose()

    print("Data successfully loaded and indexed in MySQL Workbench!")


# ---------------- RUN PROGRAM ----------------

if __name__ == "__main__":

    ensure_database()
    init_db()
