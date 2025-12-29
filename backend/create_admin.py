# create_admin.py
from app import app, get_db_connection, bcrypt
import os
import getpass # Para solicitar a senha de forma segura

def create_admin_user():
    """Cria um usuário administrador no banco de dados com senha hasheada."""
    with app.app_context(): # Necessário para usar o Bcrypt
        print("--- Criação do Usuário Administrador ---")
        
        # 1. Obter credenciais
        username = input("Digite o NOME DE USUÁRIO do Admin: ").strip()
        email = input("Digite o EMAIL do Admin: ").strip()
        # Usa getpass para não exibir a senha digitada no console
        password = getpass.getpass("Digite a SENHA do Admin: ").strip()
        
        if not username or not email or not password:
            print("Erro: Todos os campos são obrigatórios.")
            return

        # 2. Hash da Senha
        # Encode a senha para bytes antes de hasear
        hashed_password = bcrypt.generate_password_hash(password.encode('utf-8')).decode('utf-8')
        
        # 3. Conexão e Inserção no DB
        conn = get_db_connection()
        if conn is None:
            print("Erro: Falha na conexão com o banco de dados. Verifique seu .env.")
            return
        
        cursor = conn.cursor()
        try:
            # ⚠️ ATENÇÃO: Esta query assume que você tem uma tabela 'usuarios' com as colunas 'username', 'email' e 'password_hash'
            query = """
            INSERT INTO usuarios (username, email, password_hash, is_admin) 
            VALUES (%s, %s, %s, TRUE)
            """
            values = (username, email, hashed_password)
            cursor.execute(query, values)
            conn.commit()
            print(f"\n✅ Usuário '{username}' criado com sucesso no banco de dados.")

        except Exception as e:
            conn.rollback()
            print(f"\n❌ Erro ao inserir usuário: {e}")
            print("Certifique-se de que a tabela 'usuarios' existe e possui as colunas corretas.")
            
        finally:
            cursor.close()
            conn.close()

if __name__ == '__main__':
    create_admin_user()