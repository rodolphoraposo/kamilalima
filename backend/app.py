from flask import Flask, jsonify, request
import mysql.connector
import os 
from flask_cors import CORS 
from flask_bcrypt import Bcrypt 
import jwt 
from functools import wraps 
import datetime
from dotenv import load_dotenv # NOVO: Para carregar o .env localmente

# Carrega as variáveis de ambiente do arquivo .env (apenas para desenvolvimento local)
load_dotenv() 

# --- CONFIGURAÇÃO DO BANCO DE DADOS (Lendo Variáveis de Ambiente) ---
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST'),      
    'user': os.getenv('MYSQL_USER'),           
    'password': os.getenv('MYSQL_PASSWORD'),  
    'database': os.getenv('MYSQL_DATABASE')
}

app = Flask(__name__)
# Permitir CORS para requisições do frontend
CORS(app, resources={r"/api/*": {"origins": "*"}}) 

# Inicialização do Bcrypt
bcrypt = Bcrypt(app) 

# Configuração da Chave Secreta do JWT
app.config['SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'chave_padrao_para_local')

# Função para conectar ao banco de dados
def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao MySQL: {err}") 
        # Retorna a mensagem de erro detalhada no ambiente de desenvolvimento
        return None

# ----------------------------------------------------
# --- DECORADOR DE AUTENTICAÇÃO JWT (Segurança) ---
# ----------------------------------------------------
def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            try:
                token = request.headers['Authorization'].split()[1] 
            except IndexError:
                return jsonify({'erro': 'Token de autenticação inválido'}), 401

        if not token:
            return jsonify({'erro': 'Token de autenticação ausente'}), 401

        try:
            # Decodifica o token
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            request.current_user = data 
        except jwt.ExpiredSignatureError:
            return jsonify({'erro': 'Token expirado. Faça login novamente.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'erro': 'Token inválido. Acesso negado.'}), 401

        return f(*args, **kwargs)

    return decorated
# ----------------------------------------------------

# --- ROTA DE TESTE (SAÚDE) ---
@app.route('/', methods=['GET'])
def index():
    return "API Kamila Lima Agendamentos está rodando!"

# ----------------------------------------------------
# --- ROTA: AUTENTICAÇÃO (POST /api/login) ---
# ----------------------------------------------------
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"erro": "Usuário e senha são obrigatórios"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"erro": "Falha na conexão com o banco de dados"}), 500

    cursor = conn.cursor(dictionary=True) 
    
    try:
        # 1. Busca o usuário pelo username (que armazena o email)
        query = "SELECT id, username, password_hash, role FROM usuarios WHERE username = %s"
        cursor.execute(query, (username,))
        user = cursor.fetchone()

        if user:
            # 2. Verifica a senha usando Bcrypt
            if bcrypt.check_password_hash(user['password_hash'], password):
                
                # 3. Senha correta: Gera o Token JWT
                token_payload = {
                    'user_id': user['id'],
                    'username': user['username'],
                    'role': user['role'],
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24) 
                }
                
                token = jwt.encode(token_payload, app.config['SECRET_KEY'], algorithm='HS256')
                
                # 4. Retorna o token
                return jsonify({
                    "mensagem": "Login bem-sucedido",
                    "token": token
                }), 200
            else:
                return jsonify({"erro": "Usuário ou senha incorretos"}), 401
        else:
            return jsonify({"erro": "Usuário ou senha incorretos"}), 401

    except mysql.connector.Error as err:
        print(f"Erro no processo de login: {err}")
        return jsonify({"erro": "Erro interno do servidor"}), 500
    finally:
        cursor.close()
        conn.close()

# ----------------------------------------------------
# --- ROTA: SERVIÇOS (GET /api/servicos) - Novo ---
# ----------------------------------------------------
@app.route('/api/servicos', methods=['GET'])
def get_servicos():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"erro": "Falha na conexão com o banco de dados"}), 500

    cursor = conn.cursor(dictionary=True)
    query = "SELECT id, nome, descricao, preco, duracao_minutos FROM servicos ORDER BY nome"
    
    try:
        cursor.execute(query)
        servicos = cursor.fetchall()
        
        # Converte preco para float para JSON
        for s in servicos:
             s['preco'] = float(s['preco'])

        return jsonify(servicos), 200
    except mysql.connector.Error as err:
        print(f"Erro ao buscar serviços: {err}")
        return jsonify({"erro": "Erro ao buscar serviços no banco de dados"}), 500
    finally:
        cursor.close()
        conn.close()

# ----------------------------------------------------
# --- ROTA: AGENDAMENTOS OCUPADOS (GET /api/agendamentos/ocupados) - NOVO FILTRO ---
# ----------------------------------------------------
@app.route('/api/agendamentos/ocupados', methods=['GET'])
def get_horarios_ocupados():
    data_consulta = request.args.get('data') # Ex: '2025-11-20'

    if not data_consulta:
        return jsonify({'erro': 'A data é obrigatória para consultar horários ocupados'}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"erro": "Falha na conexão com o banco de dados"}), 500

    cursor = conn.cursor(dictionary=True)
    
    # Busca apenas agendamentos APROVADOS e PENDENTES na data especificada
    query = """
    SELECT hora_inicio, hora_fim, s.duracao_minutos
    FROM agendamentos a
    JOIN servicos s ON a.servico_id = s.id
    WHERE a.data_agendamento = %s AND a.status IN ('APROVADO', 'PENDENTE')
    """
    
    try:
        cursor.execute(query, (data_consulta,))
        ocupados = cursor.fetchall()
        
        return jsonify(ocupados), 200
    except mysql.connector.Error as err:
        print(f"Erro ao buscar horários ocupados: {err}")
        return jsonify({"erro": "Erro ao buscar horários ocupados no banco de dados"}), 500
    finally:
        cursor.close()
        conn.close()

