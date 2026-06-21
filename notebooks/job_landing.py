import json
import os
from datetime import date, datetime
from decimal import Decimal

from dotenv import load_dotenv
from pymongo import MongoClient
from pyspark.sql import SparkSession

try:
    from bson import ObjectId
except ImportError:  # pragma: no cover - bson is provided by pymongo in Airflow.
    ObjectId = None

try:
    from bson.decimal128 import Decimal128
except ImportError:  # pragma: no cover - bson is provided by pymongo in Airflow.
    Decimal128 = None


load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "gearlog_erp")

S3_ENDPOINT = os.getenv("TIGRIS_ENDPOINT")
AWS_ACCESS_KEY = os.getenv("TIGRIS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("TIGRIS_SECRET_KEY")
NOME_BUCKET = os.getenv("TIGRIS_BUCKET", "projeto-lakehouse-satc")

COLECOES = [
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


def validar_variaveis_obrigatorias():
    variaveis = {
        "MONGO_URI": MONGO_URI,
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
        SparkSession.builder.appName("Job_Landing_Layer")
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


def normalizar_valor(valor):
    if ObjectId is not None and isinstance(valor, ObjectId):
        return str(valor)

    if Decimal128 is not None and isinstance(valor, Decimal128):
        return float(valor.to_decimal())

    if isinstance(valor, Decimal):
        return float(valor)

    if isinstance(valor, (datetime, date)):
        return valor.isoformat()

    if isinstance(valor, dict):
        return {str(chave): normalizar_valor(item) for chave, item in valor.items()}

    if isinstance(valor, list):
        return [normalizar_valor(item) for item in valor]

    return valor


def normalizar_documento(documento):
    documento_normalizado = {
        str(chave): normalizar_valor(valor) for chave, valor in documento.items()
    }

    # Garante que o Spark receba apenas tipos serializaveis em JSON.
    return json.loads(json.dumps(documento_normalizado, ensure_ascii=False))


def gravar_colecao_na_landing(spark, db, colecao):
    print(f"Iniciando Landing para a colecao: {colecao}")

    documentos = [
        normalizar_documento(documento)
        for documento in db[colecao].find()
    ]

    if not documentos:
        print(f"Aviso: colecao {colecao} sem documentos. Nada foi gravado.")
        return False

    path_landing = f"s3a://{NOME_BUCKET}/landing/{colecao}/"
    df = spark.createDataFrame(documentos)

    (
        df.write
        .mode("overwrite")
        .json(path_landing)
    )

    print(f"Sucesso: colecao {colecao} gravada em {path_landing}")
    return True


def main():
    validar_variaveis_obrigatorias()

    spark = criar_spark_session()
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DATABASE]

    try:
        total_gravado = 0

        for colecao in COLECOES:
            if gravar_colecao_na_landing(spark, db, colecao):
                total_gravado += 1

        if total_gravado == 0:
            raise RuntimeError("Nenhuma colecao foi gravada na camada Landing.")
    finally:
        client.close()
        spark.stop()


if __name__ == "__main__":
    main()
