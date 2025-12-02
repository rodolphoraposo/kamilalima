from flask import Flask, jsonify, request
import mysql.connector
from mysql.connector import Error as MysqlError # CORREÇÃO: Importação específica para o tratamento de erros
import os 
from flask_cors import CORS 

# --- Imports para Segurança e Autenticação ---
from flask_bcrypt import Bcrypt
import jwt
from functools import wraps
import datetime

# --- CONFIGURAÇÃO DO BANCO DE DADOS (Lendo Variáveis de Ambiente) ---
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST'),      
    'user': os.getenv('MYSQL_USER'),           
    'password': os.getenv('MYSQL_PASSWORD'),  
    'database': os.getenv('MYSQL_DATABASE')
}

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}}) 

# --- Inicialização do Bcrypt e Configuração da Chave Secreta ---
bcrypt = Bcrypt(app) 
app.config['SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'chave_secreta_padrao_muito_longa_e_aleatoria') 


# Função para conectar ao banco de dados
def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except MysqlError as err: # CORRIGIDO: Usando MysqlError
        print(f"Erro ao conectar ao MySQL (Verifique as Variáveis de Ambiente): {err}") 
        return None

# --- DECORATOR PARA PROTEÇÃO DE ROTAS (Segurança JWT) ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'erro': 'Token de acesso mal formatado (Use Bearer)'}), 401

        if not token:
            return jsonify({'erro': 'Token de acesso é obrigatório'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user_id = data['user_id']
        
        except jwt.ExpiredSignatureError:
            return jsonify({'erro': 'Token de acesso expirado'}), 401

        except jwt.InvalidTokenError:
            return jsonify({'erro': 'Token de acesso inválido'}), 401

        return f(current_user_id, *args, **kwargs)

    return decorated


# =========================================================================
# === ROTAS DE ACESSO PÚBLICO (Frontend) ===
# =========================================================================

@app.route('/', methods=['GET'])
def index():
    return "API do Agendamento Kamila Lima está funcionando!"

# --- ROTA: LISTAR TODOS OS SERVIÇOS DISPONÍVEIS ---
@app.route('/api/servicos', methods=['GET'])
def listar_servicos():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"erro": "Falha na conexão com o banco de dados"}), 500

    cursor = conn.cursor(dictionary=True)
    
    try:
        query = "SELECT id, nome, descricao, preco, duracao_minutos FROM servicos ORDER BY nome"
        cursor.execute(query)
        servicos = cursor.fetchall()
        return jsonify(servicos), 200
        
    except MysqlError as err: # CORRIGIDO: Usando MysqlError
        print(f"Erro ao buscar serviços: {err}")
        return jsonify({"erro": "Erro ao buscar serviços no banco de dados"}), 500
        
    finally:
        cursor.close()
        conn.close()

# --- ROTA PARA BUSCAR HORÁRIOS JÁ AGENDADOS (Público) ---
@app.route('/api/horarios-indisponiveis', methods=['GET'])
def get_indisponiveis():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"erro": "Falha na conexão com o banco de dados"}), 500

    cursor = conn.cursor(dictionary=True)
    query = "SELECT data_agendamento, hora_inicio, hora_fim FROM agendamentos WHERE status = 'APROVADO'"
    
    try:
        cursor.execute(query)
        horarios = cursor.fetchall()
        
        horarios_formatados = []
        for h in horarios:
            horarios_formatados.append({
                'data': h['data_agendamento'].strftime('%Y-%m-%d'),
                'hora_inicio': str(h['hora_inicio']),
                'hora_fim': str(h['hora_fim']) 
            })
            
        return jsonify(horarios_formatados), 200
        
    except MysqlError as err: # CORRIGIDO: Usando MysqlError
        return jsonify({"erro": f"Erro na consulta SQL: {err}"}), 500
        
    finally:
        cursor.close()
        conn.close()


