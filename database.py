import sqlite3
import pandas as pd
import bcrypt
import datetime
import time

DB_NAME = "store.db"

def init_db():
    max_retries = 5
    for attempt in range(max_retries):
        conn = None
        try:
            conn = sqlite3.connect(DB_NAME)
            # Habilitar WAL mode para melhor concorrência online
            conn.execute("PRAGMA journal_mode=WAL;")
            c = conn.cursor()
            
            # Tabela de Usuários
            c.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE NOT NULL,
                            password TEXT NOT NULL,
                            role TEXT NOT NULL,
                            name TEXT
                        )''')
            
            # Migração: Adicionar colunas novas se não existirem
            cols_to_add = [
                ("birth_date", "TEXT"),
                ("email", "TEXT"),
                ("phone", "TEXT"),
                ("cpf", "TEXT"),
                ("profile_image", "BLOB"),
                ("preferred_type", "TEXT"),
                ("preferred_brand", "TEXT"),
                ("preferred_style", "TEXT")
            ]
            
            for col_name, col_type in cols_to_add:
                try:
                    c.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                except sqlite3.OperationalError:
                    pass # Coluna já existe
            
            # Tabela de Produtos
            c.execute('''CREATE TABLE IF NOT EXISTS products (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL,
                            brand TEXT,
                            style TEXT,
                            type TEXT,
                            price REAL,
                            quantity INTEGER,
                            expiration_date TEXT,
                            image BLOB
                        )''')
            
            # Tabela de Vendas
            c.execute('''CREATE TABLE IF NOT EXISTS sales (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            product_id INTEGER,
                            quantity INTEGER,
                            total_value REAL,
                            sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            user_id INTEGER,
                            FOREIGN KEY(product_id) REFERENCES products(id),
                            FOREIGN KEY(user_id) REFERENCES users(id)
                        )''')
            
            # Criar admin padrão se não existir
            c.execute("SELECT * FROM users WHERE username = 'admin'")
            if not c.fetchone():
                hashed = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
                c.execute("INSERT INTO users (username, password, role, name) VALUES (?, ?, ?, ?)",
                          ('admin', hashed.decode('utf-8'), 'admin', 'Administrador'))
            
            conn.commit()
            return # Sucesso
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower():
                if attempt < max_retries - 1:
                    time.sleep(1)
                    if conn: 
                        try: conn.close()
                        except: pass
                    continue
            print(f"Erro ao inicializar DB (tentativa {attempt+1}): {e}")
            if conn:
                try: conn.close()
                except: pass
        except Exception as e:
            print(f"Erro fatal ao inicializar DB: {e}")
            if conn:
                try: conn.close()
                except: pass
            break


def get_connection():
    # Helper para criar conexão com timeout maior para evitar locks
    return sqlite3.connect(DB_NAME, timeout=30)

def execute_write_query(query, params=()):
    """
    Executa uma query de escrita (INSERT, UPDATE, DELETE) com lógica de retry robusta.
    Retorna True se sucesso, False caso contrário.
    """
    max_retries = 5
    conn = None
    for attempt in range(max_retries):
        try:
            conn = get_connection()
            c = conn.cursor()
            c.execute(query, params)
            conn.commit()
            return True
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower():
                if attempt < max_retries - 1:
                    time.sleep(1) # Espera 1s antes de tentar novamente
                    if conn: conn.close()
                    continue
            print(f"Erro operacional no DB (tentativa {attempt+1}): {e}")
            return False
        except Exception as e:
            print(f"Erro geral no DB: {e}")
            return False
        finally:
            if conn: 
                try: conn.close()
                except: pass
    return False

def execute_read_query(query, params=(), fetch_one=False, use_pandas=False):
    """
    Executa uma query de leitura (SELECT) com lógica de retry.
    Retorna resultado, DataFrame ou None/Empty dependendo dos parâmetros.
    """
    max_retries = 5
    conn = None
    for attempt in range(max_retries):
        try:
            conn = get_connection()
            if use_pandas:
                return pd.read_sql_query(query, conn, params=params)
            else:
                c = conn.cursor()
                c.execute(query, params)
                if fetch_one:
                    return c.fetchone()
                else:
                    return c.fetchall()
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower():
                if attempt < max_retries - 1:
                    time.sleep(1)
                    if conn: conn.close()
                    continue
            print(f"Erro de leitura no DB (tentativa {attempt+1}): {e}")
            return pd.DataFrame() if use_pandas else None
        except Exception as e:
            print(f"Erro geral de leitura: {e}")
            return pd.DataFrame() if use_pandas else None
        finally:
            if conn: 
                try: conn.close()
                except: pass
    return pd.DataFrame() if use_pandas else None

# -------------------------------------------------------------------
# Funções de Negócio Refatoradas
# -------------------------------------------------------------------

def check_login(username, password):
    row = execute_read_query("SELECT * FROM users WHERE username = ?", (username,), fetch_one=True)
    if row and bcrypt.checkpw(password.encode('utf-8'), row[2].encode('utf-8')):
        return row
    return None

def create_user(username, password, role, name, birth_date=None, email=None, phone=None, cpf=None, preferred_type=None, preferred_brand=None, preferred_style=None):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return execute_write_query(
        "INSERT INTO users (username, password, role, name, birth_date, email, phone, cpf, preferred_type, preferred_brand, preferred_style) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (username, hashed.decode('utf-8'), role, name, birth_date, email, phone, cpf, preferred_type, preferred_brand, preferred_style)
    )

def update_user_image(user_id, image_bytes):
    success = execute_write_query("UPDATE users SET profile_image = ? WHERE id = ?", (image_bytes, user_id))
    if success:
        return execute_read_query("SELECT * FROM users WHERE id = ?", (user_id,), fetch_one=True)
    return None

def get_birthday_clients():
    return execute_read_query(
        "SELECT * FROM users WHERE role='cliente' AND birth_date IS NOT NULL AND birth_date != ''", 
        use_pandas=True
    )

def add_product(nome, marca, estilo, tipo, preco, quantidade, data_validade, image_bytes, id=None):
    if id is not None:
        # Check exists
        exists = execute_read_query("SELECT id FROM products WHERE id=?", (id,), fetch_one=True)
        if exists:
            if image_bytes:
                return execute_write_query(
                    '''UPDATE products SET name=?, brand=?, style=?, type=?, price=?, quantity=?, expiration_date=?, image=? WHERE id=?''',
                    (nome, marca, estilo, tipo, preco, quantidade, data_validade, image_bytes, id)
                )
            else:
                return execute_write_query(
                    '''UPDATE products SET name=?, brand=?, style=?, type=?, price=?, quantity=?, expiration_date=? WHERE id=?''',
                    (nome, marca, estilo, tipo, preco, quantidade, data_validade, id)
                )
        else:
            return execute_write_query(
                '''INSERT INTO products (id, name, brand, style, type, price, quantity, expiration_date, image) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (id, nome, marca, estilo, tipo, preco, quantidade, data_validade, image_bytes)
            )
    else:
        return execute_write_query(
            '''INSERT INTO products (name, brand, style, type, price, quantity, expiration_date, image) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (nome, marca, estilo, tipo, preco, quantidade, data_validade, image_bytes)
        )

def get_products():
    return execute_read_query("SELECT * FROM products", use_pandas=True)

def update_product(id, nome, marca, estilo, tipo, preco, quantidade, data_validade, image_bytes=None):
    if image_bytes:
        return execute_write_query(
            '''UPDATE products SET name=?, brand=?, style=?, type=?, price=?, quantity=?, expiration_date=?, image=? WHERE id=?''',
            (nome, marca, estilo, tipo, preco, quantidade, data_validade, image_bytes, id)
        )
    else:
        return execute_write_query(
            '''UPDATE products SET name=?, brand=?, style=?, type=?, price=?, quantity=?, expiration_date=? WHERE id=?''',
            (nome, marca, estilo, tipo, preco, quantidade, data_validade, id)
        )

def delete_product(id):
    return execute_write_query("DELETE FROM products WHERE id=?", (id,))

def get_product_by_id(id):
    return execute_read_query("SELECT * FROM products WHERE id=?", (id,), fetch_one=True)

def get_sales_report():
    query = '''
        SELECT s.id, p.name as product_name, s.quantity, s.total_value, s.sale_date, u.name as user_name
        FROM sales s
        LEFT JOIN products p ON s.product_id = p.id
        LEFT JOIN users u ON s.user_id = u.id
    '''
    return execute_read_query(query, use_pandas=True)

def register_sale(product_id, quantity, user_id=None):
    """
    Transação complexa: Verifica estoque, atualiza e insere venda.
    Precisa de controle manual de transação para garantir integridade.
    """
    max_retries = 5
    conn = None
    
    for attempt in range(max_retries):
        try:
            conn = get_connection()
            c = conn.cursor()
            
            # Verificar estoque e preço (dentro da mesma conexão para consistência)
            c.execute("SELECT price, quantity FROM products WHERE id=?", (product_id,))
            res = c.fetchone()
            
            if not res:
                return False, "Produto não encontrado"
            
            price, current_qty = res
            if current_qty < quantity:
                return False, "Estoque insuficiente"
            
            total_value = price * quantity
            
            # Atualizar estoque
            c.execute("UPDATE products SET quantity = quantity - ? WHERE id=?", (quantity, product_id))
            
            # Registrar venda
            c.execute("INSERT INTO sales (product_id, quantity, total_value, user_id) VALUES (?, ?, ?, ?)",
                      (product_id, quantity, total_value, user_id))
            
            conn.commit()
            return True, "Venda realizada com sucesso"
            
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower():
                if attempt < max_retries - 1:
                    time.sleep(1)
                    if conn: 
                        try: conn.rollback()
                        except: pass
                        conn.close()
                    continue
            print(f"Erro transação venda (tentativa {attempt+1}): {e}")
            if conn: 
                try: conn.rollback()
                except: pass
            return False, f"Erro de banco de dados: {e}"
            
        except Exception as e:
            print(f"Erro na venda: {e}")
            if conn: 
                try: conn.rollback()
                except: pass
            return False, f"Erro ao processar venda: {e}"
            
        finally:
            if conn: 
                try: conn.close()
                except: pass
                
    return False, "Sistema ocupado, tente novamente."
