"""Banco de dados SQLite do sistema de supermercado."""
import sqlite3
from pathlib import Path

import sys
PASTA = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
DB_PATH = PASTA / "supermercado.db"

def conectar():
    """Abre uma conexão com o banco local."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def inicializar_banco():
    """Cria tabelas e um usuário administrador inicial, se necessário."""
    with conectar() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            senha_hash TEXT NOT NULL,
            perfil TEXT NOT NULL CHECK(perfil IN ('gerente','caixa')),
            ativo INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS produtos (
            codigo TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            preco_custo REAL NOT NULL DEFAULT 0,
            imposto REAL NOT NULL DEFAULT 0,
            lucro REAL NOT NULL DEFAULT 0,
            preco_venda REAL NOT NULL,
            estoque INTEGER NOT NULL DEFAULT 0,
            ativo INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            total REAL NOT NULL,
            pagamento TEXT NOT NULL,
            funcionario_id INTEGER,
            FOREIGN KEY(funcionario_id) REFERENCES usuarios(id)
        );

        CREATE TABLE IF NOT EXISTS itens_venda (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venda_id INTEGER NOT NULL,
            codigo_produto TEXT NOT NULL,
            nome_produto TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            preco_unitario REAL NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY(venda_id) REFERENCES vendas(id)
        );

        CREATE TABLE IF NOT EXISTS movimentos_estoque (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            codigo_produto TEXT NOT NULL,
            nome_produto TEXT NOT NULL,
            tipo TEXT NOT NULL CHECK(tipo IN ('ENTRADA','SAIDA','ESTORNO')),
            quantidade INTEGER NOT NULL,
            observacao TEXT
        );
        """)
        # Senha inicial: admin123. O hash é criado em seguranca.py.
        from seguranca import gerar_hash
        conn.execute("""
            INSERT OR IGNORE INTO usuarios(usuario,nome,senha_hash,perfil,ativo)
            VALUES(?,?,?,?,1)
        """, ("admin", "Administrador", gerar_hash("admin123"), "gerente"))

def registrar_movimento(codigo, nome, tipo, quantidade, observacao=""):
    with conectar() as conn:
        conn.execute("""
            INSERT INTO movimentos_estoque(codigo_produto,nome_produto,tipo,quantidade,observacao)
            VALUES(?,?,?,?,?)
        """, (codigo, nome, tipo, quantidade, observacao))
