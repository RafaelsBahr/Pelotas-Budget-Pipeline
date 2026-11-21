# Pelotas Budget Pipeline

> **Resumo em português.** Pipeline de dados em Python que lê os balancetes de receita e despesa da Prefeitura de Pelotas (RS), publicados nos dados abertos do TCE-RS, valida o arquivo bruto, limpa e padroniza os dados e gera quatro tabelas em Parquet prontas para análise. Responde a perguntas como: a prefeitura fechou o ano no azul? Para onde vai o dinheiro? Quanto a cidade depende de transferências? Período atual: 2024 e 2025.

An ETL pipeline in Python that turns the raw budget reports of the City of Pelotas (Rio Grande do Sul, Brazil) into clean, analysis-ready tables.

This is a study project, built to practice data engineering end to end with real public data.

## What this project answers

1. Did the city run a budget surplus or deficit each year?
2. How much goes to each area of government (health, education, etc.)?
3. Where does the money come from, and how much does the city depend on transfers from the state and federal governments?
4. Budget vs. execution: how much of what was planned actually happened?
5. How much was committed but still unpaid at year end?
6. Revenue and expense per inhabitant, including health and education per inhabitant.
7. What changed from 2024 to 2025?

## Data sources

| Data | Source | File |
|---|---|---|
| Revenue and expense reports (*balancetes*) of the City of Pelotas, 2024 and 2025, accumulated through December | [TCE-RS open data portal](https://dados.tce.rs.gov.br/) (Rio Grande do Sul State Court of Accounts) | `data/raw/receita_*.csv`, `data/raw/despesa_*.csv` |
| Official names of government functions and subfunctions | TCE-RS open data portal (reference tables) | `data/raw/funcoes.csv`, `data/raw/subfuncoes.csv` |
| Population | [IBGE](https://www.ibge.gov.br/cidades-e-estados/rs/pelotas.html) (Brazilian Institute of Geography and Statistics) | `data/raw/populacao.csv` |

The TCE-RS files are published as sent by the city, without any treatment. That is the point of this project: the raw data has real quality issues, and the pipeline has to deal with them.

## How to run

Requirements: Python 3.14 and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/RafaelsBahr/pelotas-budget-pipeline.git
cd pelotas-budget-pipeline
uv sync
uv run python main.py
```

The pipeline writes four Parquet files to `data/processed/` and a log to `logs/pipeline.log`. Running it twice gives the same result.

## How the pipeline works

```
data/raw/*.csv
   │
   ├── extract     read every year's file and stack them (extract.py)
   ├── validate    check the raw data against Pandera schemas (schemas.py)
   ├── transform   select, rename and standardize columns (transform.py)
   ├── indicators  build the four final tables (indicators.py)
   └── load        save each table as Parquet (main.py)
   │
data/processed/*.parquet
```

Every step is logged with its duration by two decorators (`utils.py`): `@log_decorator` records when each function starts, finishes or fails, and `@timer_decorator` measures how long it took.

| Output table | Grain (one row per) | Main columns |
|---|---|---|
| `summary_by_year` | year | revenue, committed/liquidated/paid expense, budget result, committed but unpaid, per capita values, year-over-year change |
| `expenses_by_function` | year and function | committed expense, share of the year, per capita |
| `revenues_by_category` | year and revenue category | estimated, collected, % collected, share of the year |
| `budget_execution` | year | initial and updated budget, committed expense, execution rates |

```
pelotas-budget-pipeline/
├── data/
│   ├── raw/                 source files, never changed
│   └── processed/           pipeline output (not versioned)
├── notebooks/               data exploration and column profiling
├── src/pelotas_budget_pipeline/
│   ├── extract.py
│   ├── schemas.py
│   ├── transform.py
│   ├── indicators.py
│   └── utils.py
└── main.py                  entry point
```

## Decisions

**Scope: the City Hall only.** The TCE-RS publishes one file per public body. This project covers only the City Hall (*Prefeitura*, body code 54400), not the City Council or the city's autonomous agencies, to keep the first version small and focused. The validation schema locks the city and body codes, so widening the scope has to be a deliberate change.

**Codes are read as text.** Account codes have up to 16 digits. Read as numbers, they lose precision and their leading digits, which carry meaning (the first two digits of a revenue account give its category).

**Validate the raw data before anything else.** Each raw file is checked with a Pandera schema right after extraction: data types, allowed values and rules such as "paid ≤ liquidated ≤ committed". If the source changes, the pipeline stops with a clear error instead of producing wrong numbers silently. The schema is not strict about extra columns, so a new column in the source does not break it.

**Revenue: only analytical rows.** The revenue file is a hierarchy: summary rows (`S`) are subtotals of the detail rows (`A`). Adding everything would count the same money several times, so only `A` rows are summed.

**Net revenue.** Part of the revenue goes straight to FUNDEB, the national education fund, and never reaches the city's hands. These deductions are kept in the sum, so the revenue figures show what the city actually had available.

**The FUNDEB deduction changed format between years.** In 2024 it comes as separate accounts whose code is the deducted account's code with a 9 in front; in 2025 it comes as negative rows inside the account itself. The pipeline removes the leading 9 so both years are classified the same way.

**Official function names from the reference table.** The name of each government function is spelled differently across years (upper and lower case). The pipeline drops it and brings the official name from the TCE-RS reference table by code.

**Expense rows with zero commitment are kept.** About half of the expense rows have nothing committed. They add zero to spending but hold R$ 227 million of budget, which matters for the budget vs. execution comparison.

**Committed expense as the measure.** Brazilian public spending has three stages: committed (*empenhado*), liquidated (service delivered) and paid. The budget result and the spending by area use committed expense, as set by Brazilian public budget law (Lei 4.320/1964, art. 35) and used by the courts of accounts. Liquidated and paid stay as supporting columns.

**What goes to GitHub.** The raw CSVs are versioned: the TCE-RS can revise its files, and versioning the input guarantees that the same code gives the same result. The Parquet output and the log are not, because the pipeline generates them. The tables in the next section serve as a reference for anyone who runs it.

## Findings (2024–2025)

Values in R$ million, except per capita values (R$).

| | 2024 | 2025 |
|---|---:|---:|
| Revenue collected | 1,458.7 | 1,549.1 |
| Expense committed | 1,329.3 | 1,427.9 |
| **Budget result (surplus)** | **129.4** | **121.2** |
| Committed but unpaid at year end | 186.0 | 154.8 |
| Revenue per inhabitant | 4,340 | 4,608 |
| Expense per inhabitant | 3,955 | 4,248 |

1. **Surplus in both years**, but smaller in 2025: expense grew 7.4% while revenue grew 6.2%.
2. **Health and education take about 70% of spending.**

   | Function | 2024 | 2025 | Share 2025 | Per capita 2025 (R$) |
   |---|---:|---:|---:|---:|
   | Health | 518.1 | 566.6 | 39.7% | 1,686 |
   | Education | 411.1 | 451.5 | 31.6% | 1,343 |
   | Special charges (court-ordered payments and debt service) | 112.4 | 143.8 | 10.1% | 428 |
   | Urban services | 109.9 | 85.5 | 6.0% | 254 |

3. **The city depends on transfers.** Current transfers from the state and federal governments are 65.5% of revenue in 2024 and 64.1% in 2025; the city's own taxes are 27.4% and 28.5%.
4. **Budget vs. execution.** Revenue came in about 13% above the estimate in both years. Expense committed reached 94% (2024) and 99% (2025) of the initial budget, but only 78% and 83% of the updated budget, which grows about 20% during the year with additional credits. Property income (*Receita Patrimonial*) collected 7 times the estimate in 2024 and 13 times in 2025.
5. **Committed but unpaid** fell from R$ 186.0 million to R$ 154.8 million.
6. **Per inhabitant**, revenue was R$ 4,608 and expense R$ 4,248 in 2025.
7. **From 2024 to 2025**, spending on urban services fell 22% while special charges rose 28%, almost entirely because court-ordered payments rose from R$ 48.9 million to R$ 77.9 million.

## Next steps

- Run the pipeline with 2021–2023 to test that it handles new years without code changes.
- Project 2, with SQL: monthly data, the water and sewage agency (SANEP), the City Council, and comparison with other cities.
- Optional: a Power BI dashboard reading the Parquet files.

## About this project

Built with AI tutoring (Claude): the AI explained concepts, reviewed my code and guided each step. The decisions and the data investigation are mine, and I can explain every line.
