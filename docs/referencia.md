# Referência do repositório

## Estrutura

```text
projeto-ed-satc/
├── .astro/                  # Configuração local do Astro
├── dags/                    # Definições das DAGs do Airflow
├── docs/                    # Fontes desta documentação
├── include/                 # Utilitários e gerador de massa
├── metabase-data/           # Banco interno persistente do Metabase
├── notebooks/               # Jobs PySpark das quatro camadas
├── plugins/                 # Drivers adicionais do Metabase
├── tests/dags/              # Testes de integridade das DAGs
├── airflow_settings.yaml    # Conexões, variáveis e pools locais
├── docker-compose.yml       # Serviço local do Metabase
├── Dockerfile               # Imagem do Astro Runtime
├── Dockerfile.metabase      # Imagem do Metabase
├── mkdocs.yml               # Configuração desta documentação
├── requirements.txt         # Dependências do pipeline
└── requirements-docs.txt    # Dependências da documentação
```

## Mapeamento DAG → job

| Definição Airflow | DAG ID | Job |
| --- | --- | --- |
| `dags/dag_landing.py` | `ingestao_camada_landing` | `notebooks/job_landing.py` |
| `dags/dag_bronze.py` | `ingestao_camada_bronze` | `notebooks/job_bronze.py` |
| `dags/dag_silver.py` | `processamento_camada_silver` | `notebooks/job_silver.py` |
| `dags/dag_gold.py` | `processamento_camada_gold` | `notebooks/job_gold.py` |

## Caminhos de armazenamento

Todos os jobs usam URIs no formato `s3a://<bucket>/<camada>/<entidade>/`.

| Camada | Formato | Exemplo |
| --- | --- | --- |
| Landing | JSON | `s3a://projeto-lakehouse-satc/landing/clientes/` |
| Bronze | Delta | `s3a://projeto-lakehouse-satc/bronze/clientes/` |
| Silver | Delta | `s3a://projeto-lakehouse-satc/silver/clientes/` |
| Dimensão Gold | Delta | `s3a://projeto-lakehouse-satc/gold/dim_cliente/` |
| Fato Gold | Parquet | `s3a://projeto-lakehouse-satc/gold/fato_ordens_servico/` |

## Arquivos de configuração

### `Dockerfile`

Estende `quay.io/astronomer/astro-runtime:10.4.0` e instala um JRE para atender às necessidades do Spark.

### `airflow_settings.yaml`

É destinado ao desenvolvimento local. Cadastra conexões, variáveis e pool quando o ambiente Astro inicia.

### `docker-compose.yml`

Constrói e executa somente o Metabase em uma rede Docker chamada `data-lake-network`.

### `.gitignore`

Protege arquivos `.env`, credenciais, ambientes virtuais, caches Python, logs do Airflow e a saída estática `site/` do MkDocs.
