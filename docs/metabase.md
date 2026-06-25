# Metabase e consumo analítico

## Serviço local

O `docker-compose.yml` define somente o serviço Metabase. O Airflow continua sendo administrado pelo Astro CLI em outro ambiente.

O container:

- é construído por `Dockerfile.metabase`;
- baixa o Metabase 0.49.15;
- publica a porta `3000`;
- limita a JVM a 2 GB de memória;
- persiste a aplicação em `metabase-data/`;
- carrega drivers adicionais de `plugins/`;
- expõe um healthcheck em `/api/health`.

## Persistência

`MB_DB_FILE` aponta para `/metabase-data/metabase.db`. O volume local mantém usuários, conexões, perguntas e dashboards entre reinicializações.

!!! warning "Banco interno versionado"

    O banco H2 do Metabase está presente no repositório. Além de aumentar o tamanho do Git, esse arquivo pode transportar configuração específica do ambiente. Evite armazenar segredos sem uma chave de criptografia segura.

## Drivers

O diretório `plugins/` contém drivers para DuckDB, MongoDB, SQL Server, Oracle, Snowflake e outras fontes. Para o desenho atual, o driver DuckDB é o mais relacionado à conexão com MotherDuck.

## Dashboard documentado

Os prints do painel analítico estão registrados na página [Dashboard analítico](dashboard.md). Eles servem como referência visual do consumo esperado da camada Gold no Metabase.

## Fronteira não implementada

O pipeline Gold grava arquivos no Tigris, mas não há no repositório uma das seguintes etapas:

- publicação da Gold em tabelas MotherDuck;
- criação de views DuckDB sobre os objetos do Tigris;
- catálogo compartilhado entre Spark e Metabase;
- job de sincronização para o warehouse.

Portanto, a documentação não assume que o Metabase já consome automaticamente a Gold. Essa conexão precisa ser configurada externamente ou implementada em uma próxima evolução.

## Caminho recomendado para evolução

1. Definir se MotherDuck será o warehouse oficial ou apenas uma camada de consulta.
2. Criar um job versionado de publicação ou sincronização.
3. Registrar esquema, tabelas e estratégia de atualização.
4. Configurar a conexão do Metabase sem expor credenciais.
5. Versionar a definição lógica dos dashboards, quando possível.
