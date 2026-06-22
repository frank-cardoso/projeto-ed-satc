import os
from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
import os
import traceback
from datetime import datetime

from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import TimestampType

load_dotenv()

S3_ENDPOINT = os.getenv("TIGRIS_ENDPOINT")
AWS_ACCESS_KEY = os.getenv("TIGRIS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("TIGRIS_SECRET_KEY")
NOME_BUCKET = os.getenv("TIGRIS_BUCKET", "projeto-lakehouse-satc")

# Dimensões mapeadas: silver_table -> dim_name
DIM_TABLES = {
    "clientes": "dim_cliente",
    "mecanicos": "dim_mecanico",
    "veiculos": "dim_veiculo",
    "fornecedores": "dim_fornecedor",
    "pecas_estoque": "dim_peca",
}

FACT_TABLE = "fato_ordens_servico"

try:
    from delta.tables import DeltaTable
    HAS_DELTA = True
except Exception:
    DeltaTable = None
    HAS_DELTA = False


def validar_variaveis_obrigatorias():
    variaveis = {
        "TIGRIS_ENDPOINT": S3_ENDPOINT,
        "TIGRIS_ACCESS_KEY": AWS_ACCESS_KEY,
        "TIGRIS_SECRET_KEY": AWS_SECRET_KEY,
    }
    faltantes = [nome for nome, valor in variaveis.items() if not valor]

    if faltantes:
        raise ValueError("Variaveis de ambiente obrigatorias ausentes: " + ", ".join(faltantes))


def criar_spark_session():
    return (
        SparkSession.builder.appName("Job_Gold_Layer")
        .config(
            "spark.jars.packages",
            "io.delta:delta-core_2.12:2.4.0,org.apache.hadoop:hadoop-aws:3.3.4",
        )
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.hadoop.fs.s3a.endpoint", S3_ENDPOINT)
        .config("spark.hadoop.fs.s3a.access.key", AWS_ACCESS_KEY)
        .config("spark.hadoop.fs.s3a.secret.key", AWS_SECRET_KEY)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .getOrCreate()
    )


def _determine_key_column(df):
    cols = [c.upper() for c in df.columns]
    if "ID" in cols:
        # preserve original casing
        for c in df.columns:
            if c.upper() == "ID":
                return c

    codigo_cols = [c for c in df.columns if c.upper().startswith("CODIGO_")]
    if codigo_cols:
        return codigo_cols[0]

    return None


def _add_natural_key_if_needed(df, key_col):
    if key_col:
        return df, key_col

    # cria NATURAL_KEY como hash das colunas (fallback)
    cols = df.columns
    df = df.withColumn(
        "NATURAL_KEY", F.md5(F.concat_ws("||", *[F.coalesce(F.col(c).cast("string"), F.lit("")) for c in cols]))
    )
    return df, "NATURAL_KEY"


def _compute_hash(df, key_col, ignore_cols=None):
    if ignore_cols is None:
        ignore_cols = []

    attrs = [c for c in df.columns if c not in ignore_cols + [key_col, "sk", "data_inicio", "data_fim", "flag_ativo", "hash_atributos"]]

    if attrs:
        df = df.withColumn("hash_atributos", F.md5(F.concat_ws("||", *[F.coalesce(F.col(c).cast("string"), F.lit("")) for c in attrs])))
    else:
        df = df.withColumn("hash_atributos", F.md5(F.lit("")))

    return df, attrs


def process_dimension(spark, tabela, dim_name):
    path_silver = f"s3a://{NOME_BUCKET}/silver/{tabela}/"
    path_dim = f"s3a://{NOME_BUCKET}/gold/{dim_name}/"

    print(f"[DIM] Iniciando processamento da dimensão {dim_name} a partir de {path_silver}")

    try:
        incoming = spark.read.format("delta").load(path_silver)
    except Exception as e:
        print(f"[DIM] Aviso: não foi possível ler {path_silver} - {e}")
        return False

    # remove colunas de auditoria/carga que não fazem parte do domínio
    for col in ["NOME_TABELA_ORIGEM", "DATA_HORA_SILVER", "DATA_CARGA", "NOME_ARQUIVO", "NOME_ARQUIVO_ORIGEM", "DATA_HORA_BRONZE"]:
        if col in incoming.columns:
            incoming = incoming.drop(col)

    key_col = _determine_key_column(incoming)
    incoming, key_col = _add_natural_key_if_needed(incoming, key_col)

    incoming, attrs = _compute_hash(incoming, key_col)

    incoming = incoming.withColumn("data_inicio", F.current_timestamp()).withColumn(
        "data_fim", F.lit(None).cast(TimestampType())
    ).withColumn("flag_ativo", F.lit(True))

    # surrogate key por versão
    incoming = incoming.withColumn(
        "sk", F.md5(F.concat_ws("||", F.col(key_col).cast("string"), F.date_format(F.col("data_inicio"), "yyyy-MM-dd'T'HH:mm:ss")))
    )

    final_cols = [key_col] + attrs + ["sk", "data_inicio", "data_fim", "flag_ativo", "hash_atributos"]

    if not HAS_DELTA:
        print("[DIM] Delta não disponível: gravando dimensão em modo overwrite (fallback)")
        incoming.select(*final_cols).write.format("parquet").mode("overwrite").save(path_dim)
        return True

    try:
        if not DeltaTable.isDeltaTable(spark, path_dim):
            incoming.select(*final_cols).write.format("delta").mode("overwrite").save(path_dim)
            print(f"[DIM] Dimensão {dim_name} criada em {path_dim}")
            return True

        # tabela já existe: identificar mudanças e aplicar SCD Type 2
        delta_table = DeltaTable.forPath(spark, path_dim)
        existing = spark.read.format("delta").load(path_dim)
        existing_active = existing.filter(F.col("flag_ativo") == True).select(key_col, "hash_atributos")

        src_hashes = incoming.select(key_col, "hash_atributos").alias("src")
        joined = src_hashes.join(existing_active.alias("tgt"), on=key_col, how="inner")
        changed = joined.filter(F.col("src.hash_atributos") != F.col("tgt.hash_atributos")).select(key_col).distinct()
        changed_keys = [r[key_col] for r in changed.collect()]

        if changed_keys:
            keys_literal = ",".join([f"'{k}'" for k in changed_keys])
            print(f"[DIM] Expirando {len(changed_keys)} chaves na dimensão {dim_name}")
            delta_table.update(
                condition=f"{key_col} IN ({keys_literal}) AND flag_ativo = true",
                set={"data_fim": "current_timestamp()", "flag_ativo": "false"},
            )

        # registros novos: chaves novas (leftanti) + registros que mudaram (changed_keys)
        new_from_new = incoming.alias("src").join(existing_active.alias("tgt"), on=key_col, how="leftanti").select("src.*")
        if changed_keys:
            new_from_changed = incoming.filter(F.col(key_col).isin(changed_keys))
            new_records = new_from_new.unionByName(new_from_changed)
        else:
            new_records = new_from_new

        if new_records.count() > 0:
            new_records.select(*final_cols).write.format("delta").mode("append").save(path_dim)
            print(f"[DIM] Inseridos {new_records.count()} registros na dimensão {dim_name}")
        else:
            print(f"[DIM] Nenhuma inserção nova para dimensão {dim_name}")

        return True
    except Exception as e:
        print(f"[DIM] Erro ao processar dimensão {dim_name}: {e}")
        traceback.print_exc()
        return False


def _find_column_by_keywords(df, keywords):
    cols = df.columns
    for kw in keywords:
        for c in cols:
            if kw in c.upper():
                return c
    return None


def process_fact_ordens_servico(spark):
    path_orders = f"s3a://{NOME_BUCKET}/silver/ordens_servico/"
    path_items = f"s3a://{NOME_BUCKET}/silver/itens_os/"
    path_fact = f"s3a://{NOME_BUCKET}/gold/{FACT_TABLE}/"
    path_checkpoint = f"s3a://{NOME_BUCKET}/gold/checkpoints/{FACT_TABLE}/"

    print(f"[FACT] Iniciando processamento do fato {FACT_TABLE}")

    try:
        orders = spark.read.format("delta").load(path_orders)
    except Exception as e:
        print(f"[FACT] Aviso: não foi possível ler {path_orders} - {e}")
        return False

    # lê checkpoint
    last_ts = None
    if HAS_DELTA and DeltaTable.isDeltaTable(spark, path_checkpoint):
        try:
            chk = spark.read.format("delta").load(path_checkpoint).select("last_processed").limit(1).collect()
            if chk:
                last_ts = chk[0]["last_processed"]
        except Exception:
            last_ts = None

    if "DATA_HORA_SILVER" in orders.columns:
        orders = orders.withColumn("DATA_HORA_SILVER_TS", F.to_timestamp(F.col("DATA_HORA_SILVER")))
        if last_ts:
            orders_new = orders.filter(F.col("DATA_HORA_SILVER_TS") > F.lit(last_ts))
        else:
            orders_new = orders
    else:
        orders_new = orders

    if orders_new.rdd.isEmpty():
        print("[FACT] Nenhum pedido novo para processar")
        return True

    # tenta agregar valor total a partir de itens
    try:
        items = spark.read.format("delta").load(path_items)
        # encontrar coluna de FK para ordens em items
        candidate_fk = _find_column_by_keywords(items, ["ORDEM", "OS", "ORDENSERVICO", "ID_ORDEM"]) or _find_column_by_keywords(items, ["ID"])
        # encontrar coluna de valor em items
        candidate_val = _find_column_by_keywords(items, ["VALOR", "VLR", "PRECO", "TOTAL"]) or None

        if candidate_fk and candidate_val:
            items_agg = (
                items.groupBy(candidate_fk)
                .agg(F.sum(F.col(candidate_val).cast("double")).alias("VALOR_TOTAL"))
            )

            # tentar descobrir coluna de id da ordem em orders
            order_id_col = _determine_key_column(orders_new)
            if order_id_col and order_id_col in orders_new.columns:
                orders_enriched = orders_new.join(items_agg, orders_new[order_id_col] == items_agg[candidate_fk], how="left").drop(items_agg[candidate_fk])
            else:
                orders_enriched = orders_new
        else:
            orders_enriched = orders_new
    except Exception:
        orders_enriched = orders_new

    # mapear chaves surrogate das dimensões ativas
    for silver_table, dim_name in DIM_TABLES.items():
        path_dim = f"s3a://{NOME_BUCKET}/gold/{dim_name}/"
        if not (HAS_DELTA and DeltaTable.isDeltaTable(spark, path_dim)):
            continue

        dim_df = spark.read.format("delta").load(path_dim).filter(F.col("flag_ativo") == True)
        # identificar chave natural da dimensão
        dim_key = _determine_key_column(dim_df)
        if not dim_key:
            continue

        # procurar coluna de FK correspondente em orders_enriched
        fk_candidate = _find_column_by_keywords(orders_enriched, [silver_table.upper(), silver_table.split("_")[0].upper()])
        if not fk_candidate:
            # tentar por palavras chave comuns
            fk_candidate = _find_column_by_keywords(orders_enriched, ["CLIENTE", "MECANICO", "VEICULO", "FORNECEDOR", "PECA"])

        if fk_candidate and fk_candidate in orders_enriched.columns and dim_key in dim_df.columns:
            map_df = dim_df.select(dim_key, "sk").withColumnRenamed(dim_key, fk_candidate)
            orders_enriched = orders_enriched.join(map_df, on=fk_candidate, how="left").withColumnRenamed("sk", f"SK_{dim_name.upper()}")

    # Escolher coluna ID natural do fato
    fact_key = _determine_key_column(orders_enriched)
    if not fact_key:
        # cria um id sintético
        orders_enriched = orders_enriched.withColumn("ID_FACT", F.md5(F.concat_ws("||", *[F.coalesce(F.col(c).cast("string"), F.lit("")) for c in orders_enriched.columns])))
        fact_key = "ID_FACT"

    # preparar dataframe final do fato
    # garantir coluna de timestamp usada para checkpoint
    if "DATA_HORA_SILVER_TS" in orders_enriched.columns:
        ts_col = "DATA_HORA_SILVER_TS"
    elif "DATA_HORA_SILVER" in orders_enriched.columns:
        orders_enriched = orders_enriched.withColumn("DATA_HORA_SILVER_TS", F.to_timestamp(F.col("DATA_HORA_SILVER")))
        ts_col = "DATA_HORA_SILVER_TS"
    else:
        orders_enriched = orders_enriched.withColumn("DATA_HORA_SILVER_TS", F.current_timestamp())
        ts_col = "DATA_HORA_SILVER_TS"

    # seleciona colunas úteis
    keep_cols = [fact_key, ts_col]
    # adiciona SKs se existirem
    for _, dim_name in DIM_TABLES.items():
        sk_col = f"SK_{dim_name.upper()}"
        if sk_col in orders_enriched.columns:
            keep_cols.append(sk_col)

    # tenta detectar VALOR_TOTAL
    if "VALOR_TOTAL" in orders_enriched.columns:
        keep_cols.append("VALOR_TOTAL")
    else:
        # tenta encontrar algum campo de valor
        val_col = _find_column_by_keywords(orders_enriched, ["VALOR", "VLR", "TOTAL", "PRECO"]) or None
        if val_col:
            keep_cols.append(val_col)

    final_fact = orders_enriched.select(*[c for c in keep_cols if c in orders_enriched.columns])

    # upsert na tabela fato usando Delta (merge) para evitar duplicados
    if HAS_DELTA and DeltaTable.isDeltaTable(spark, path_fact):
        try:
            delta_fact = DeltaTable.forPath(spark, path_fact)
            src_alias = "s"
            tgt_alias = "t"
            merge_condition = f"{tgt_alias}.{fact_key} = {src_alias}.{fact_key}"

            set_map = {c: f"{src_alias}.{c}" for c in final_fact.columns}

            delta_fact.alias(tgt_alias).merge(final_fact.alias(src_alias), merge_condition).whenMatchedUpdate(set=set_map).whenNotMatchedInsert(values=set_map).execute()
            print(f"[FACT] Upsert realizado em {path_fact}")
        except Exception as e:
            print(f"[FACT] Erro no merge do fato: {e}")
            traceback.print_exc()
            # fallback para append
            final_fact.write.format("delta").mode("append").save(path_fact)
    else:
        # escrita inicial
        final_fact.write.format("delta" if HAS_DELTA else "parquet").mode("append").save(path_fact)

    # atualizar checkpoint
    try:
        max_ts = final_fact.agg(F.max(F.col(ts_col)).alias("max_ts")).collect()[0]["max_ts"]
        if max_ts:
            chk_df = spark.createDataFrame([(max_ts,)], ["last_processed"]) 
            if HAS_DELTA:
                chk_df.write.format("delta").mode("overwrite").save(path_checkpoint)
            else:
                chk_df.write.mode("overwrite").parquet(path_checkpoint)
            print(f"[FACT] Checkpoint atualizado: {max_ts}")
    except Exception as e:
        print(f"[FACT] Falha ao atualizar checkpoint: {e}")

    return True


def main():
    validar_variaveis_obrigatorias()

    spark = criar_spark_session()

    try:
        total_ok = 0

        # processar dimensões com SCD Tipo 2
        for silver_table, dim_name in DIM_TABLES.items():
            try:
                if process_dimension(spark, silver_table, dim_name):
                    total_ok += 1
            except Exception as err:
                print(f"[MAIN] Erro na dimensão {dim_name}: {err}")

        # processar fato com carga incremental
        try:
            if process_fact_ordens_servico(spark):
                total_ok += 1
        except Exception as err:
            print(f"[MAIN] Erro no processamento do fato: {err}")

        if total_ok == 0:
            raise RuntimeError("Nenhuma operação foi concluída na camada Gold.")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
