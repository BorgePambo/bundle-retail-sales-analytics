"""
Testes estruturais do Databricks Bundle.

Objetivo:
- Validar a configuração do Bundle antes do deploy.
- Não precisa de Spark, Databricks ou credenciais.
- Descobre os arquivos dinamicamente.

Executar:
    pytest tests/test_bundle.py -v
"""

import re
from pathlib import Path

import pytest
import yaml

# ============================================================
# CONFIGURAÇÃO
# ============================================================

REPO = Path(__file__).resolve().parent.parent

LAYERS = ("bronze", "silver", "gold")

SQL_FILES = sorted(
    (REPO / "src").rglob("*.sql")
)

CREATE = re.compile(
    r"CREATE\s+OR\s+(?:REFRESH|REPLACE)\s+"
    r"(?:STREAMING\s+TABLE|MATERIALIZED\s+VIEW)\s+"
    r"([^\s(;]+)",
    re.IGNORECASE,
)


# ============================================================
# HELPERS
# ============================================================

def _pipeline() -> dict:
    """
    Encontra dinamicamente o primeiro pipeline
    declarado em resources/*.yml.
    """

    resources_dir = REPO / "resources"

    for yml in sorted(resources_dir.glob("*.yml")):
        doc = yaml.safe_load(yml.read_text(encoding="utf-8")) or {}

        pipelines = (
            (doc.get("resources") or {})
            .get("pipelines") or {}
        )

        for spec in pipelines.values():
            return spec or {}

    raise AssertionError(
        "Nenhum recurso 'pipelines:' encontrado em resources/*.yml"
    )


def _resources() -> dict:
    """
    Retorna todos os recursos declarados no Bundle.
    """

    resources_dir = REPO / "resources"

    resultado = {
        "pipelines": {},
        "schemas": {},
    }

    for yml in sorted(resources_dir.glob("*.yml")):
        doc = yaml.safe_load(yml.read_text(encoding="utf-8")) or {}
        resources = doc.get("resources") or {}

        resultado["pipelines"].update(
            resources.get("pipelines") or {}
        )

        resultado["schemas"].update(
            resources.get("schemas") or {}
        )

    return resultado


def ids(path: Path) -> str:
    return str(path.relative_to(REPO))


# ============================================================
# DESCOBERTA
# ============================================================

PIPELINE = _pipeline()
RESOURCES = _resources()


# ============================================================
# TESTES DO BUNDLE
# ============================================================

def test_existem_arquivos_sql():
    """
    O pipeline precisa ter transformações SQL.
    """

    assert SQL_FILES, (
        "Nenhum arquivo .sql encontrado em src/"
    )


def test_pipeline_sales_pipeline_existe():
    """
    O Bundle deve declarar o pipeline sales_pipeline.
    """

    pipelines = RESOURCES["pipelines"]

    assert "sales_pipeline" in pipelines, (
        "Recurso 'sales_pipeline' não encontrado "
        "em resources/*.yml"
    )


def test_pipeline_tem_nome():
    """
    O pipeline precisa possuir uma propriedade name.
    """

    assert PIPELINE.get("name"), (
        "sales_pipeline não possui 'name'"
    )


def test_pipeline_e_serverless():
    """
    Valida a configuração serverless esperada.
    """

    assert PIPELINE.get("serverless") is True, (
        "sales_pipeline deveria estar configurado "
        "com serverless: true"
    )


def test_pipeline_nao_e_continuo():
    """
    O projeto usa continuous: false.
    """

    assert PIPELINE.get("continuous") is False, (
        "sales_pipeline deveria usar continuous: false"
    )


def test_pipeline_nao_e_development():
    """
    Evita deploy acidental em modo development.
    """

    assert PIPELINE.get("development") is False, (
        "sales_pipeline deveria usar development: false"
    )


# ============================================================
# SQL
# ============================================================

def test_pipeline_carrega_os_sqls():
    """
    Verifica se os SQLs principais do projeto
    estão declarados nas libraries do pipeline.
    """

    libraries = PIPELINE.get("libraries") or []

    caminhos = set()

    for library in libraries:
        file_spec = library.get("file") or {}
        path = file_spec.get("path")

        if path:
            caminhos.add(
                Path(path).as_posix()
            )

    esperados = {
        "../src/transformations/bronze/sales_retails.sql",
        "../src/transformations/silver/sales_retails.sql",
        "../src/transformations/gold/dim_produto.sql",
        "../src/transformations/gold/dim_cliente.sql",
        "../src/transformations/gold/dim_localidade.sql",
        "../src/transformations/gold/dim_tempo.sql",
        "../src/transformations/gold/fct_vendas.sql",
    }

    faltando = esperados - caminhos

    assert not faltando, (
        f"SQLs não carregados pelo pipeline: {faltando}"
    )