# ----------------------------------------------------
# --- ROTA: AGENDAR UM NOVO SERVIÇO (POST /api/agendar) ---
# ----------------------------------------------------
@app.route('/api/agendar', methods=['POST'])
def agendar():
    data = request.get_json()

    # ATUALIZADO: Agora espera servico_id (INT)
    required_fields = ['cliente_nome', 'cliente_whatsapp', 'servico_id', 'data_agendamento', 'hora_inicio', 'hora_fim']
    if not all(field in data for field in required_fields):
        return jsonify({"erro": "Todos os campos de agendamento são obrigatórios."}), 400

    cliente_nome = data['cliente_nome']
    cliente_whatsapp = data['cliente_whatsapp']
    servico_id = data['servico_id'] # NOVO
    data_agendamento = data['data_agendamento']
    hora_inicio = data['hora_inicio']
    hora_fim = data['hora_fim'] 
    
    # 1. Checar se o servico_id é válido (Opcional, mas recomendado)
    if not isinstance(servico_id, int):
        return jsonify({"erro": "ID do serviço inválido."}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"erro": "Falha na conexão com o banco de dados"}), 500
        
    # 2. Consulta de Checagem de Conflito (RECOMENDADO MANTIDO)
    conflito_query = """
    SELECT COUNT(*) FROM agendamentos 
    WHERE data_agendamento = %s 
    AND (
        (hora_inicio < %s AND hora_fim > %s) OR
        (hora_inicio >= %s AND hora_inicio < %s) OR
        (hora_fim > %s AND hora_fim <= %s)
    )
    AND status IN ('APROVADO', 'PENDENTE')
    """
    conflito_values = (
        data_agendamento, hora_fim, hora_inicio, 
        hora_inicio, hora_fim, 
        hora_inicio, hora_fim
    )
    
    cursor = conn.cursor()
    try:
        cursor.execute(conflito_query, conflito_values)
        conflito_count = cursor.fetchone()[0]

        if conflito_count > 0:
             return jsonify({"erro": "O horário selecionado não está mais disponível ou conflita com outro agendamento."}), 409

        # 3. Consulta SQL para Inserção (Status PENDENTE)
        query = """
        INSERT INTO agendamentos 
        (cliente_nome, cliente_whatsapp, servico_id, data_agendamento, hora_inicio, hora_fim, status) 
        VALUES (%s, %s, %s, %s, %s, %s, 'PENDENTE')
        """
        # ATUALIZADO: valores agora incluem servico_id
        values = (cliente_nome, cliente_whatsapp, servico_id, data_agendamento, hora_inicio, hora_fim)
        
        cursor.execute(query, values)
        conn.commit()
        
        # 4. Retorno de sucesso
        return jsonify({
            "mensagem": "Agendamento solicitado com sucesso. Aguardando aprovação.",
            "id": cursor.lastrowid,
            "status": "PENDENTE"
        }), 201
        
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Erro ao agendar: {err}")
        return jsonify({"erro": "Erro interno ao processar agendamento"}), 500
    finally:
        cursor.close()
        conn.close()


# ----------------------------------------------------
# --- ROTA: PAINEL ADMINISTRATIVO (PROTEGIDA) ---
# ----------------------------------------------------
@app.route('/api/admin/agendamentos', methods=['GET'])
@auth_required
def admin_agendamentos():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"erro": "Falha na conexão com o banco de dados"}), 500

    cursor = conn.cursor(dictionary=True)
    
    # ATUALIZADO: JOIN com a tabela 'servicos' para buscar o nome do serviço
    query = """
    SELECT 
        a.id, 
        a.cliente_nome, 
        a.cliente_whatsapp, 
        s.nome AS servico_nome, 
        a.data_agendamento, 
        a.hora_inicio, 
        a.hora_fim, 
        a.status,
        a.data_registro 
    FROM agendamentos a
    JOIN servicos s ON a.servico_id = s.id
    ORDER BY a.data_agendamento DESC, a.hora_inicio
    """ 
    
    try:
        cursor.execute(query)
        agendamentos = cursor.fetchall()
        
        # Formata datas/horas para JSON
        for ag in agendamentos:
            ag['data_agendamento'] = ag['data_agendamento'].isoformat() if ag['data_agendamento'] else None
            ag['hora_inicio'] = str(ag['hora_inicio']) if ag['hora_inicio'] else None
            ag['hora_fim'] = str(ag['hora_fim']) if ag['hora_fim'] else None
            ag['data_registro'] = ag['data_registro'].isoformat() if ag['data_registro'] else None
            
        return jsonify(agendamentos), 200
    except mysql.connector.Error as err:
        print(f"Erro ao buscar agendamentos: {err}")
        return jsonify({"erro": "Erro ao buscar agendamentos no banco de dados"}), 500
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    app.run(debug=True)