# --- ROTA PARA RECEBER E SALVAR UM NOVO AGENDAMENTO (CREATE) ---
@app.route('/api/agendamentos', methods=['POST'])
def criar_agendamento():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"erro": "Falha na conexão com o banco de dados"}), 500

    data = request.get_json()
    required_fields = ['cliente_nome', 'cliente_whatsapp', 'servico_nome', 'data_agendamento', 'hora_inicio', 'hora_fim']
    if not all(field in data for field in required_fields):
        return jsonify({"erro": "Dados incompletos. Faltam campos obrigatórios."}), 400

    cliente_nome = data['cliente_nome']
    cliente_whatsapp = data['cliente_whatsapp']
    servico_nome = data['servico_nome']
    data_agendamento = data['data_agendamento']
    hora_inicio = data['hora_inicio']
    hora_fim = data['hora_fim']

    cursor = conn.cursor()
    try:
        # 2. BUSCAR servico_id pelo servico_nome (Adaptação à 3FN)
        cursor.execute("SELECT id FROM servicos WHERE nome = %s", (servico_nome,))
        result = cursor.fetchone()
        
        if result is None:
            return jsonify({"erro": f"Serviço '{servico_nome}' não encontrado. Selecione um serviço válido."}), 400
            
        servico_id = result[0]
        
        # 3. Consulta SQL para Inserção (usando servico_id, Status PENDENTE)
        query = """
        INSERT INTO agendamentos 
        (cliente_nome, cliente_whatsapp, servico_id, data_agendamento, hora_inicio, hora_fim, status) 
        VALUES (%s, %s, %s, %s, %s, %s, 'PENDENTE')
        """
        values = (cliente_nome, cliente_whatsapp, servico_id, data_agendamento, hora_inicio, hora_fim)
        
        cursor.execute(query, values)
        conn.commit()
        
        return jsonify({
            "mensagem": "Agendamento solicitado com sucesso. Aguardando aprovação.",
            "id": cursor.lastrowid,
            "status": "PENDENTE"
        }), 201
        
    except MysqlError as err: # CORRIGIDO: Usando MysqlError
        conn.rollback()
        print(f"Erro ao salvar agendamento: {err}")
        return jsonify({"erro": f"Erro interno ao processar o agendamento: {err}"}), 500
        
    finally:
        cursor.close()
        conn.close()


# =========================================================================
# === ROTAS DE AUTENTICAÇÃO E SETUP ===
# =========================================================================

# --- ROTA DE LOGIN (Autenticação) ---
@app.route('/api/login', methods=['POST'])
def login():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"erro": "Falha na conexão com o banco de dados"}), 500

    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'erro': 'Email e senha são obrigatórios'}), 400

    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT id, senha_hash FROM usuarios WHERE email = %s"
        cursor.execute(query, (email,))
        user = cursor.fetchone()

        if user is None or not bcrypt.check_password_hash(user['senha_hash'], password):
            return jsonify({'erro': 'Credenciais inválidas'}), 401

        # Gerar o JWT
        token_payload = {
            'user_id': user['id'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24) 
        }
        token = jwt.encode(token_payload, app.config['SECRET_KEY'], algorithm="HS256")

        return jsonify({'mensagem': 'Login bem-sucedido', 'token': token}), 200
            
    except Exception as e:
        print(f"Erro no login: {e}")
        return jsonify({'erro': 'Erro interno do servidor no login'}), 500
        
    finally:
        cursor.close()
        conn.close()

# --- ROTA DE CRIAÇÃO DO PRIMEIRO USUÁRIO (SETUP) ---
@app.route('/api/setup/admin', methods=['POST'])
def create_admin_user():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"erro": "Falha na conexão com o banco de dados"}), 500

    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    nome = data.get('nome', 'Administrador') 

    if not email or not password:
        return jsonify({'erro': 'Email e senha são obrigatórios'}), 400

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM usuarios LIMIT 1")
        if cursor.fetchone():
            return jsonify({'erro': 'Usuário administrador já existe. Setup não permitido.'}), 403

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        query = "INSERT INTO usuarios (nome, email, senha_hash) VALUES (%s, %s, %s)"
        cursor.execute(query, (nome, email, hashed_password))
        conn.commit()

        return jsonify({'mensagem': 'Usuário administrador criado com sucesso. Utilize a rota /api/login.'}), 201

    except MysqlError as err: # CORRIGIDO: Usando MysqlError
        conn.rollback()
        print(f"Erro ao criar usuário: {err}")
        return jsonify({'erro': f'Erro interno ao salvar usuário: {err}'}), 500
        
    finally:
        cursor.close()
        conn.close()


