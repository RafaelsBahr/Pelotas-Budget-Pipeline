from pathlib import Path

import pandas as pd
from loguru import logger

from pelotas_budget_pipeline.extract import extract_all, read_reference
from pelotas_budget_pipeline.indicators import (
    budget_execution,
    expenses_by_function,
    revenues_by_category,
    summary_by_year,
)
from pelotas_budget_pipeline.schemas import DespesaBrutaSchema, ReceitaBrutaSchema
from pelotas_budget_pipeline.transform import transform_expenses, transform_revenues
from pelotas_budget_pipeline.utils import log_decorator, timer_decorator

PROJECT_DIR = Path(__file__).parent
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
LOG_FILE = PROJECT_DIR / "logs" / "pipeline.log"

logger.add(LOG_FILE, rotation="5 MB")


@log_decorator
@timer_decorator
def save_table(df: pd.DataFrame, name: str) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(PROCESSED_DIR / f"{name}.parquet", index=False)


@log_decorator
@timer_decorator
def main() -> None:
    functions = read_reference("funcoes")
    subfunctions = read_reference("subfuncoes")
    population = read_reference("populacao")

    expenses = DespesaBrutaSchema.validate(extract_all("despesa"))
    expenses = transform_expenses(expenses, functions, subfunctions)
    revenues = ReceitaBrutaSchema.validate(extract_all("receita"))
    revenues = transform_revenues(revenues)

    tables = {
        "summary_by_year": summary_by_year(expenses, revenues, population),
        "expenses_by_function": expenses_by_function(expenses, population),
        "revenues_by_category": revenues_by_category(revenues),
        "budget_execution": budget_execution(expenses),
    }
    for name, df in tables.items():
        save_table(df, name)
        logger.info(f"{name}: {len(df)} linhas gravadas")


if __name__ == "__main__":
    main()
