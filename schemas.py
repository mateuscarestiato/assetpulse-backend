from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import date


# ==========================================================
# Schemas de Entrada (Requisição)
# ==========================================================

class AtivoSchema(BaseModel):
    """Esquema para criação de um novo ativo na carteira."""
    codigo: str = Field(
        ...,
        min_length=2,
        max_length=20,
        description="Código ou Ticker de negociação do ativo",
        json_schema_extra={"example": "VALE3"}
    )
    nome: str = Field(
        ...,
        min_length=2,
        max_length=120,
        description="Razão social ou nome de exibição do ativo",
        json_schema_extra={"example": "Vale S.A."}
    )
    categoria: str = Field(
        ...,
        description="Categoria ou classe do ativo (ex: Ações, FIIs, Criptomoedas, Renda Fixa, ETFs)",
        json_schema_extra={"example": "Ações"}
    )
    meta_alocacao: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Percentual objetivo de alocação da carteira (0 a 100%)",
        json_schema_extra={"example": 15.0}
    )
    observacoes: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Notas ou teses de investimento sobre o ativo",
        json_schema_extra={"example": "Líder global na exportação de minério de ferro."}
    )


class AtivoUpdateSchema(BaseModel):
    """Esquema para atualização dos dados cadastrais de um ativo."""
    id: int = Field(..., description="ID identificador único do ativo a ser atualizado", json_schema_extra={"example": 1})
    nome: Optional[str] = Field(None, min_length=2, max_length=120, description="Novo nome do ativo", json_schema_extra={"example": "Petrobras Preferencial"})
    categoria: Optional[str] = Field(None, description="Nova categoria do ativo", json_schema_extra={"example": "Ações"})
    meta_alocacao: Optional[float] = Field(None, ge=0.0, le=100.0, description="Nova meta percentual de alocação", json_schema_extra={"example": 22.5})
    observacoes: Optional[str] = Field(None, max_length=255, description="Novas anotações", json_schema_extra={"example": "Atualização de tese de dividendos"})


class AtivoBuscaQuery(BaseModel):
    """Parâmetros de busca para localizar um ativo específico."""
    id: Optional[int] = Field(None, description="ID único do ativo cadastrado")
    codigo: Optional[str] = Field(None, description="Código/Ticker do ativo (busca case-insensitive)")


class AtivoDelQuery(BaseModel):
    """Parâmetro obrigatório para exclusão de um ativo."""
    id: int = Field(..., description="ID identificador do ativo a ser excluído")


class TransacaoSchema(BaseModel):
    """Esquema para inclusão de uma nova transação financeira vinculada a um ativo."""
    ativo_id: int = Field(..., description="ID do ativo existente ao qual a transação pertence", json_schema_extra={"example": 1})
    tipo: str = Field(..., description="Tipo da movimentação: COMPRA, VENDA ou DIVIDENDO", json_schema_extra={"example": "COMPRA"})
    quantidade: float = Field(..., gt=0, description="Quantidade negociada", json_schema_extra={"example": 50.0})
    preco_unitario: float = Field(..., gt=0, description="Preço unitário pago ou recebido por cota/ação", json_schema_extra={"example": 35.20})
    data_transacao: date = Field(default_factory=date.today, description="Data em que a operação ocorreu (AAAA-MM-DD)", json_schema_extra={"example": "2025-03-12"})
    descricao: Optional[str] = Field(default=None, max_length=255, description="Detalhes adicionais ou corretora utilizada", json_schema_extra={"example": "Compra regular via corretora"})


class TransacaoQuery(BaseModel):
    """Parâmetros opcionais para filtragem da listagem de transações."""
    ativo_id: Optional[int] = Field(None, description="Filtrar movimentações por ID de um ativo específico")
    tipo: Optional[str] = Field(None, description="Filtrar por tipo (COMPRA, VENDA, DIVIDENDO)")


# ==========================================================
# Schemas de Saída (Respostas)
# ==========================================================

