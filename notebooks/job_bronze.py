import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, lit
from dotenv import load_dotenv

load_dotenv()

S3_ENDPOINT = os.getenv("TIGRIS_ENDPOINT")
AWS_ACCESS_KEY = os.getenv("TIGRIS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("TIGRIS_SECRET_KEY")

spark = SparkSession.builder \
    .appName("Job_Bronze_Layer") \
    .config("spark.jars.packages", "io.delta:delta-core_2.12:2.4.0,org.apache.hadoop:hadoop-aws:3.3.4") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .config("spark.hadoop.fs.s3a.endpoint", S3_ENDPOINT) \
    .config("spark.hadoop.fs.s3a.access.key", AWS_ACCESS_KEY) \
    .config("spark.hadoop.fs.s3a.secret.key", AWS_SECRET_KEY) \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .getOrCreate()

nome_bucket = "projeto-lakehouse-satc"
tabelas = [
    "mecanicos", "fornecedores", "clientes", "veiculos",
    "pecas_estoque", "ordens_servico", "itens_os", 
    "pagamentos", "agendamentos", "avaliacoes"
]

for tabela in tabelas:
    print(f"Iniciando camada Bronze para a tabela: {tabela}")
    
    path_landing = f"s3a://{nome_bucket}/landing/{tabela}/"
    path_bronze = f"s3a://{nome_bucket}/bronze/{tabela}/"
    
    try:
        df_origem = spark.read.json(path_landing)
        
        df_bronze = df_origem \
            .withColumn("data_carga", current_timestamp()) \
            .withColumn("nome_arquivo_origem", lit(f"{tabela}.json"))
            
        df_bronze.write \
            .format("delta") \
            .mode("append") \
            .save(path_bronze)
            
        print(f"✅ Sucesso: Tabela {tabela} salva em Delta na Bronze!")
        
    except Exception as e:
        print(f"❌ Aviso: Erro na tabela {tabela} - {e}")

spark.stop()