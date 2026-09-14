from flask import redirect, jsonify, make_response
from flask_openapi3 import OpenAPI, Info, Tag
from flask_cors import CORS
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from models import init_db, SessionLocal, Ativo, Transacao
from schemas import (
    AtivoSchema, AtivoUpdateSchema, AtivoBuscaQuery, AtivoDelQuery,
    AtivoViewSchema, AtivoDetalheViewSchema, ListaAtivosViewSchema,
    TransacaoSchema, TransacaoQuery, TransacaoViewSchema, ListaTransacoesViewSchema,
    DashboardViewSchema, CategoriaDistribuicaoSchema,
    MensagemSchema, ErrorSchema
)

# Inicializa metadados da documentação OpenAPI 3.0
info = Info(
    title="AssetPulse API - Gestão de Ativos & Investimentos",
    version="1.0.0",
    description=(
        "API RESTful desenvolvida em Python com Flask para gerenciamento inteligente de carteiras "
        "de investimentos, acompanhamento de preço médio, proventos e alocação de ativos.\n\n"
        "Desenvolvida com base nas key constraints de Roy Fielding (separação cliente-servidor, "
        "interface uniforme, ausência de estado e arquitetura em camadas)."
    )
)

# Cria a aplicação Flask com OpenAPI nativo
app = OpenAPI(__name__, info=info)

# Configuração permissiva de CORS para aceitar requisições de qualquer origem,
# incluindo o protocolo file:// ao abrir diretamente o index.html no navegador.
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)