class TransacaoViewSchema(BaseModel):
    """Estrutura detalhada de retorno para uma transação."""
    id: int = Field(..., description="ID único da transação")
    ativo_id: int = Field(..., description="ID do ativo associado")
    ativo_codigo: Optional[str] = Field(None, description="Ticker do ativo para facilitar visualização")
    tipo: str = Field(..., description="Tipo da operação")
    quantidade: float = Field(..., description="Quantidade operada")
    preco_unitario: float = Field(..., description="Preço unitário")
    valor_total: float = Field(..., description="Valor total calculado da operação")
    data_transacao: str = Field(..., description="Data da operação formatada (AAAA-MM-DD)")
    descricao: Optional[str] = Field(None, description="Descrição")
    data_registro: str = Field(..., description="Carimbo de data/hora do registro no sistema")


class AtivoViewSchema(BaseModel):
    """Estrutura consolidada de visualização resumida de um ativo na carteira."""
    id: int = Field(..., description="Identificador único")
    codigo: str = Field(..., description="Código do ativo")
    nome: str = Field(..., description="Nome do ativo")
    categoria: str = Field(..., description="Categoria do investimento")
    meta_alocacao: float = Field(..., description="Meta percentual de alocação")
    observacoes: Optional[str] = Field(None, description="Observações")
    data_cadastro: str = Field(..., description="Data de criação no sistema")
    quantidade_custodia: float = Field(..., description="Quantidade líquida em carteira")
    total_investido: float = Field(..., description="Total financeiro investido em compras")
    preco_medio: float = Field(..., description="Preço médio unitário de compra")
    total_proventos: float = Field(..., description="Total recebido em proventos/dividendos")
    total_transacoes: int = Field(..., description="Número de transações registradas")


class AtivoDetalheViewSchema(AtivoViewSchema):
    """Estrutura detalhada contendo o ativo e todo o seu histórico de transações."""
    transacoes: List[TransacaoViewSchema] = Field(default=[], description="Lista cronológica de transações vinculadas")


class ListaAtivosViewSchema(BaseModel):
    """Resposta com lista de ativos e totais calculados."""
    total_itens: int = Field(..., description="Total de ativos cadastrados")
    total_investido_geral: float = Field(..., description="Montante global investido em todos os ativos")
    total_proventos_geral: float = Field(..., description="Montante global recebido em proventos")
    ativos: List[AtivoViewSchema] = Field(..., description="Lista de ativos cadastrados")


class ListaTransacoesViewSchema(BaseModel):
    """Resposta com lista de transações registradas."""
    total_itens: int = Field(..., description="Total de transações encontradas")
    transacoes: List[TransacaoViewSchema] = Field(..., description="Lista de transações")


class CategoriaDistribuicaoSchema(BaseModel):
    """Informações de alocação por categoria de investimento."""
    categoria: str = Field(..., description="Nome da categoria")
    total_investido: float = Field(..., description="Total alocado nesta categoria")
    percentual: float = Field(..., description="Percentual em relação ao total da carteira")
    quantidade_ativos: int = Field(..., description="Quantidade de ativos nesta categoria")


class DashboardViewSchema(BaseModel):
    """Resumo executivo da carteira de investimentos para exibição em dashboard."""
    patrimonio_investido: float = Field(..., description="Valor total atualmente alocado na carteira")
    total_proventos: float = Field(..., description="Total acumulado recebido de proventos")
    quantidade_ativos: int = Field(..., description="Total de ativos na carteira")
    quantidade_transacoes: int = Field(..., description="Total de transações registradas")
    distribuicao_categorias: List[CategoriaDistribuicaoSchema] = Field(..., description="Detalhamento por categoria")


class MensagemSchema(BaseModel):
    """Resposta padrão de sucesso para operações de exclusão ou atualização."""
    mensagem: str = Field(..., description="Mensagem explicativa de sucesso", json_schema_extra={"example": "Ativo removido com sucesso!"})
    id: Optional[int] = Field(None, description="ID do recurso afetado", json_schema_extra={"example": 1})


class ErrorSchema(BaseModel):
    """Resposta padronizada para erros e exceções da API."""
    mensagem: str = Field(..., description="Mensagem clara sobre a falha ocorrida")
    detalhes: Optional[str] = Field(None, description="Detalhes técnicos adicionais")
