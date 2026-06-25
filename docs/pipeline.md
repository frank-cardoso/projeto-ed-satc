# Processamento por camada

## Resumo

| Camada | Entrada | Transformação principal | Saída | Escrita |
| --- | --- | --- | --- | --- |
| Landing | MongoDB Atlas | Normalização de tipos BSON | JSON no Tigris | `overwrite` |
| Bronze | JSON da Landing | Metadados de carga | Delta Lake | `append` |
| Silver | Delta da Bronze | Padronização, limpeza e deduplicação | Delta Lake | `overwrite` |
| Gold | Delta da Silver | SCD Tipo 2 e fato dimensional | Delta e Parquet | `append`/`overwrite` |

## Landing

Arquivo: `notebooks/job_landing.py`

Para cada uma das dez coleções, o job:

1. Carrega todos os documentos com `find()`.
2. Converte `ObjectId`, `Decimal128`, `Decimal` e datas para tipos serializáveis.
3. Cria um DataFrame Spark em memória.
4. Grava JSON em `landing/<colecao>/`, substituindo a versão anterior.

Uma coleção vazia é ignorada. Se nenhuma coleção for gravada, o job termina com erro.

!!! warning "Uso de memória"

    Todos os documentos de uma coleção são convertidos primeiro para uma lista Python. Isso é adequado à massa acadêmica atual, mas concentra a extração na memória do processo em vez de distribuí-la pelo Spark.

## Bronze

Arquivo: `notebooks/job_bronze.py`

O job lê cada pasta JSON da Landing e adiciona:

- `data_carga`: timestamp atual;
- `nome_arquivo_origem`: nome lógico `<tabela>.json`.

A saída é adicionada a `bronze/<tabela>/` em Delta Lake.

!!! danger "Duplicação entre execuções"

    A Landing é regravada com uma fotografia completa, enquanto a Bronze usa `append`. Assim, cada nova execução pode inserir novamente todos os registros da fonte.

Erros são capturados por tabela e apenas impressos. O script pode encerrar sem erro mesmo quando tabelas falharem.

## Silver

Arquivo: `notebooks/job_silver.py`

As transformações aplicadas são:

1. Remoção de acentos e caracteres especiais dos nomes das colunas.
2. Conversão dos nomes para maiúsculas.
3. Expansão de prefixos como `VL_` para `VALOR_` e `DT_` para `DATA_`.
4. Remoção das colunas técnicas da Bronze.
5. Conversão de strings vazias para nulo.
6. Conversão de strings de data para timestamp.
7. Remoção de IDs nulos.
8. Deduplicação pelo campo `ID`.
9. Inclusão da origem e do timestamp Silver.

A Silver é regravada por completo com `overwriteSchema` habilitado.

!!! note "Escolha do registro duplicado"

    `dropDuplicates(["ID"])` não define uma ordenação. Quando a Bronze contém diferentes versões do mesmo ID, o código não garante explicitamente qual versão será preservada.

## Gold

Arquivo: `notebooks/job_gold.py`

O processamento é dividido em duas partes.

### Dimensões SCD Tipo 2

Para cada dimensão, o job:

1. Remove metadados das camadas anteriores.
2. Determina a chave natural, preferencialmente `ID`.
3. Calcula um hash dos atributos.
4. Cria campos de validade e uma chave substituta.
5. Encerra versões ativas cujo hash mudou.
6. Adiciona chaves novas e novas versões.

Exclusões na origem não encerram registros dimensionais. Apenas alterações presentes na carga são detectadas.

### Fato

A fato parte das ordens de serviço, tenta agregar valores dos itens e associa as dimensões ativas de mecânico e veículo. O resultado é gravado integralmente em Parquet.

Apesar do comentário de “carga incremental”, a operação usada na fato é `overwrite`.

## Comportamento em falhas parciais

| Job | Comportamento |
| --- | --- |
| Landing | Uma exceção não tratada em uma coleção interrompe o job |
| Bronze | Captura erros por tabela e não exige sucesso mínimo |
| Silver | Captura erros por tabela; falha somente se nenhuma tabela for gravada |
| Gold | Captura erros por dimensão/fato; falha somente se nenhuma operação funcionar |
