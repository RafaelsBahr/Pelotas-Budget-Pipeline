import pandas as pd

from pelotas_budget_pipeline.extract import extract_all, read_reference
from pelotas_budget_pipeline.schemas import DespesaBrutaSchema, ReceitaBrutaSchema
from pelotas_budget_pipeline.transform import transform_expenses, transform_revenues


def summary_by_year(
    expenses: pd.DataFrame, revenues: pd.DataFrame, population: pd.DataFrame
) -> pd.DataFrame:
    """Resume receita, despesa e resultado orçamentário por ano.

    Args:
        expenses (pd.DataFrame): despesa limpa (saída de transform_expenses).
        revenues (pd.DataFrame): receita limpa (saída de transform_revenues).
        population (pd.DataFrame): população por ano (IBGE).

    Returns:
        pd.DataFrame: uma linha por ano, com valores, resultado, per capita e variação.

    """
    amount_columns = ["committed_amount", "liquidated_amount", "paid_amount"]
    expenses_year = expenses.groupby("year")[amount_columns].sum().reset_index()
    revenues_year = revenues.groupby("year")["collected_amount"].sum().reset_index()
    n_rows_expenses_year = len(expenses_year)
    summary = expenses_year.merge(revenues_year, on="year", how="left")
    assert len(summary) == n_rows_expenses_year, "O merge mudou o número de linhas"
    summary = summary.merge(population, on="year", how="left")
    assert len(summary) == n_rows_expenses_year, "O merge mudou o número de linhas"
    assert summary["population"].notna().all(), "Há ano sem população"
    summary["budget_result"] = summary["collected_amount"] - summary["committed_amount"]
    summary["committed_unpaid"] = summary["committed_amount"] - summary["paid_amount"]
    summary["revenue_per_capita"] = summary["collected_amount"] / summary["population"]
    summary["expense_per_capita"] = summary["committed_amount"] / summary["population"]
    summary = summary.sort_values("year")
    summary["revenue_change"] = summary["collected_amount"].pct_change()
    summary["expense_change"] = summary["committed_amount"].pct_change()
    return summary


def expenses_by_function(
    expenses: pd.DataFrame, population: pd.DataFrame
) -> pd.DataFrame:
    """Despesa empenhada por ano e função, com participação e valor per capita.

    Args:
        expenses (pd.DataFrame): despesa limpa (saída de transform_expenses).
        population (pd.DataFrame): população por ano (IBGE).

    Returns:
        pd.DataFrame: uma linha por ano e função.

    """
    keys = ["year", "function_code", "function_name"]
    by_function = expenses.groupby(keys)["committed_amount"].sum().reset_index()
    year_total = by_function.groupby("year")["committed_amount"].transform("sum")
    by_function["share_of_year"] = by_function["committed_amount"] / year_total
    n_rows = len(by_function)
    by_function = by_function.merge(population, on="year", how="left")
    assert len(by_function) == n_rows, "O merge mudou o número de linhas"
    assert by_function["population"].notna().all(), "Há ano sem população"
    by_function["amount_per_capita"] = (
        by_function["committed_amount"] / by_function["population"]
    )
    by_function = by_function.drop(columns="population")
    by_function = by_function.sort_values(
        by=["year", "committed_amount"], ascending=[True, False]
    )
    return by_function


def revenues_by_category(revenues: pd.DataFrame) -> pd.DataFrame:
    """Receita orçada e arrecadada por ano e categoria.

    Args:
        revenues (pd.DataFrame): receita limpa, (saída de transform_revenues)

    Returns:
        pd.DataFrame: uma linha por ano e categoria
    """
    keys = ["year", "category_code", "category_name"]
    by_category = (
        revenues.groupby(keys)
        .agg(
            estimated_budget=("estimated_budget", "sum"),
            collected_amount=("collected_amount", "sum"),
        )
        .reset_index()
    )
    by_category["pct_collected"] = (
        by_category["collected_amount"] / by_category["estimated_budget"]
    ).where(by_category["estimated_budget"] != 0)
    year_total = by_category.groupby("year")["collected_amount"].transform("sum")
    by_category["share_of_year"] = by_category["collected_amount"] / year_total
    by_category = by_category.sort_values(
        by=["year", "collected_amount"], ascending=[True, False]
    )
    return by_category


def budget_execution(expenses: pd.DataFrame) -> pd.DataFrame:
    """Dotação orçamentária x despesa empenhada por ano.

    Args:
        expenses (pd.DataFrame): despesa limpa (saída de transform_expenses).

    Returns:
        pd.DataFrame: uma linha por ano.
    """
    budget_columns = ["initial_budget", "updated_budget", "committed_amount"]
    execution = expenses.groupby("year")[budget_columns].sum().reset_index()
    execution["execution_rate_initial"] = (
        execution["committed_amount"] / execution["initial_budget"]
    )
    execution["execution_rate_updated"] = (
        execution["committed_amount"] / execution["updated_budget"]
    )
    return execution


if __name__ == "__main__":
    pd.options.display.float_format = "{:,.2f}".format
    pd.options.display.max_columns = None
    funcoes = read_reference("funcoes")
    subfuncoes = read_reference("subfuncoes")
    populacao = read_reference("populacao")

    expenses = extract_all("despesa")
    expenses = DespesaBrutaSchema.validate(expenses)
    expenses = transform_expenses(expenses, funcoes, subfuncoes)

    receita = extract_all("receita")
    receita = ReceitaBrutaSchema.validate(receita)
    revenues = transform_revenues(receita)
    summary = summary_by_year(expenses, revenues, populacao)
    by_function = expenses_by_function(expenses, populacao)
    by_category = revenues_by_category(revenues)
    execution = budget_execution(expenses)

    print("\n== Resumo por ano ==")
    print(summary)
    print("\n== Despesa por função ==")
    print(by_function)
    print("\n== Receita por categoria ==")
    print(by_category)
    print("\n== Execução orçamentária ==")
    print(execution)