@pytest.mark.parametrize(
    "sql",
    SQL_FILES,
    ids=ids,
)
def test_sql_eh_declaracao_valida(sql):
    """
    Verifica se cada SQL contém CREATE OR REFRESH
    STREAMING TABLE ou MATERIALIZED VIEW.
    """

    texto = sql.read_text(encoding="utf-8")

    assert CREATE.search(texto), (
        f"{ids(sql)} não contém uma declaração "
        "CREATE OR REFRESH válida"
    )


# ============================================================
# CAMADAS
# ============================================================

@pytest.mark.parametrize(
    "sql",
    SQL_FILES,
    ids=ids,
)
def test_sql_esta_em_uma_camada_valida(sql):
    """
    Cada transformação deve estar em:
        bronze/
        silver/
        gold/
    """

    camada = sql.parent.name.lower()

    assert camada in LAYERS, (
        f"{ids(sql)} está fora das camadas "
        f"esperadas: {LAYERS}"
    )


def test_bronze_existe():
    assert (REPO / "src/transformations/bronze").is_dir()


def test_silver_existe():
    assert (REPO / "src/transformations/silver").is_dir()


def test_gold_existe():
    assert (REPO / "src/transformations/gold").is_dir()


def test_bronze_tem_sql():
    arquivos = list(
        (REPO / "src/transformations/bronze").glob("*.sql")
    )

    assert arquivos, "Bronze não possui nenhum SQL"


def test_silver_tem_sql():
    arquivos = list(
        (REPO / "src/transformations/silver").glob("*.sql")
    )

    assert arquivos, "Silver não possui nenhum SQL"


def test_gold_tem_sql():
    arquivos = list(
        (REPO / "src/transformations/gold").glob("*.sql")
    )

    assert arquivos, "Gold não possui nenhum SQL"


# ============================================================
# CONFIGURATION
# ============================================================

def test_pipeline_possui_configuration():
    """
    O pipeline deve possuir configuration,
    conforme a configuração do projeto.
    """

    configuration = PIPELINE.get("configuration") or {}

    assert configuration, (
        "sales_pipeline não possui configuration"
    )


def test_pipeline_possui_bundle_source_path():
    """
    Valida bundle.sourcePath.
    """

    configuration = PIPELINE.get("configuration") or {}

    assert "bundle.sourcePath" in configuration, (
        "bundle.sourcePath não encontrado no pipeline"
    )


# ============================================================
# FILTER
# ============================================================

def test_pipeline_possui_filter():
    """
    O pipeline deve possuir filters.include.
    """

    filters = PIPELINE.get("filters") or {}
    include = filters.get("include") or []

    assert include, (
        "sales_pipeline não possui filters.include"
    )


def test_filter_include_transformations():
    """
    O filtro deve incluir src/transformations.
    """

    filters = PIPELINE.get("filters") or {}
    include = filters.get("include") or []

    assert any(
        "src/transformations" in str(item)
        for item in include
    ), (
        "filters.include não inclui "
        "src/transformations"
    )


# ============================================================
# CONSISTÊNCIA DOS ARQUIVOS
# ============================================================

def test_nao_existam_sqls_vazios():
    """
    Nenhum SQL deve estar vazio.
    """

    vazios = []

    for sql in SQL_FILES:
        texto = sql.read_text(encoding="utf-8").strip()

        if not texto:
            vazios.append(ids(sql))

    assert not vazios, (
        f"SQLs vazios encontrados: {vazios}"
    )


def test_gold_possui_dimensoes_e_fato():
    """
    Valida as transformações Gold esperadas
    pelo modelo do projeto.
    """

    gold = REPO / "src/transformations/gold"

    esperados = {
        "dim_cliente.sql",
        "dim_localidade.sql",
        "dim_produto.sql",
        "dim_tempo.sql",
        "fct_vendas.sql",
    }

    encontrados = {
        arquivo.name
        for arquivo in gold.glob("*.sql")
    }

    faltando = esperados - encontrados

    assert not faltando, (
        f"Transformações Gold ausentes: {faltando}"
    )
