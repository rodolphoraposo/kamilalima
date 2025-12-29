# backend/test_app.py

import pytest
import json
from app import app, get_db_connection # Importa a aplicação Flask e a função de conexão
import os

# Configura o Pytest para usar o cliente de teste do Flask
@pytest.fixture
def client():
    # Isso configura o app para testes
    app.config['TESTING'] = True
    # O app.test_client() simula requisições HTTP
    with app.test_client() as client:
        yield client

# Fixture para garantir que um serviço de teste esteja no banco de dados
# O agendamento depende da existência de um serviço
@pytest.fixture(scope='session', autouse=True)
def setup_db():
    # Se a conexão falhar aqui, o teste não deve prosseguir
    conn = get_db_connection()
    if conn is None:
        pytest.fail("Falha ao conectar ao banco de dados para o setup dos testes. Verifique seu .env.")
    
    cursor = conn.cursor()
    try:
        # Tenta inserir um serviço de teste se ele não existir
        cursor.execute("SELECT id FROM servicos WHERE nome = 'Corte de Teste'")
        if cursor.fetchone() is None:
            cursor.execute("""
                INSERT INTO servicos (nome, descricao, preco, duracao_minutos) 
                VALUES ('Corte de Teste', 'Serviço temporário para validação da API', 30.00, 30)
            """)
            conn.commit()
    except Exception as e:
        # Apenas avisa se houver erro na inserção (pode ser que a tabela não exista)
        print(f"Aviso: Não foi possível realizar o setup do serviço de teste: {e}")
        pass 
    finally:
        cursor.close()
        conn.close()

# =================================================================
# === TESTES DA ROTA PÚBLICA (Frontend) ===
# =================================================================

# Teste 1: Checa se a rota inicial (/) está funcionando
def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200
    # Checagem de bytes é necessária devido ao encoding da resposta HTML/string
    assert b"API do Agendamento Kamila Lima est\xc3\xa1 funcionando!" in response.data 

# Teste 2: Checa se a rota de listagem de serviços (GET /api/servicos) está funcionando
def test_list_services_route(client):
    response = client.get('/api/servicos')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)

# Teste 3: Checa a criação de um novo agendamento (POST /api/agendamentos)
def test_create_agendamento_success(client):
    # DADOS VÁLIDOS (Depende do 'Corte de Teste' estar no banco)
    booking_data = {
        'cliente_nome': 'Cliente Teste Pytest',
        'cliente_whatsapp': '82998887766',
        'servico_nome': 'Corte de Teste', 
        'data_agendamento': '2050-12-30', 
        'hora_inicio': '10:00:00',
        'hora_fim': '10:30:00'
    }
    
    response = client.post('/api/agendamentos', 
                           data=json.dumps(booking_data),
                           content_type='application/json')
    
    # Limpeza: Após o teste, tenta deletar o agendamento criado
    if response.status_code == 201:
        try:
            data = json.loads(response.data)
            booking_id = data.get('id')
            if booking_id:
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM agendamentos WHERE id = %s", (booking_id,))
                    conn.commit()
                    cursor.close()
                    conn.close()
        except Exception as e:
            print(f"Aviso: Falha na limpeza do agendamento de teste. ID: {booking_id} - Erro: {e}")

    # Verifica a resposta da API
    assert response.status_code == 201
    assert 'Agendamento solicitado com sucesso' in response.get_data(as_text=True)

# Teste 4: Checa erro na criação de agendamento (Dados incompletos)
def test_create_agendamento_incomplete_data(client):
    booking_data = {
        'cliente_nome': 'Cliente Incompleto',
        # Faltando 'servico_nome' e outros campos obrigatórios
    }
    response = client.post('/api/agendamentos', 
                           data=json.dumps(booking_data),
                           content_type='application/json')
    
    assert response.status_code == 400
    assert 'Dados incompletos' in response.get_data(as_text=True)

# Testes de Autenticação (Apenas para garantir que estão protegidas - 401 Unauthorized)

# Teste 5: Checa se a listagem de agendamentos está protegida
def test_list_agendamentos_protected(client):
    response = client.get('/api/agendamentos')
    # Deve retornar 401 porque o token não foi fornecido
    assert response.status_code == 401
    
    # CORREÇÃO: Utiliza get_json() para decodificar a resposta JSON, 
    # resolvendo o problema de codificação de caracteres especiais (é, ó).
    data = response.get_json()
    assert data['erro'] == 'Token de acesso é obrigatório'