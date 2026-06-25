# Projeto ED SATC

Projeto de Data Lakehouse com arquitetura medallion (Landing, Bronze, Silver, Gold) para processamento de dados de um sistema ERP de oficina mecânica.

## Tecnologias Utilizadas

### Serviços em Nuvem
- **MongoDB Atlas**: Banco de dados NoSQL para armazenamento dos dados de origem (mecânicos, fornecedores, clientes, veículos, peças, ordens de serviço, etc.)
- **Tigris**: Storage S3-compatible para armazenamento do Data Lakehouse (Landing, Bronze, Silver, Gold)
- **MotherDuck**: Data warehouse baseado em DuckDB para conexão com Power BI e análise de dados

### Ferramentas Locais
- **Astro CLI**: Orquestração de workflows Apache Airflow para desenvolvimento local
- **Apache Airflow**: Orquestração de pipelines de dados
- **Apache Spark**: Processamento de dados em larga escala com PySpark
- **Delta Lake**: Formato de dados ACID para confiabilidade e versionamento
- **Power BI**: Ferramenta de modelagem de dados, visualização e relatórios analíticos
- **MkDocs**: Gerador de documentação estática para documentação técnica do projeto
- **mkdocs-jupyter**: Plugin para renderizar notebooks e scripts Python na documentação

## Arquitetura do Projeto

### Camadas do Data Lakehouse

1. **Landing Zone**: Dados brutos extraídos do MongoDB Atlas em formato JSON
2. **Bronze Layer**: Dados brutos processados em formato Delta Lake com metadados de carga
3. **Silver Layer**: Dados limpos, padronizados e com quality rules aplicadas
4. **Gold Layer**: Modelo dimensional com dimensões (SCD Type 2) e tabelas fato

### Estrutura de Pastas

```text
projeto-ed-satc/
├── dags/                # DAGs do Airflow
│   ├── dag_landing.py   # DAG para ingestão na camada Landing
│   ├── dag_bronze.py    # DAG para processamento da camada Bronze
│   ├── dag_silver.py    # DAG para processamento da camada Silver
│   └── dag_gold.py      # DAG para processamento da camada Gold
├── notebooks/           # Scripts PySpark
│   ├── job_landing.py   # Extração do MongoDB para Landing
│   ├── job_bronze.py    # Processamento Landing -> Bronze
│   ├── job_silver.py    # Processamento Bronze -> Silver
│   └── job_gold.py      # Processamento Silver -> Gold
├── .env                 # Variáveis de ambiente (gitignore)
├── airflow_settings.yaml # Configurações do Airflow local
└── docker-compose.yml  # Compose para serviços auxiliares
```

## Configuração

### Variáveis de Ambiente (.env)

```bash
MONGO_URI="mongodb+srv://<user>:<password>@<cluster>/"
MONGO_PASSWORD="<password>"
TIGRIS_ENDPOINT="[https://fly.storage.tigris.dev](https://fly.storage.tigris.dev)"
TIGRIS_ACCESS_KEY="<access_key>"
TIGRIS_SECRET_KEY="<secret_key>"
```

### Execução com Astro CLI

```bash
# Iniciar o ambiente de desenvolvimento
astro dev start

# Acessar a interface do Airflow
# URL: http://projeto-ed-satc.localhost:6563
# User: admin
# Password: admin

# Reiniciar o ambiente (após alterações nos arquivos)
astro dev restart

# Parar o ambiente
astro dev stop
```

## Documentação do projeto

A documentação técnica completa está em `docs/` e usa MkDocs Material.

```bash
python -m pip install -r requirements-docs.txt
python -m mkdocs serve
```

Para validar e gerar o site estático:

```bash
python -m mkdocs build --strict
```

Para publicar no GitHub Pages:

```bash
python -m mkdocs gh-deploy
```

## Referências

- [Astro CLI Documentation](https://www.astronomer.io/docs/astro/cli/develop-project)
- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [Apache Spark Documentation](https://spark.apache.org/docs/)
- [Delta Lake Documentation](https://docs.delta.io/)
- [MongoDB Atlas Documentation](https://www.mongodb.com/docs/atlas/)
- [Tigris Documentation](https://docs.tigrisdata.com/)
- [MotherDuck Documentation](https://motherduck.com/docs)
- [Power BI Documentation](https://learn.microsoft.com/pt-br/power-bi/)
- [MkDocs Documentation](https://www.mkdocs.org/)