@app.after_request
def add_cors_headers(response):
    """Garante cabeçalhos CORS completos em todas as respostas, inclusive OPTIONS."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept"
    return response


# Inicializa as tabelas e dados semente do SQLite
init_db()

# Definição das Tags organizacionais do Swagger UI
ativo_tag = Tag(name="Ativos", description="Rotas para criação, busca, listagem, atualização e exclusão de ativos")
transacao_tag = Tag(name="Transações", description="Rotas para registro e histórico de operações financeiras (Compras, Vendas, Dividendos)")
dashboard_tag = Tag(name="Dashboard", description="Rotas agregadas de métricas e indicadores de desempenho da carteira")


# ==========================================================
# Helpers de Serialização
# ==========================================================

def formatar_transacao(t: Transacao) -> dict:
    """Converte um modelo Transacao em dicionário serializável."""
    return {
        "id": t.id,
        "ativo_id": t.ativo_id,
        "ativo_codigo": t.ativo.codigo if t.ativo else None,
        "tipo": t.tipo,
        "quantidade": float(t.quantidade),
        "preco_unitario": float(t.preco_unitario),
        "valor_total": float(t.valor_total),
        "data_transacao": t.data_transacao.strftime("%Y-%m-%d"),
        "descricao": t.descricao,
        "data_registro": t.data_registro.strftime("%Y-%m-%d %H:%M:%S") if t.data_registro else ""
    }


def formatar_ativo(a: Ativo, detalhado: bool = False) -> dict:
    """Converte um modelo Ativo em dicionário com campos calculados."""
    dados = {
        "id": a.id,
        "codigo": a.codigo,
        "nome": a.nome,
        "categoria": a.categoria,
        "meta_alocacao": float(a.meta_alocacao or 0.0),
        "observacoes": a.observacoes,
        "data_cadastro": a.data_cadastro.strftime("%Y-%m-%d %H:%M:%S") if a.data_cadastro else "",
        "quantidade_custodia": float(a.quantidade_custodia),
        "total_investido": float(round(a.total_investido, 2)),
        "preco_medio": float(a.preco_medio),
        "total_proventos": float(round(a.total_proventos, 2)),
        "total_transacoes": len(a.transacoes)
    }
    if detalhado:
        dados["transacoes"] = [formatar_transacao(t) for t in a.transacoes]
    return dados


# ==========================================================
# Rotas Principais da API
# ==========================================================

@app.route("/")
def index():
    """Redireciona a raiz para a documentação interativa OpenAPI Swagger."""
    return redirect("/openapi/swagger")


# ----------------------------------------------------------
# 1. Rotas de Ativos
# ----------------------------------------------------------

@app.post(
    "/api/ativo",
    tags=[ativo_tag],
    summary="Cadastrar um novo ativo",
    description="Cria um novo ativo na carteira (ex: PETR4, HGLG11, BTC). O código/ticker deve ser único.",
    responses={
        201: AtivoViewSchema,
        400: ErrorSchema,
        409: ErrorSchema
    }
)
def cadastrar_ativo(body: AtivoSchema):
    """Cadastra um novo ativo no banco de dados SQLite."""
    db = SessionLocal()
    try:
        codigo_limpo = body.codigo.strip().upper()

        # Verifica duplicidade
        if db.query(Ativo).filter(Ativo.codigo == codigo_limpo).first():
            return jsonify({
                "mensagem": f"Já existe um ativo cadastrado com o código '{codigo_limpo}'.",
                "detalhes": "Conflito de unicidade de ticker."
            }), 409

        novo_ativo = Ativo(
            codigo=codigo_limpo,
            nome=body.nome.strip(),
            categoria=body.categoria.strip(),
            meta_alocacao=float(body.meta_alocacao),
            observacoes=body.observacoes.strip() if body.observacoes else None,
            data_cadastro=datetime.now()
        )
        db.add(novo_ativo)
        db.commit()
        db.refresh(novo_ativo)

        return jsonify(formatar_ativo(novo_ativo)), 201

    except IntegrityError as e:
        db.rollback()
        return jsonify({"mensagem": "Erro de integridade no banco de dados.", "detalhes": str(e)}), 400
    except Exception as e:
        db.rollback()
        return jsonify({"mensagem": "Erro interno ao cadastrar o ativo.", "detalhes": str(e)}), 500
    finally:
        db.close()


@app.get(
    "/api/ativos",
    tags=[ativo_tag],
    summary="Listar todos os ativos da carteira",
    description="Retorna a lista completa de ativos cadastrados com suas métricas calculadas em tempo real.",
    responses={200: ListaAtivosViewSchema}
)
def listar_ativos():
    """Retorna todos os ativos ordenados por código."""
    db = SessionLocal()
    try:
        ativos = db.query(Ativo).order_by(Ativo.codigo.asc()).all()
        lista_formatada = [formatar_ativo(a) for a in ativos]
        total_investido = sum(a["total_investido"] for a in lista_formatada)
        total_proventos = sum(a["total_proventos"] for a in lista_formatada)

        return jsonify({
            "total_itens": len(lista_formatada),
            "total_investido_geral": round(total_investido, 2),
            "total_proventos_geral": round(total_proventos, 2),
            "ativos": lista_formatada
        }), 200
    finally:
        db.close()


@app.get(
    "/api/ativo",
    tags=[ativo_tag],
    summary="Buscar ativo por ID ou Ticker",
    description="Localiza um ativo específico e retorna todos os seus dados cadastrais juntamente com o histórico completo de transações vinculadas.",
    responses={
        200: AtivoDetalheViewSchema,
        400: ErrorSchema,
        404: ErrorSchema
    }
)
def buscar_ativo(query: AtivoBuscaQuery):
    """Busca ativo por ID ou Código/Ticker."""
    db = SessionLocal()
    try:
        ativo = None
        if query.id:
            ativo = db.query(Ativo).filter(Ativo.id == query.id).first()
        elif query.codigo:
            ativo = db.query(Ativo).filter(Ativo.codigo == query.codigo.strip().upper()).first()
        else:
            return jsonify({
                "mensagem": "Informe ao menos o parâmetro 'id' ou 'codigo' para efetuar a busca.",
                "detalhes": "Parâmetro ausente na consulta."
            }), 400

        if not ativo:
            return jsonify({
                "mensagem": "Ativo não encontrado.",
                "detalhes": f"Nenhum ativo localizado com os parâmetros fornecidos: id={query.id}, codigo={query.codigo}"
            }), 404

        return jsonify(formatar_ativo(ativo, detalhado=True)), 200
    finally:
        db.close()


@app.put(
    "/api/ativo",
    tags=[ativo_tag],
    summary="Atualizar dados de um ativo",
    description="Permite atualizar o nome, categoria, meta de alocação e observações de um ativo existente.",
    responses={
        200: AtivoViewSchema,
        404: ErrorSchema,
        500: ErrorSchema
    }
)
def atualizar_ativo(body: AtivoUpdateSchema):
    """Atualiza as informações cadastrais de um ativo pelo seu ID."""
    db = SessionLocal()
    try:
        ativo = db.query(Ativo).filter(Ativo.id == body.id).first()
        if not ativo:
            return jsonify({
                "mensagem": "Ativo não encontrado para atualização.",
                "detalhes": f"ID {body.id} inexistente."
            }), 404

        if body.nome is not None:
            ativo.nome = body.nome.strip()
        if body.categoria is not None:
            ativo.categoria = body.categoria.strip()
        if body.meta_alocacao is not None:
            ativo.meta_alocacao = float(body.meta_alocacao)
        if body.observacoes is not None:
            ativo.observacoes = body.observacoes.strip()

        db.commit()
        db.refresh(ativo)
        return jsonify(formatar_ativo(ativo)), 200

    except Exception as e:
        db.rollback()
        return jsonify({"mensagem": "Erro interno ao atualizar ativo.", "detalhes": str(e)}), 500
    finally:
        db.close()


@app.delete(
    "/api/ativo",
    tags=[ativo_tag],
    summary="Excluir ativo por ID",
    description="Exclui um ativo da base de dados e todas as suas transações vinculadas em efeito cascata.",
    responses={
        200: MensagemSchema,
        404: ErrorSchema
    }
)
def deletar_ativo(query: AtivoDelQuery):
    """Remove um ativo da base de dados."""
    db = SessionLocal()
    try:
        ativo = db.query(Ativo).filter(Ativo.id == query.id).first()
        if not ativo:
            return jsonify({
                "mensagem": "Ativo não encontrado para exclusão.",
                "detalhes": f"ID {query.id} inexistente."
            }), 404

        codigo = ativo.codigo
        db.delete(ativo)
        db.commit()

        return jsonify({
            "mensagem": f"Ativo '{codigo}' e todas as suas movimentações foram removidos com sucesso!",
            "id": query.id
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({"mensagem": "Erro ao excluir o ativo.", "detalhes": str(e)}), 500
    finally:
        db.close()


# ----------------------------------------------------------
# 2. Rotas de Transações (Relacionamento 1:N)
# ----------------------------------------------------------

@app.post(
    "/api/transacao",
    tags=[transacao_tag],
    summary="Registrar nova transação financeira",
    description="Registra uma operação de COMPRA, VENDA ou DIVIDENDO vinculada a um ativo existente.",
    responses={
        201: TransacaoViewSchema,
        400: ErrorSchema,
        404: ErrorSchema
    }
)
def cadastrar_transacao(body: TransacaoSchema):
    """Cria uma nova movimentação vinculada a um ativo."""
    db = SessionLocal()
    try:
        # Valida existência do ativo
        ativo = db.query(Ativo).filter(Ativo.id == body.ativo_id).first()
        if not ativo:
            return jsonify({
                "mensagem": "Ativo associado não encontrado.",
                "detalhes": f"Nenhum ativo com ID {body.ativo_id} foi localizado."
            }), 404

        tipo_normalizado = body.tipo.strip().upper()
        if tipo_normalizado not in ["COMPRA", "VENDA", "DIVIDENDO"]:
            return jsonify({
                "mensagem": "Tipo de transação inválido.",
                "detalhes": "Os tipos permitidos são: COMPRA, VENDA ou DIVIDENDO."
            }), 400

        nova_transacao = Transacao(
            ativo_id=body.ativo_id,
            tipo=tipo_normalizado,
            quantidade=float(body.quantidade),
            preco_unitario=float(body.preco_unitario),
            data_transacao=body.data_transacao,
            descricao=body.descricao.strip() if body.descricao else None,
            data_registro=datetime.now()
        )
        db.add(nova_transacao)
        db.commit()
        db.refresh(nova_transacao)

        return jsonify(formatar_transacao(nova_transacao)), 201

    except Exception as e:
        db.rollback()
        return jsonify({"mensagem": "Erro ao registrar transação.", "detalhes": str(e)}), 500
    finally:
        db.close()


@app.get(
    "/api/transacoes",
    tags=[transacao_tag],
    summary="Listar transações com filtros opcionais",
    description="Lista as movimentações cadastradas, permitindo filtro por ID do ativo ou tipo da transação.",
    responses={200: ListaTransacoesViewSchema}
)
def listar_transacoes(query: TransacaoQuery):
    """Retorna a lista de transações com suporte a filtros."""
    db = SessionLocal()
    try:
        consulta = db.query(Transacao)
        if query.ativo_id:
            consulta = consulta.filter(Transacao.ativo_id == query.ativo_id)
        if query.tipo:
            consulta = consulta.filter(Transacao.tipo == query.tipo.strip().upper())

        transacoes = consulta.order_by(Transacao.data_transacao.desc(), Transacao.id.desc()).all()
        lista = [formatar_transacao(t) for t in transacoes]

        return jsonify({
            "total_itens": len(lista),
            "transacoes": lista
        }), 200
    finally:
        db.close()


# ----------------------------------------------------------
# 3. Rota de Dashboard e Métricas Consolidadas
# ----------------------------------------------------------

@app.get(
    "/api/dashboard",
    tags=[dashboard_tag],
    summary="Resumo executivo e indicadores da carteira",
    description="Consolida dados da carteira para visualização gerencial: patrimônio alocado, proventos acumulados e percentual por classe de ativos.",
    responses={200: DashboardViewSchema}
)
def obter_dashboard():
    """Calcula e retorna as métricas consolidadas da carteira."""
    db = SessionLocal()
    try:
        ativos = db.query(Ativo).all()
        transacoes_count = db.query(Transacao).count()

        total_investido = sum(a.total_investido for a in ativos)
        total_proventos = sum(a.total_proventos for a in ativos)

        # Agrupamento por categoria
        categorias_map = {}
        for a in ativos:
            cat = a.categoria or "Outros"
            if cat not in categorias_map:
                categorias_map[cat] = {"total_investido": 0.0, "quantidade_ativos": 0}
            categorias_map[cat]["total_investido"] += a.total_investido
            categorias_map[cat]["quantidade_ativos"] += 1

        distribuicao = []
        for cat, dados in categorias_map.items():
            pct = (dados["total_investido"] / total_investido * 100) if total_investido > 0 else 0.0
            distribuicao.append({
                "categoria": cat,
                "total_investido": round(dados["total_investido"], 2),
                "percentual": round(pct, 1),
                "quantidade_ativos": dados["quantidade_ativos"]
            })

        distribuicao.sort(key=lambda x: x["total_investido"], reverse=True)

        return jsonify({
            "patrimonio_investido": round(total_investido, 2),
            "total_proventos": round(total_proventos, 2),
            "quantidade_ativos": len(ativos),
            "quantidade_transacoes": transacoes_count,
            "distribuicao_categorias": distribuicao
        }), 200
    finally:
        db.close()


# Ponto de entrada para execução direta
if __name__ == "__main__":
    print("Iniciando AssetPulse API na porta 5000...")
    print("Swagger UI disponível em: http://127.0.0.1:5000/openapi/swagger")
    app.run(host="0.0.0.0", port=5000, debug=True)
