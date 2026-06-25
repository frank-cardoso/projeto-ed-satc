# Power BI e consumo analítico

## Ambiente de consumo

Diferente da orquestração que roda localmente via Astro CLI, o Power BI atua como uma ferramenta externa ao pipeline de dados. O consumo e a visualização devem ser feitos através do **Power BI Desktop** (para modelagem e desenvolvimento das análises) e publicados no **Serviço do Power BI** (na nuvem, caso haja necessidade de compartilhamento).

Com isso, a arquitetura do projeto não requer containers adicionais no `docker-compose.yml` para a camada de visualização, aliviando o consumo de recursos da máquina local.

## Persistência e versionamento

O desenvolvimento no Power BI é tradicionalmente salvo em arquivos `.pbix`.

!!! warning "Arquivos binários no repositório"

    O arquivo `.pbix` é um binário que pode salvar dados em cache importados para o modelo. Commitá-lo com dados carregados inflará rapidamente o tamanho do repositório Git, além de apresentar riscos de vazamento de informações. Ao versionar o projeto, prefira salvar o arquivo vazio (sem dados carregados) ou explore o formato de projeto do Power BI (`.pbip`), que salva metadados em texto plano e facilita o versionamento.

## Conectores

Para que o Power BI consuma os dados finais gerados pelo Lakehouse, a abordagem de conexão depende de onde os dados estão expostos:

- **ODBC / MotherDuck:** A rota arquitetural mais aderente ao projeto é utilizar o MotherDuck como warehouse. O Power BI pode se conectar a ele utilizando um driver ODBC previamente configurado no sistema operacional.
- **Leitura Direta:** Em caráter de homologação ou testes rápidos, o Power BI também possui capacidade nativa de ler os arquivos Delta/Parquet diretamente, embora perca as vantagens de processamento do warehouse.

## Dashboard documentado

Os prints do painel analítico estão registrados na página [Dashboard analítico](dashboard.md). Eles servem como referência visual do consumo esperado da camada Gold no Power BI.

## Fronteira não implementada

O pipeline Gold atual grava os dados no Tigris, mas não há no repositório uma das seguintes etapas automatizadas:

- publicação da Gold em tabelas no MotherDuck;
- criação de views DuckDB sobre os objetos do Tigris;
- integração de um catálogo compartilhado;
- job de sincronização para o warehouse analítico.

Portanto, a documentação não assume que o Power BI já consome os dados da Gold em tempo real. Essa conexão precisa ser provisionada manualmente pelo desenvolvedor ou implementada em uma próxima evolução do pipeline.

## Caminho recomendado para evolução

1. Definir se o MotherDuck será mantido como o warehouse oficial ou se será substituída a estratégia de consumo.
2. Criar um job versionado no Airflow para publicação ou sincronização dos dados da Gold para o warehouse.
3. Registrar esquema, tabelas e política de atualização incremental.
4. Configurar a conexão do Power BI via ODBC garantindo a segurança de credenciais.
5. Adotar o formato de salvamento `.pbip` para versionar a semântica e as medidas DAX de forma transparente no GitHub.