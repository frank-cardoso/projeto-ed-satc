# Guia de contribuição

## Fluxo recomendado

1. Crie uma branch a partir de `main`.
2. Faça alterações pequenas e relacionadas a um único objetivo.
3. Atualize a documentação quando mudar contratos, variáveis, tabelas ou operação.
4. Execute as validações locais disponíveis.
5. Abra um pull request descrevendo impacto e forma de teste.

## Validações

### DAGs

No ambiente Astro:

```bash
astro dev pytest
```

### Documentação

```bash
python -m mkdocs build --strict
```

O modo estrito transforma avisos de navegação, links e configuração em falhas de build.

## Convenções para jobs

- Validar variáveis antes de criar a sessão Spark.
- Encerrar `SparkSession` e clientes externos em blocos `finally`.
- Registrar início, sucesso, quantidade e falha por entidade.
- Não suprimir falhas obrigatórias apenas com `print()`.
- Tornar a estratégia de escrita explícita: `append`, `overwrite` ou `merge`.
- Evitar nomes de bucket e credenciais fixos no código.
- Manter o mesmo conjunto de entidades centralizado ou documentar diferenças.

## Convenções para dados

- Documentar o grão antes de criar uma tabela fato.
- Definir chaves naturais e substitutas de forma explícita.
- Incluir uma regra determinística para deduplicação.
- Definir o tratamento de inserções, alterações e exclusões.
- Não alterar esquemas publicados sem registrar compatibilidade e migração.

## Convenções para documentação

- Descrever primeiro o comportamento implementado.
- Marcar propostas futuras como planejadas.
- Nunca inserir credenciais reais em exemplos.
- Atualizar diagramas quando o fluxo mudar.
- Preferir links relativos entre páginas.
