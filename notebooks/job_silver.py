import os
import re
import unicodedata

from dotenv import load_dotenv
from pyspark.sql import functions as F
from pyspark.sql import SparkSession
from pyspark.sql.types import StringType


load_dotenv()

S3_ENDPOINT = os.getenv("TIGRIS_ENDPOINT")
AWS_ACCESS_KEY = os.getenv("TIGRIS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("TIGRIS_SECRET_KEY")
NOME_BUCKET = os.getenv("TIGRIS_BUCKET", "projeto-lakehouse-satc")

TABELAS = [
    "mecanicos",
    "fornecedores",
    "clientes",
    "veiculos",
    "pecas_estoque",
    "ordens_servico",
    "itens_os",
    "pagamentos",
    "agendamentos",
    "avaliacoes",
]

COLUNAS_AUDITORIA_BRONZE = [
    "DATA_CARGA",
    "NOME_ARQUIVO_ORIGEM",
    "DATA_HORA_BRONZE",
    "NOME_ARQUIVO",
]


def validar_variaveis_obrigatorias():
    variaveis = {
        "TIGRIS_ENDPOINT": S3_ENDPOINT,
        "TIGRIS_ACCESS_KEY": AWS_ACCESS_KEY,
        "TIGRIS_SECRET_KEY": AWS_SECRET_KEY,
    }
    faltantes = [nome for nome, valor in variaveis.items() if not valor]

    if faltantes:
        raise ValueError(
            "Variaveis de ambiente obrigatorias ausentes: "
            + ", ".join(faltantes)
        )


def criar_spark_session():
    return (
        SparkSession.builder.appName("Job_Silver_Layer")
        .config(
            "spark.jars.packages",
            "io.delta:delta-core_2.12:2.4.0,org.apache.hadoop:hadoop-aws:3.3.4",
        )
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
        .config("spark.hadoop.fs.s3a.endpoint", S3_ENDPOINT)
        .config("spark.hadoop.fs.s3a.access.key", AWS_ACCESS_KEY)
        .config("spark.hadoop.fs.s3a.secret.key", AWS_SECRET_KEY)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .getOrCreate()
    )


def aplicar_regras_nome_coluna(coluna):
    nome = unicodedata.normalize("NFKD", coluna)
    nome = nome.encode("ascii", "ignore").decode("ascii")
    nome = nome.upper()
    nome = re.sub(r"[^A-Z0-9]+", "_", nome).strip("_")

    regras = {
        "CD_": "CODIGO_",
        "VL_": "VALOR_",
        "DT_": "DATA_",
        "NM_": "NOME_",
        "DS_": "DESCRICAO_",
        "NR_": "NUMERO_",
    }

    for origem, destino in regras.items():
        nome = nome.replace(origem, destino)

    nome = nome.replace("_UF", "_UNIDADE_FEDERATIVA")

    if nome == "ID":
        return "ID"

    return nome or "COLUNA"


def padronizar_nomes_colunas(df):
    colunas_padronizadas = []
    ocorrencias = {}

    for coluna in df.columns:
        nome_base = aplicar_regras_nome_coluna(coluna)
        ocorrencias[nome_base] = ocorrencias.get(nome_base, 0) + 1

        if ocorrencias[nome_base] == 1:
            colunas_padronizadas.append(nome_base)
        else:
            colunas_padronizadas.append(f"{nome_base}_{ocorrencias[nome_base]}")

    return df.toDF(*colunas_padronizadas)


def remover_colunas_se_existirem(df, colunas):
    existentes = [coluna for coluna in colunas if coluna in df.columns]

    if existentes:
        return df.drop(*existentes)

    return df


def tratar_strings_vazias(df):
    for campo in df.schema.fields:
        if isinstance(campo.dataType, StringType):
            df = df.withColumn(
                campo.name,
                F.when(F.trim(F.col(campo.name)) == "", F.lit(None)).otherwise(
                    F.trim(F.col(campo.name))
                ),
            )

    return df


def converter_colunas_de_data(df):
    for campo in df.schema.fields:
        if isinstance(campo.dataType, StringType) and campo.name.startswith("DATA_"):
            df = df.withColumn(
                campo.name,
                F.coalesce(
                    F.to_timestamp(F.col(campo.name)),
                    F.to_timestamp(F.col(campo.name), "yyyy-MM-dd'T'HH:mm:ss.SSSSSS"),
                    F.to_timestamp(F.col(campo.name), "yyyy-MM-dd'T'HH:mm:ss"),
                ),
            )

    return df


def aplicar_regras_data_quality(df):
    df = tratar_strings_vazias(df)
    df = converter_colunas_de_data(df)

    if "ID" in df.columns:
        df = df.filter(F.col("ID").isNotNull())
        df = df.dropDuplicates(["ID"])
    else:
        df = df.dropDuplicates()

    return df


def gravar_silver(spark, tabela):
    path_bronze = f"s3a://{NOME_BUCKET}/bronze/{tabela}/"
    path_silver = f"s3a://{NOME_BUCKET}/silver/{tabela}/"

    print(f"Iniciando camada Silver para a tabela: {tabela}")

    df = spark.read.format("delta").load(path_bronze)
    df = padronizar_nomes_colunas(df)
    df = remover_colunas_se_existirem(df, COLUNAS_AUDITORIA_BRONZE)
    df = aplicar_regras_data_quality(df)

    df = (
        df.withColumn("NOME_TABELA_ORIGEM", F.lit(path_bronze))
        .withColumn("DATA_HORA_SILVER", F.current_timestamp())
    )

    (
        df.write
        .format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .save(path_silver)
    )

    print(f"Sucesso: tabela {tabela} gravada em {path_silver}")
    return True


def main():
    validar_variaveis_obrigatorias()

    spark = criar_spark_session()

    try:
        total_gravado = 0

        for tabela in TABELAS:
            try:
                if gravar_silver(spark, tabela):
                    total_gravado += 1
            except Exception as erro:
                print(f"Aviso: erro na tabela {tabela} - {erro}")

        if total_gravado == 0:
            raise RuntimeError("Nenhuma tabela foi gravada na camada Silver.")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
