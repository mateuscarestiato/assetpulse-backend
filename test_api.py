import unittest
from app import app


class TestAssetPulseAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_01_listar_ativos(self):
        res = self.client.get("/api/ativos")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("ativos", data)
        self.assertGreaterEqual(data["total_itens"], 1)

    def test_02_buscar_ativo(self):
        res = self.client.get("/api/ativo?codigo=PETR4")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["codigo"], "PETR4")
        self.assertIn("transacoes", data)

    def test_03_crud_completo_ativo_e_transacao(self):
        # 1. Cadastro de ativo
        payload = {
            "codigo": "BBAS3",
            "nome": "Banco do Brasil ON",
            "categoria": "Ações",
            "meta_alocacao": 15.0,
            "observacoes": "Instituição financeira secular com forte payout."
        }
        res = self.client.post("/api/ativo", json=payload)
        self.assertEqual(res.status_code, 201)
        ativo = res.get_json()
        ativo_id = ativo["id"]
        self.assertEqual(ativo["codigo"], "BBAS3")

        # 2. Cadastro de transação vinculada (Relacionamento 1:N com tratamento de datas)
        trans_payload = {
            "ativo_id": ativo_id,
            "tipo": "COMPRA",
            "quantidade": 100.0,
            "preco_unitario": 27.50,
            "data_transacao": "2025-03-01",
            "descricao": "Compra inicial de ações ordinárias"
        }
        res_t = self.client.post("/api/transacao", json=trans_payload)
        self.assertEqual(res_t.status_code, 201)
        transacao = res_t.get_json()
        self.assertEqual(transacao["valor_total"], 2750.0)

        # 3. Atualizar ativo (PUT)
        update_payload = {
            "id": ativo_id,
            "nome": "Banco do Brasil S.A.",
            "meta_alocacao": 18.0
        }
        res_u = self.client.put("/api/ativo", json=update_payload)
        self.assertEqual(res_u.status_code, 200)
        self.assertEqual(res_u.get_json()["nome"], "Banco do Brasil S.A.")

        # 4. Listar transações com filtro
        res_lt = self.client.get(f"/api/transacoes?ativo_id={ativo_id}")
        self.assertEqual(res_lt.status_code, 200)
        self.assertEqual(res_lt.get_json()["total_itens"], 1)

        # 5. Dashboard
        res_d = self.client.get("/api/dashboard")
        self.assertEqual(res_d.status_code, 200)
        dash = res_d.get_json()
        self.assertGreater(dash["patrimonio_investido"], 0)

        # 6. Excluir ativo (DELETE)
        res_del = self.client.delete(f"/api/ativo?id={ativo_id}")
        self.assertEqual(res_del.status_code, 200)
        self.assertIn("removidos com sucesso", res_del.get_json()["mensagem"])

        # Verificar se realmente foi excluído
        res_check = self.client.get(f"/api/ativo?id={ativo_id}")
        self.assertEqual(res_check.status_code, 404)

    def test_04_swagger_docs(self):
        res = self.client.get("/openapi/swagger")
        self.assertIn(res.status_code, [200, 308, 302])

    def test_05_validacao_duplicidade_ticker(self):
        # Tentar cadastrar ticker já existente deve retornar 409 Conflict
        payload = {
            "codigo": "PETR4",
            "nome": "Petrobras PN Repetida",
            "categoria": "Ações",
            "meta_alocacao": 10.0
        }
        res = self.client.post("/api/ativo", json=payload)
        self.assertEqual(res.status_code, 409)
        self.assertIn("Já existe um ativo cadastrado", res.get_json()["mensagem"])

    def test_06_validacao_transacao_tipo_invalido(self):
        # Transação com tipo não reconhecido deve retornar 400 Bad Request
        payload = {
            "ativo_id": 1,
            "tipo": "TRANSFERENCIA_INVALIDA",
            "quantidade": 10.0,
            "preco_unitario": 20.0
        }
        res = self.client.post("/api/transacao", json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("Tipo de transação inválido", res.get_json()["mensagem"])

    def test_07_busca_ativo_inexistente(self):
        # Busca por ID inexistente deve retornar 404 Not Found
        res = self.client.get("/api/ativo?id=999999")
        self.assertEqual(res.status_code, 404)
        self.assertIn("Ativo não encontrado", res.get_json()["mensagem"])

    def test_08_integridade_delecao_em_cascata(self):
        # Cria ativo temporário
        res_a = self.client.post("/api/ativo", json={
            "codigo": "TEMP3",
            "nome": "Ativo Temporário Teste",
            "categoria": "Ações",
            "meta_alocacao": 5.0
        })
        self.assertEqual(res_a.status_code, 201)
        temp_id = res_a.get_json()["id"]

        # Cria transação vinculada a ele
        res_t = self.client.post("/api/transacao", json={
            "ativo_id": temp_id,
            "tipo": "COMPRA",
            "quantidade": 10.0,
            "preco_unitario": 50.0
        })
        self.assertEqual(res_t.status_code, 201)

        # Deleta o ativo
        res_del = self.client.delete(f"/api/ativo?id={temp_id}")
        self.assertEqual(res_del.status_code, 200)

        # Verifica se as transações vinculadas foram expurgadas em cascata
        res_check_t = self.client.get(f"/api/transacoes?ativo_id={temp_id}")
        self.assertEqual(res_check_t.status_code, 200)
        self.assertEqual(res_check_t.get_json()["total_itens"], 0)


if __name__ == "__main__":
    unittest.main()

