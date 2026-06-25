# Qualidade e limitações

Esta página registra o comportamento observado no código atual. Ela não representa falhas de infraestrutura externa nem resultados de uma execução completa em nuvem.

## Validações existentes

### Landing

- Verifica variáveis obrigatórias.
- Ignora coleções vazias.
- Normaliza tipos que não são diretamente serializáveis em JSON.

### Silver

- Padroniza nomes de colunas.
- Converte strings vazias para nulo.
- Converte campos de data.
- Elimina IDs nulos.
- Deduplica por ID.

### Gold

- Detecta alterações dimensionais por hash.
- Mantém datas de vigência e flag ativa.
- Usa chave substituta por versão.

### DAGs

- Possuem tags.
- São carregadas pelo teste de integridade do Airflow.
- Três das quatro DAGs atendem à regra de duas tentativas.

## Limitações conhecidas

| Prioridade | Limitação | Impacto |
| --- | --- | --- |
| Alta | DAGs sem encadeamento | Uma camada pode começar antes de sua entrada estar pronta |
| Alta | Bronze completa em `append` | Reexecuções podem duplicar toda a fonte |
| Alta | Erros Bronze apenas impressos | A tarefa pode parecer bem-sucedida com tabelas ausentes |
| Alta | MotherDuck sem carga versionada | Não há caminho reproduzível entre Gold e BI |
| Média | Deduplicação Silver sem ordenação | A versão preservada de um ID não é explicitamente determinada |
| Média | Fato Gold simplificada | Análises financeiras e operacionais ficam muito limitadas |
| Média | Bucket Bronze fixo | Configurações com outro bucket ficam inconsistentes |
| Média | Fato marcada como incremental, mas usa `overwrite` | Histórico da fato não é preservado |
| Média | Exclusões não tratadas no SCD | Dimensões removidas da fonte permanecem ativas |
| Baixa | Imports duplicados no job Gold | Reduz clareza e manutenção do código |

## Cobertura de testes

O único teste versionado é um teste genérico de integridade de DAGs. Ainda não existem testes para:

- normalização BSON;
- regras de nomes da Silver;
- conversão de datas;
- deduplicação;
- SCD Tipo 2;
- relacionamentos e medidas da fato;
- leitura e escrita no Tigris;
- integração com MotherDuck ou Power BI.

## Critérios sugeridos para evolução

- Uma DAG só deve terminar com sucesso quando todas as tabelas obrigatórias forem processadas.
- Cada carga deve possuir um identificador e métricas de quantidade.
- A Bronze deve ter estratégia explícita de idempotência.
- A Silver deve escolher registros duplicados por uma regra temporal determinística.
- A Gold deve possuir testes para novas chaves, alterações, registros inalterados e exclusões.
- O modelo analítico deve definir claramente grão, dimensões e medidas de cada fato.