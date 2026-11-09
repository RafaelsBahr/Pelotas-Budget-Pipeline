import pandas as pd

from pelotas_budget_pipeline.extract import extract_all, read_reference
from pelotas_budget_pipeline.schemas import DespesaBrutaSchema, ReceitaBrutaSchema

EXPENSE_COLUMNS = [
    "ANO",
    "CD_ORGAO_ORCAMENTARIO",
    "NOME_ORGAO_ORCAMENTARIO",
    "CD_FUNCAO",
    "CD_SUBFUNCAO",
    "CD_PROGRAMA",
    "DS_PROGRAMA",
    "CD_ELEMENTO",
    "VL_DOTACAO_INICIAL",
    "VL_PREVISAO_EXECUCAO",
    "VL_EMPENHADO",
    "VL_LIQUIDADO",
    "VL_PAGO",
]

EXPENSE_NAMES = {
    "ANO": "year",
    "CD_ORGAO_ORCAMENTARIO": "department_code",
    "NOME_ORGAO_ORCAMENTARIO": "department_name",
    "CD_FUNCAO": "function_code",
    "DS_FUNCAO": "function_name",
    "CD_SUBFUNCAO": "subfunction_code",
    "DS_SUBFUNCAO": "subfunction_name",
    "CD_PROGRAMA": "program_code",
    "DS_PROGRAMA": "program_name",
    "CD_ELEMENTO": "element_code",
    "VL_DOTACAO_INICIAL": "initial_budget",
    "VL_PREVISAO_EXECUCAO": "updated_budget",
    "VL_EMPENHADO": "committed_amount",
    "VL_LIQUIDADO": "liquidated_amount",
    "VL_PAGO": "paid_amount",
}


def transform_expenses(
    df: pd.DataFrame, functions: pd.DataFrame, subfunctions: pd.DataFrame
) -> pd.DataFrame:
    """Limpa a despesa bruta e traz os nomes oficiais de função e subfunção.

    Args:
        df (pd.DataFrame): despesa bruta, já validada.
        functions (pd.DataFrame): tabela de referência de funções.
        subfunctions (pd.DataFrame): tabela de referência de subfunções.

    Returns:
        pd.DataFrame: despesa limpa, com colunas em inglês.
    """
    df = df[EXPENSE_COLUMNS]
    n_rows = len(df)
    df = df.merge(functions, on="CD_FUNCAO", how="left")
    df = df.merge(subfunctions, on="CD_SUBFUNCAO", how="left")
    assert len(df) == n_rows, "O merge mudou o número de linhas"
    assert df["DS_FUNCAO"].notna().all(), "Há função sem nome"
    assert df["DS_SUBFUNCAO"].notna().all(), "Há subfunção sem nome"
    df = df.rename(columns=EXPENSE_NAMES)
    return df


REVENUE_COLUMNS = [
    "ANO",
    "CD_CONTA_SG",
    "DS_CONTA_SG",
    "VL_ORCADO",
    "VL_ARRECADADO",
]


REVENUE_NAMES = {
    "ANO": "year",
    "CD_CONTA_SG": "account_code",
    "DS_CONTA_SG": "account_name",
    "VL_ORCADO": "estimated_budget",
    "VL_ARRECADADO": "collected_amount",
}

REVENUE_CATEGORIES = {
    "11": "Impostos, Taxas e Contribuições de Melhoria",
    "12": "Contribuições",
    "13": "Receita Patrimonial",
    "16": "Receita de Serviços",
    "17": "Transferências Correntes",
    "19": "Outras Receitas Correntes",
    "21": "Operações de Crédito",
    "22": "Alienação de Bens",
    "24": "Transferências de Capital",
}


def transform_revenues(df: pd.DataFrame) -> pd.DataFrame:
    """Limpa a receita bruta e classifica cada conta pela origem do dinheiro.

    Args:
        df (pd.DataFrame): receita bruta, já validada.

    Returns:
        pd.DataFrame: receita líquida, uma linha por conta analítica, com colunas em inglês.
    """
    df = df.loc[df["NIVEL"] == "A", REVENUE_COLUMNS]
    code = df["CD_CONTA_SG"]
    adjusted_code = code.where(~code.str.startswith("9"), code.str[1:])
    df["category_code"] = adjusted_code.str[:2]
    df["category_name"] = df["category_code"].map(REVENUE_CATEGORIES)
    assert df["category_name"].notna().all(), "Há conta sem categoria"
    assert (df["category_code"] != "91").all(), "Sobrou dedução sem ajuste"
    df = df.rename(columns=REVENUE_NAMES)
    return df


if __name__ == "__main__":
    pd.options.display.float_format = "{:,.2f}".format
    receita = extract_all("receita")
    receita = ReceitaBrutaSchema.validate(receita)
    revenues = transform_revenues(receita)
    print(revenues.shape)
    print(revenues.groupby("year")["collected_amount"].sum())
    print(revenues.groupby(["year", "category_name"])["collected_amount"].sum())