# =========================================================================
# === ROTAS DE GERENCIAMENTO (PROTEGIDAS PELO @token_required) ===
# =========================================================================

# --- ROTA: LISTAR TODOS OS AGENDAMENTOS (READ ALL) ---
@app.route('/api/agendamentos', methods=['GET'])
@token_required 
def listar_agendamentos(current_user_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"erro": "Falha na conexão com o banco de dados"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        query = """
        SELECT a.id, a.cliente_nome, a.cliente_whatsapp, s.nome AS servico_nome, 
               a.data_agendamento, a.hora_inicio, a.hora_fim, a.status, a.data_registro
        FROM agendamentos a JOIN servicos s ON a.servico_id = s.id
        ORDER BY a.data_agendamento DESC, a.hora_inicio DESC
        """
        cursor.execute(query)
        agendamentos = cursor.fetchall()
        
        agendamentos_formatados = []
        for ag in agendamentos:
            ag_formatado = ag.copy()
            ag_formatado['data_agendamento'] = ag['data_agendamento'].strftime('%Y-%m-%d')
            ag_formatado['hora_inicio'] = str(ag['hora_inicio'])
            ag_formatado['hora_fim'] = str(ag['hora_fim'])
            ag_formatado['data_registro'] = ag['data_registro'].strftime('%Y-%m-%d %H:%M:%S')
            agendamentos_formatados.append(ag_formatado)
        
        return jsonify(agendamentos_formatados), 200
        
    except MysqlError as err: # CORRIGIDO: Usando MysqlError
        print(f"Erro ao buscar agendamentos: {err}")
        return jsonify({"erro": "Erro ao buscar agendamentos no banco de dados"}), 500
        
    finally:
        cursor.close()
        conn.close()


# --- ROTA: BUSCAR UM AGENDAMENTO ESPECÍFICO (READ ONE) ---
@app.route('/api/agendamentos/<int:agendamento_id>', methods=['GET'])
@token_required 
def buscar_agendamento(current_user_id, agendamento_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"erro": "Falha na conexão com o banco de dados"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        query = """
        SELECT a.id, a.cliente_nome, a.cliente_whatsapp, s.nome AS servico_nome, a.servico_id,
               a.data_agendamento, a.hora_inicio, a.hora_fim, a.status, a.data_registro
        FROM agendamentos a JOIN servicos s ON a.servico_id = s.id
        WHERE a.id = %s
        """
        cursor.execute(query, (agendamento_id,))
        agendamento = cursor.fetchone()

        if agendamento:
            agendamento['data_agendamento'] = agendamento['data_agendamento'].strftime('%Y-%m-%d')
            agendamento['hora_inicio'] = str(agendamento['hora_inicio'])
            agendamento['hora_fim'] = str(agendamento['hora_fim'])
            agendamento['data_registro'] = agendamento['data_registro'].strftime('%Y-%m-%d %H:%M:%S')
            return jsonify(agendamento), 200
        else:
            return jsonify({"erro": "Agendamento não encontrado"}), 404
            
    except MysqlError as err: # CORRIGIDO: Usando MysqlError
        print(f"Erro ao buscar agendamento: {err}")
        return jsonify({"erro": "Erro ao buscar agendamento no banco de dados"}), 500
    finally:
        cursor.close()
        conn.close()


# --- ROTA: ATUALIZAR UM AGENDAMENTO (UPDATE / PATCH) ---
@app.route('/api/agendamentos/<int:agendamento_id>', methods=['PATCH'])
@token_required 
def atualizar_agendamento(current_user_id, agendamento_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"erro": "Falha na conexão com o banco de dados"}), 500

    data = request.get_json()
    updates = []
    values = []
    allowed_fields = ['cliente_nome', 'cliente_whatsapp', 'servico_nome', 'data_agendamento', 'hora_inicio', 'hora_fim', 'status']

    try:
        cursor = conn.cursor()
        
        if 'servico_nome' in data:
            servico_nome = data['servico_nome']
            cursor.execute("SELECT id FROM servicos WHERE nome = %s", (servico_nome,))
            result = cursor.fetchone()
            
            if result is None:
                return jsonify({"erro": f"Serviço '{servico_nome}' não encontrado para atualização."}), 400
                
            updates.append("servico_id = %s")
            values.append(result[0])
            del data['servico_nome'] 

        for field in allowed_fields:
            if field in data and field != 'servico_nome':
                updates.append(f"{field} = %s")
                values.append(data[field])

        if not updates:
            return jsonify({"erro": "Nenhum campo válido para atualização fornecido."}), 400

        query = f"UPDATE agendamentos SET {', '.join(updates)} WHERE id = %s"
        values.append(agendamento_id)
        
        cursor.execute(query, tuple(values))
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({"erro": "Agendamento não encontrado ou dados não alterados"}), 404
        
        return jsonify({"mensagem": "Agendamento atualizado com sucesso"}), 200
        
    except MysqlError as err: # CORRIGIDO: Usando MysqlError
        conn.rollback()
        print(f"Erro ao atualizar agendamento: {err}")
        return jsonify({"erro": f"Erro interno ao atualizar agendamento: {err}"}), 500
        
    finally:
        cursor.close()
        conn.close()


# --- ROTA: DELETAR UM AGENDAMENTO (DELETE) ---
@app.route('/api/agendamentos/<int:agendamento_id>', methods=['DELETE'])
@token_required 
def deletar_agendamento(current_user_id, agendamento_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"erro": "Falha na conexão com o banco de dados"}), 500

    cursor = conn.cursor()
    try:
        query = "DELETE FROM agendamentos WHERE id = %s"
        cursor.execute(query, (agendamento_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({"erro": "Agendamento não encontrado para exclusão"}), 404

        return '', 204 
        
    except MysqlError as err: # CORRIGIDO: Usando MysqlError
        conn.rollback()
        print(f"Erro ao deletar agendamento: {err}")
        return jsonify({"erro": f"Erro interno ao deletar agendamento: {err}"}), 500
        
    finally:
        cursor.close()
        conn.close()


# --- ROTA SECRETA PARA KAMILA LIMA APROVAR O AGENDAMENTO (Legado - Protegida) ---
@app.route('/api/agendamentos/<int:booking_id>/aprovar', methods=['GET'])
@token_required 
def aprovar_agendamento(current_user_id, booking_id):
    conn = get_db_connection()
    if conn is None:
        return "Erro: Falha na conexão com o banco de dados", 500

    cursor = conn.cursor()
    query = "UPDATE agendamentos SET status = 'APROVADO' WHERE id = %s"
    
    try:
        cursor.execute(query, (booking_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            return "Erro 404: Agendamento não encontrado para aprovação.", 404
            
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>Agendamento Aprovado</title>
        <style>
        body {{ background-color: #F7ECE0; font-family: sans-serif; text-align: center; padding-top: 50px; }}
        .container {{ max-width: 400px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1); }}
        h1 {{ color: #28A745; }}
        </style>
        </head>
        <body>
        <div class="container">
            <h1>✅ Agendamento ID {booking_id} Aprovado com Sucesso!</h1>
            <p>Este horário agora está **BLOQUEADO** no site para novos clientes.</p>
        </div>
        </body>
        </html>
        """, 200
        
    except MysqlError as err: # CORRIGIDO: Usando MysqlError
        conn.rollback()
        return f"Erro ao aprovar o agendamento: {err}", 500
        
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    app.run(debug=True, port=5000)