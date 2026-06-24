# Configuração

## Pré-requisitos

- Git;
- Python compatível com as dependências do projeto;
- Astro CLI e um runtime de containers para o Airflow local;
- Docker Compose para o Metabase;
- acesso a um cluster MongoDB Atlas;
- bucket no Tigris ou outro object storage compatível com S3A.

## Variáveis de ambiente

Crie um arquivo `.env` na raiz. Ele é ignorado pelo Git e não deve ser versionado.

```dotenv
MONGO_URI=mongodb+srv://<usuario>:<senha>@<cluster>/
MONGO_DATABASE=gearlog_erp
MONGO_PASSWORD=<senha>

TIGRIS_ENDPOINT=https://fly.storage.tigris.dev
TIGRIS_ACCESS_KEY=<access-key>
TIGRIS_SECRET_KEY=<secret-key>
TIGRIS_BUCKET=projeto-lakehouse-satc

MB_ENCRYPTION_SECRET_KEY=<segredo-longo-e-aleatorio>
```

## Referência das variáveis

| Variável | Obrigatória | Consumidor | Valor padrão |
| --- | --- | --- | --- |
| `MONGO_URI` | Landing e gerador | PyMongo | Nenhum |
| `MONGO_DATABASE` | Não | Landing | `gearlog_erp` |
| `MONGO_PASSWORD` | Para `mongo_default` local | Astro/Airflow | Nenhum |
| `TIGRIS_ENDPOINT` | Sim | Todos os jobs Spark | Nenhum |
| `TIGRIS_ACCESS_KEY` | Sim | Todos os jobs Spark | Nenhum |
| `TIGRIS_SECRET_KEY` | Sim | Todos os jobs Spark | Nenhum |
| `TIGRIS_BUCKET` | Não | Landing, Silver e Gold | `projeto-lakehouse-satc` |
| `MB_ENCRYPTION_SECRET_KEY` | Recomendada | Metabase | Valor inseguro de desenvolvimento |

!!! warning "Bucket da Bronze"

    O job Bronze usa o nome `projeto-lakehouse-satc` diretamente no código. Alterar apenas `TIGRIS_BUCKET` fará Landing, Silver e Gold apontarem para outro bucket, mas não alterará a Bronze.

## Dependências Python

As dependências do pipeline estão em `requirements.txt`:

```text
apache-airflow-providers-mongo
pymongo
faker
pyspark==3.4.1
delta-spark==2.4.0
python-dotenv
```

As dependências da documentação ficam isoladas em `requirements-docs.txt` para não aumentar a imagem do Airflow sem necessidade.

## Credenciais

- Nunca publique o `.env`.
- Não coloque chaves diretamente em DAGs, notebooks ou páginas da documentação.
- Substitua o valor padrão de `MB_ENCRYPTION_SECRET_KEY` fora de desenvolvimento.
- Para produção, prefira um gerenciador de segredos e conexões nativas do Airflow.
