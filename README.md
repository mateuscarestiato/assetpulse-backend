# 💼 AssetPulse API - Gestão Inteligente de Ativos & Investimentos

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Flask Version](https://img.shields.io/badge/flask-3.1%2B-green)
![OpenAPI](https://img.shields.io/badge/OpenAPI-3.0-orange)
![Database](https://img.shields.io/badge/SQLite-SQLAlchemy-lightgrey)
![License](https://img.shields.io/badge/license-MIT-purple)

Repositório oficial do **Back-end do MVP da Sprint de Desenvolvimento Full Stack Básico** (Pós-Graduação).

O **AssetPulse API** é um serviço RESTful moderno desenvolvido em Python e Flask voltado para o controle patrimonial, gestão de carteiras de investimentos multiactivos (Ações, FIIs, Criptomoedas, Renda Fixa) e registro cronológico de movimentações financeiras com tratamento de datas e relacionamento relacional entre entidades.

---

## 🏛️ Alinhamento com as Key Constraints de Roy Fielding

A arquitetura deste serviço foi concebida respeitando rigorosamente as diretrizes fundamentais da Web propostas por Roy Fielding:

1. **Separação de Responsabilidades (Client-Server)**: A API atua exclusivamente na camada de negócio e persistência de dados, comunicando-se com o front-end por meio de JSON, permitindo evolução independente de ambas as partes.
2. **Interface Uniforme**: Rotas semânticas utilizando métodos HTTP padronizados (`GET`, `POST`, `PUT`, `DELETE`), tipos de conteúdo uniformes (`application/json`) e códigos de status HTTP explícitos (`200 OK`, `201 Created`, `400 Bad Request`, `404 Not Found`, `409 Conflict`, `500 Server Error`).
3. **Ausência de Estado (Stateless)**: Cada requisição contém todas as informações necessárias para sua compreensão e processamento. Não há sessão armazenada no servidor entre chamadas.
4. **Sistema em Camadas**: O back-end é estruturado modularmente em Camada de Apresentação/Rotas (`app.py`), Camada de Validação/Contratos (`schemas.py`) e Camada de Domínio/Persistência (`models.py`).

---

## 🚀 Funcionalidades da API

- **Múltiplas Tabelas Relacionadas (1:N)**:
  - `Ativo`: Entidade principal contendo código/ticker (ex: `PETR4`, `HGLG11`), nome empresarial, classe/categoria, meta de alocação (%) e anotações.
  - `Transacao`: Movimentações vinculadas via chave estrangeira (`ativo_id`) com deleção em cascata (`CASCADE`), tipos de operação (`COMPRA`, `VENDA`, `DIVIDENDO`), volumes negociados, preço unitário e histórico cronológico com tratamento de datas.
- **Cálculos Consolidados em Tempo Real**:
  - Quantidade líquida em custódia (compras - vendas).
  - Preço médio unitário ponderado de compra.
  - Total de proventos/dividendos auferidos.
  - Distribuição percentual por classe de ativos para o dashboard gerencial.
- **Documentação OpenAPI 3.0 Integrada**: Swagger UI interativo nativo para testes e visualização de esquemas de entrada e saída.
- **CORS Aberto**: Configurado para viabilizar chamadas locais imediatas a partir do front-end aberto via protocolo `file://`.

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem**: Python 3.10+ (compatível com 3.13)
- **Framework Web**: [Flask](https://flask.palletsprojects.com/)
- **Documentação & Validação**: [Flask-OpenAPI3](https://luolingchun.github.io/flask-openapi3/) com [Pydantic v2](https://docs.pydantic.dev/)
- **ORM / Persistência**: [SQLAlchemy](https://www.sqlalchemy.org/) com banco embutido [SQLite](https://www.sqlite.org/)
- **Segurança & Comunicação Cross-Origin**: [Flask-CORS](https://flask-cors.readthedocs.io/)

---

## 📋 Pré-requisitos

- **Python 3.10** ou superior instalado em seu sistema operacional.
- Gerenciador de pacotes **pip** atualizado.

---

## ⚙️ Instruções de Instalação e Configuração

Siga os passos abaixo para configurar e executar a API localmente:

### 1. Clonar ou Acessar o Diretório do Projeto
```bash
git clone https://github.com/mateuscarestiato/assetpulse-backend.git
cd assetpulse-backend
```

### 2. Criar e Ativar um Ambiente Virtual (Recomendado)

**No Windows (PowerShell / Prompt de Comando):**
```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

**No Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar as Dependências
Com o ambiente virtual ativado, instale os pacotes listados no `requirements.txt`:
```bash
pip install -r requirements.txt
```

---

## 🚀 Execução da API

Para inicializar o servidor de desenvolvimento:

```bash
python app.py
```

A API será inicializada na porta `5000`:
- **URL Base:** `http://127.0.0.1:5000`
- **Documentação Interativa (Swagger UI):** `http://127.0.0.1:5000/openapi/swagger`
- **Esquema OpenAPI JSON:** `http://127.0.0.1:5000/openapi/openapi.json`

> 💡 **Nota:** Ao iniciar pela primeira vez, o banco de dados `database.db` será criado automaticamente com uma semente de dados exemplares (`PETR4`, `HGLG11`, `BTC`) para facilitar a demonstração imediata.

---

## 📖 Mapeamento das Rotas da API

Abaixo está o resumo dos endpoints implementados:

| Método | Rota | Descrição | Status Sucesso |
| :--- | :--- | :--- | :---: |
| `GET` | `/` | Redirecionamento automático para a documentação Swagger | `302` |
| `POST` | `/api/ativo` | Cadastra um novo ativo na carteira de investimentos | `201` |
| `GET` | `/api/ativos` | Lista todos os ativos com totais e métricas calculadas | `200` |
| `GET` | `/api/ativo` | Busca ativo específico por ID ou Código com histórico de transações | `200` |
| `PUT` | `/api/ativo` | Atualiza informações cadastrais de um ativo existente | `200` |
| `DELETE` | `/api/ativo` | Exclui um ativo e todas as suas transações em cascata | `200` |
| `POST` | `/api/transacao` | Registra nova transação (COMPRA, VENDA ou DIVIDENDO) vinculada ao ativo | `201` |
| `GET` | `/api/transacoes` | Lista transações registradas com filtros opcionais | `200` |
| `GET` | `/api/dashboard` | Retorna métricas executivas consolidadas da carteira | `200` |

---

## 🧪 Testes Automatizados

O projeto conta com testes de integração cobrindo todas as rotas e regras de negócio:

```bash
python test_api.py
```

---

## 📁 Estrutura do Diretório

```
mvp-invest-api/
│
├── app.py              # Ponto de entrada do servidor Flask e mapeamento das rotas
├── models.py           # Modelos ORM SQLAlchemy, conexão SQLite e seed de dados
├── schemas.py          # Esquemas Pydantic v2 de entrada e saída com OpenAPI
├── test_api.py         # Testes de integração automatizados das rotas
├── requirements.txt    # Lista de dependências do Python
├── .gitignore          # Arquivos e diretórios ignorados pelo Git
└── README.md           # Documentação completa do projeto
```
