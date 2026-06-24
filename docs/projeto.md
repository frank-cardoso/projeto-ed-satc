# Visão geral

## Objetivo

O projeto demonstra a construção de um Data Lakehouse com arquitetura Medallion para dados de uma oficina mecânica. Seu foco é organizar dados operacionais em camadas progressivamente mais preparadas para análise.

O domínio simulado inclui clientes, veículos, mecânicos, peças, fornecedores, ordens de serviço, pagamentos, agendamentos e avaliações.

## Escopo

O repositório contém quatro partes principais:

1. **Geração da massa de dados:** cria registros fictícios com Faker e os insere no MongoDB Atlas.
2. **Pipeline de dados:** executa jobs PySpark para Landing, Bronze, Silver e Gold.
3. **Orquestração:** expõe uma DAG diária do Airflow para cada camada.
4. **Consumo analítico:** disponibiliza um container Metabase com persistência e drivers de bancos de dados.

## O que está implementado

- Geração de dez coleções no banco `gearlog_erp`.
- Extração completa do MongoDB para JSON no Tigris.
- Persistência da Bronze e Silver em Delta Lake.
- Padronização e deduplicação básica na Silver.
- Cinco dimensões Gold com controle de histórico SCD Tipo 2.
- Uma tabela fato simplificada de ordens de serviço.
- Quatro DAGs independentes no Airflow.
- Container local do Metabase com armazenamento persistente.

## O que ainda é planejado ou parcial

- Encadeamento automático das quatro DAGs.
- Carga explícita da Gold no MotherDuck.
- Modelo fato completo com pagamentos, itens, datas e demais dimensões.
- Regras de qualidade específicas por entidade.
- Testes unitários e de integração para as transformações.
- Monitoramento de volume, SLA e qualidade dos dados.

## Vocabulário do projeto

| Termo | Significado neste projeto |
| --- | --- |
| Coleção | Conjunto de documentos operacionais no MongoDB |
| Tabela | Conjunto de dados de uma entidade nas camadas do Lakehouse |
| Camada | Estágio de armazenamento e tratamento dos dados |
| Chave natural | Identificador proveniente da fonte, normalmente `ID` |
| Chave substituta | Identificador de uma versão dimensional, armazenado em `sk` |
| SCD Tipo 2 | Estratégia que encerra uma versão antiga e cria outra quando atributos mudam |
| DAG | Definição de workflow agendado no Apache Airflow |
