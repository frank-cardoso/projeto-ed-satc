# Execução local

## 1. Preparar as variáveis

Crie o `.env` conforme a página de [configuração](configuracao.md). Verifique também se o bucket configurado existe e aceita operações pela API S3.

## 2. Popular a fonte

Esta etapa é necessária apenas para criar a massa fictícia inicial.

```bash
python include/gerador_dados.py
```

!!! danger "Geração não idempotente"

    O gerador usa `insert_many()` com IDs fixos e não limpa as coleções. Uma segunda execução sobre a mesma base pode falhar por chaves duplicadas.

## 3. Iniciar o Airflow

Na raiz do projeto:

```bash
astro dev start
```

Interface local esperada:

- URL: `http://projeto-ed-satc.localhost:6563`
- usuário: `admin`
- senha: `admin`

Comandos úteis:

```bash
astro dev restart
astro dev logs
astro dev stop
```

## 4. Executar o pipeline

Pela interface do Airflow, dispare manualmente as DAGs nesta ordem:

1. `ingestao_camada_landing`;
2. `ingestao_camada_bronze`;
3. `processamento_camada_silver`;
4. `processamento_camada_gold`.

Aguarde a conclusão de cada etapa antes de iniciar a próxima.

## 5. Acessar o Power BI

Como o Power BI não exige a execução de containers locais via Docker Compose, o consumo dos dados tratados deve ser feito diretamente no aplicativo desktop.

1. Abra o arquivo do projeto (`.pbix` ou `.pbip`) no Power BI Desktop.
2. Atualize as fontes de dados para garantir que a ferramenta esteja lendo as informações mais recentes da camada Gold (ou do MotherDuck, dependendo do conector configurado).

## 6. Servir a documentação

=== "PowerShell"

    ```powershell
    py -m venv .venv-docs
    .\.venv-docs\Scripts\Activate.ps1
    python -m pip install -r requirements-docs.txt
    python -m mkdocs serve
    ```

=== "Bash"

    ```bash
    python -m venv .venv-docs
    source .venv-docs/bin/activate
    python -m pip install -r requirements-docs.txt
    python -m mkdocs serve
    ```

A documentação fica disponível em `http://127.0.0.1:8000`.

Para gerar os arquivos estáticos:

    ```bash
    python -m mkdocs build --strict
    ```

A saída será criada em `site/`, pasta já ignorada pelo Git.

O projeto gera arquivos `.html` explícitos. Assim, também é possível abrir
`site/index.html` diretamente no navegador, embora `mkdocs serve` continue sendo
a opção recomendada durante a edição.
