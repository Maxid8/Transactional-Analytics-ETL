# Transactional Analytics ETL

![Python](https://img.shields.io/badge/Python-3.14-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18.4-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A small ETL pipeline that cleans, models, and loads a credit card
transaction dataset into a PostgreSQL data warehouse. Built as the
first project in a data engineering portfolio series, focused on
practicing pandas and SQL fundamentals.

The goal was to understand, clean, and organize raw transaction
data, then automatically load it into PostgreSQL for analysis.

I used a Jupyter notebook to explore the data first. I considered it
important to conduct an exploratory analysis before writing any
cleaning logic, so that every transformation decision was backed by
an actual observation about the data, not a guess.

To reduce redundancy and support efficient analytical queries, I
split the raw data into a star schema: a `fact_transaction` table
holding the measurable events, and `dim_date`, `dim_customer`,
`dim_merchant` dimension tables holding the descriptive attributes
around them.

## Data Model

The raw dataset was restructured into a star schema to reduce
redundancy and support efficient analytical queries:

- **`fact_transaction`** — one row per transaction, holding the
  measures (amount, fraud flag, transaction time, merchant
  coordinates) and foreign keys to the three dimensions below.
- **`dim_date`** — day-level calendar attributes (year, quarter,
  month, week, day name). Generated once for the full calendar
  range covered by the data, independent of this project, so it can
  be reused as-is in future projects.
- **`dim_customer`** — customer-level attributes (name, demographics,
  address).
- **`dim_merchant`** — merchant name and category.

**Why day-level, not timestamp-level, granularity in `dim_date`.**
`transaction_time` stays in `fact_transaction` rather than being
folded into the date dimension. Modeling every distinct timestamp as
its own dimension row would grow `dim_date` to millions of rows,
one per transaction, which defeats the purpose of a dimension table
(a small, reusable, mostly-static lookup). Day-level granularity
keeps `dim_date` compact and reusable across projects, while
`transaction_time` remains a per-transaction measure.

**Conscious scope decisions.** Two attributes were deliberately kept
at the fact-table level rather than pushed into a dimension:

- `merch_lat`/`merch_long`: a further-normalized model could split
  `dim_merchant` into individual store locations (moving toward a
  galaxy schema), each with its own coordinates. Customer addresses
  in the source data aren't given as coordinates, so proximity
  analysis (e.g. distance between customer and merchant) wasn't
  feasible without an external geocoding API. This is a natural
  extension for a future iteration.
- `transaction_time`: kept in the fact table for the reason
  explained above.

## Data Source

[Credit Card Transactions Fraud Detection Dataset](https://www.kaggle.com/datasets/kartik2112/fraud-detection)
(Kaggle, by Kartik Shenoy) — simulated credit card transactions,
1,852,394 rows across `fraudTrain.csv` and `fraudTest.csv`.

Not included in the repository due to size; download it from Kaggle
and place both CSV files in `data/raw/`.

## Prerequisites

- Python 3.14
- PostgreSQL 18.4

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Maxid8/Transactional-Analytics-ETL.git
   cd Transactional-Analytics-ETL
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\Activate.ps1   # Windows
   ```

3. Install the pinned dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create the raw data folder and add the dataset:
   ```bash
   mkdir data\raw
   ```
   Download the dataset from Kaggle (see [Data Source](#data-source)),
   unzip it, and place `fraudTrain.csv` and `fraudTest.csv` into
   `data/raw/`.

5. Create your `.env` file from the template and fill in your
   PostgreSQL credentials:
   ```bash
   cp .env.example .env
   ```

6. Create the database schema. During development this project used
   [DBeaver](https://dbeaver.io/) as the PostgreSQL client, so the
   simplest way is to open `sql/schema.sql` in DBeaver's SQL editor
   and execute it against your database. Alternatively, run it via
   `psql`:
   ```bash
   psql -U your_user -d your_database -f sql/schema.sql
   ```

7. Run the pipeline:
   ```bash
   python src/build_star_schema.py
   ```

8. (Optional) Run the analysis queries in `sql/queries.sql` against
   your database.

## Usage

Once the schema is created and `.env` is filled in, run the full
pipeline with a single command:

```bash
python src/build_star_schema.py
```

This will:

1. Load and clean the raw CSVs (or read the cached
   `data/processed/cleaned_fraud_data.parquet` if it already exists).
2. Build the `dim_date`, `dim_customer`, `dim_merchant` dimension
   tables and the `fact_transaction` fact table.
3. Validate that every fact row has a matching dimension row, and
   that each DataFrame's columns match the actual database schema.
4. Load all four tables into PostgreSQL, printing a row count per
   table as it goes:
   ```
   dim_date: 731 rows loaded.
   dim_merchant: 700 rows loaded.
   dim_customer: 999 rows loaded.
   fact_transaction: 1852394 rows loaded.
   ```

A full run (cleaning 1.85M rows from scratch through loading into
PostgreSQL) takes about a minute.

## Business Questions Answered

The full SQL is in [`sql/queries.sql`](sql/queries.sql). Each query
answers one specific business question:

1. Which categories experience the most fraud, and what is the total
   financial loss due to fraud per category?
2. What days of the week do fraudsters most often strike? Is there a
   detectable pattern on weekly transactions?
3. Which fraudulent transactions exceed the average transaction value
   for the given category?
4. What age groups and genders are most affected by fraud, and what
   is their average transaction size?
5. How did the total financial loss from fraud accumulate day by day
   over time?
6. Who are the merchants whose number of transactions reaches a
   minimum value (e.g. at least 50 transactions), but whose fraud
   rate is exceptionally high (>5%)?

## Project Structure

```
Transactional-Analytics-ETL/
├── data/
│   ├── raw/                       # fraudTrain.csv, fraudTest.csv (gitignored)
│   └── processed/                 # cleaned_fraud_data.parquet cache (gitignored)
├── notebooks/
│   └── data_exploration.ipynb     # exploratory analysis; not required to run the pipeline
├── sql/
│   ├── schema.sql                 # star schema DDL
│   └── queries.sql                # business-question queries
├── src/
│   ├── clean.py                   # raw CSVs -> cleaned DataFrame (with parquet caching)
│   └── build_star_schema.py       # cleaned DataFrame -> dimension/fact tables -> PostgreSQL
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for details.

## Note

This project was built for learning purposes, as part of a personal
data engineering portfolio series. Feedback is welcome, but it isn't
maintained as an actively developed, production-ready project.
