import pandas as pd
import pandera.pandas as pa
from pandera.typing import Series


class DespesaBrutaSchema(pa.DataFrameModel):
    """Regras do balancete de despesa bruto (TCE-RS), conferidas logo após a extração."""

    ANO: Series[int] = pa.Field(ge=2000)
    MES: Series[int] = pa.Field(eq=12)
    COD_MUNICIPIO: Series[int] = pa.Field(eq=144)  # escopo atual: só Pelotas
    CD_ORGAO: Series[int] = pa.Field(eq=54400)
    CD_FUNCAO: Series[str] = pa.Field(str_matches=r"^\d{1,2}$")
    CD_SUBFUNCAO: Series[str] = pa.Field(str_matches=r"^\d{2,3}$")
    CD_ELEMENTO: Series[str] = pa.Field(str_matches=r"^\d\.\d\.\d{2}\.\d{2}$")
    DS_FUNCAO: Series[str] = pa.Field(nullable=False)
    DS_SUBFUNCAO: Series[str] = pa.Field(nullable=False)
    VL_DOTACAO_INICIAL: Series[float] = pa.Field(ge=0)
    VL_EMPENHADO: Series[float] = pa.Field(ge=0)
    VL_LIQUIDADO: Series[float] = pa.Field(ge=0)
    VL_PAGO: Series[float] = pa.Field(ge=0)

    @pa.dataframe_check
    def pago_ate_liquidado(cls, df: pd.DataFrame) -> Series[bool]:
        return df["VL_PAGO"] <= df["VL_LIQUIDADO"]

    @pa.dataframe_check
    def liquidado_ate_empenhado(cls, df: pd.DataFrame) -> Series[bool]:
        return df["VL_LIQUIDADO"] <= df["VL_EMPENHADO"]

    class Config:
        strict = False  # o arquivo tem 41 colunas; só as usadas foram declaradas


class ReceitaBrutaSchema(pa.DataFrameModel):
    """Regras do balancete de receita bruto (TCE-RS), conferidas logo após a extração."""

    ANO: Series[int] = pa.Field(ge=2000)
    MES: Series[int] = pa.Field(eq=12)
    COD_MUNICIPIO: Series[int] = pa.Field(eq=144)  # escopo atual: só Pelotas
    CD_ORGAO: Series[int] = pa.Field(eq=54400)
    CD_CONTA_SG: Series[str] = pa.Field(str_matches=r"^\d{15,16}$")
    DS_CONTA_SG: Series[str] = pa.Field(nullable=False)
    NIVEL: Series[str] = pa.Field(isin=["S", "A"])
    NR_NIVEL: Series[int] = pa.Field(ge=1, le=9)
    VL_ORCADO: Series[float]
    VL_ARRECADADO: Series[float]

    class Config:
        strict = False  # o arquivo tem 24 colunas; só as usadas foram declaradas
