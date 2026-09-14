from datetime import datetime, date
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Date, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

Base = declarative_base()

# Localização do banco de dados SQLite
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Ativo(Base):
    """
    Modelo de dados para Ativos Financeiros na Carteira de Investimentos.
    Representa a entidade principal do sistema.
    """
    __tablename__ = "ativos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(20), unique=True, nullable=False, index=True)
    nome = Column(String(120), nullable=False)
    categoria = Column(String(50), nullable=False)  # Ex: Ações, FIIs, Criptomoedas, Renda Fixa, ETFs
    meta_alocacao = Column(Float, default=0.0)      # Percentual objetivo da carteira (ex: 15.0)
    observacoes = Column(String(255), nullable=True)
    data_cadastro = Column(DateTime, default=datetime.now)

    # Relacionamento 1:N com integridade referencial e deleção em cascata
    transacoes = relationship(
        "Transacao",
        back_populates="ativo",
        cascade="all, delete-orphan",
        order_by="desc(Transacao.data_transacao)"
    )

    @property
    def quantidade_custodia(self) -> float:
        """Calcula a quantidade líquida atual em custódia considerando compras e vendas."""
        compras = sum(t.quantidade for t in self.transacoes if t.tipo == "COMPRA")
        vendas = sum(t.quantidade for t in self.transacoes if t.tipo == "VENDA")
        return max(0.0, compras - vendas)

    @property
    def total_investido(self) -> float:
        """Calcula o montante total financeiro alocado em compras."""
        return sum(t.quantidade * t.preco_unitario for t in self.transacoes if t.tipo == "COMPRA")

    @property
    def preco_medio(self) -> float:
        """Calcula o preço médio unitário ponderado de compra do ativo."""
        total_qtd_compras = sum(t.quantidade for t in self.transacoes if t.tipo == "COMPRA")
        if total_qtd_compras > 0:
            return round(self.total_investido / total_qtd_compras, 2)
        return 0.0

    @property
    def total_proventos(self) -> float:
        """Calcula o valor acumulado recebido em dividendos / rendimentos."""
        return sum(t.quantidade * t.preco_unitario for t in self.transacoes if t.tipo == "DIVIDENDO")


class Transacao(Base):
    """
    Modelo de dados para Movimentações e Transações vinculadas aos Ativos.
    Implementa o relacionamento 1:N com tratamento de datas financeiras.
    """
    __tablename__ = "transacoes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ativo_id = Column(Integer, ForeignKey("ativos.id", ondelete="CASCADE"), nullable=False)
    tipo = Column(String(20), nullable=False)  # COMPRA, VENDA ou DIVIDENDO
    quantidade = Column(Float, nullable=False)
    preco_unitario = Column(Float, nullable=False)
    data_transacao = Column(Date, nullable=False, default=date.today)
    descricao = Column(String(255), nullable=True)
    data_registro = Column(DateTime, default=datetime.now)

    # Relacionamento inverso
    ativo = relationship("Ativo", back_populates="transacoes")

    @property
    def valor_total(self) -> float:
        """Valor financeiro total da transação."""
        return round(self.quantidade * self.preco_unitario, 2)


def get_db():
    """Gera uma sessão do banco de dados para controle de contexto transacional."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_initial_data():
    """Popula dados iniciais caso o banco de dados esteja vazio para facilitar a demonstração."""
    db = SessionLocal()
    try:
        if db.query(Ativo).count() == 0:
            ativo1 = Ativo(
                codigo="PETR4",
                nome="Petrobras PN",
                categoria="Ações",
                meta_alocacao=20.0,
                observacoes="Setor de Petróleo, Gás e Biocombustíveis.",
                data_cadastro=datetime(2025, 1, 15, 10, 0, 0)
            )
            ativo2 = Ativo(
                codigo="HGLG11",
                nome="CSHG Logística FII",
                categoria="FIIs",
                meta_alocacao=25.0,
                observacoes="Fundo Imobiliário com galpões logísticos classe A.",
                data_cadastro=datetime(2025, 2, 1, 14, 30, 0)
            )
            ativo3 = Ativo(
                codigo="BTC",
                nome="Bitcoin",
                categoria="Criptomoedas",
                meta_alocacao=10.0,
                observacoes="Reserva de valor descentralizada.",
                data_cadastro=datetime(2025, 2, 20, 9, 15, 0)
            )
            db.add_all([ativo1, ativo2, ativo3])
            db.commit()

            # Transações iniciais
            t1 = Transacao(
                ativo_id=ativo1.id,
                tipo="COMPRA",
                quantidade=100.0,
                preco_unitario=36.50,
                data_transacao=date(2025, 1, 20),
                descricao="Primeira compra de ações da Petrobras"
            )
            t2 = Transacao(
                ativo_id=ativo1.id,
                tipo="DIVIDENDO",
                quantidade=100.0,
                preco_unitario=1.45,
                data_transacao=date(2025, 3, 10),
                descricao="Pagamento de dividendos e JCP"
            )
            t3 = Transacao(
                ativo_id=ativo2.id,
                tipo="COMPRA",
                quantidade=30.0,
                preco_unitario=162.80,
                data_transacao=date(2025, 2, 5),
                descricao="Aporte inicial em cotas do HGLG11"
            )
            t4 = Transacao(
                ativo_id=ativo3.id,
                tipo="COMPRA",
                quantidade=0.015,
                preco_unitario=385000.0,
                data_transacao=date(2025, 2, 22),
                descricao="Aporte fracionado de Bitcoin"
            )
            db.add_all([t1, t2, t3, t4])
            db.commit()
            print("Dados iniciais semeados com sucesso!")
    finally:
        db.close()


def init_db():
    """Inicializa as tabelas do banco de dados SQLite."""
    Base.metadata.create_all(bind=engine)
    seed_initial_data()
