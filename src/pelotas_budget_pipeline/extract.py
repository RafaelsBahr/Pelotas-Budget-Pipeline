import pandas as pd
from pathlib import Path
from pelotas_budget_pipeline.schemas import DespesaBrutaSchema, ReceitaBrutaSchema

RAW_DIR = Path(__file__).parent.parent.parent / "data" / "raw"

DTYPES = {
    "CD_CONTA_SG": str,
    "CD_ELEMENTO": str,
    "CD_FUNCAO": str,
    "CD_SUBFUNCAO": str,
}

# Estas colunas são codigos e por isso devem ser do tipo string


def read_file(kind: str, year: int) -> pd.DataFrame:
    """Recebe tipo e ano dos dados. E retorna dataframe daquele dado.
    Args:
        kind (str): tipo de dado (receita ou despesa.)
        year (int): ano do dado (exemplo. 2025)

    Returns:
        (pd.dataframe): Dataframe dos dados lidos.
    """
    df = pd.read_csv(
        RAW_DIR / f"{kind}_{year}.csv",
        sep=",",
        decimal=".",
        encoding="utf-8",
        dtype=DTYPES,
    )
    return df


def extract_all(kind: str) -> pd.DataFrame:
    """Recebe um tipo de dado (receita/despesa) e retorna dataframe de todos os dados concatenados.
    Args:
        kind (str): tipo de dado (receita ou despesa.)

    Returns:
        (pd.dataframe): Dataframe dos dados lidos.
    """
    lista_arquivos = list(RAW_DIR.glob(f"{kind}_*.csv"))
    lista_dataframes = []
    for arquivo in lista_arquivos:
        ano = int(arquivo.stem.split("_")[1])
        df = read_file(kind, ano)
        lista_dataframes.append(df)
    return pd.concat(lista_dataframes, ignore_index=True)


if __name__ == "__main__":
    receita = ReceitaBrutaSchema.validate(extract_all("receita"))
    print(receita.shape)
    despesa = DespesaBrutaSchema.validate(extract_all("despesa"))
    print(despesa.shape)
