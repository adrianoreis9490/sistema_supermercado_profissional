"""Funções de cadastro e consulta de produtos."""
from banco import conectar

def calcular_preco_venda(custo, imposto_percentual, lucro_percentual):
    # Regra simples: acrescenta imposto e lucro calculados sobre o custo.
    return round(custo * (1 + imposto_percentual / 100 + lucro_percentual / 100), 2)

def salvar_produto(codigo, nome, custo, imposto, lucro, estoque, codigo_original=None):
    codigo = codigo.strip()
    nome = nome.strip()
    if not codigo or not nome:
        raise ValueError("Informe o código e o nome do produto.")
    if custo < 0 or imposto < 0 or lucro < 0 or estoque < 0:
        raise ValueError("Valores e estoque não podem ser negativos.")
    preco = calcular_preco_venda(custo, imposto, lucro)
    with conectar() as conn:
        if codigo_original and codigo_original != codigo:
            conn.execute("DELETE FROM produtos WHERE codigo=?", (codigo_original,))
        conn.execute("""
            INSERT INTO produtos(codigo,nome,preco_custo,imposto,lucro,preco_venda,estoque,ativo)
            VALUES(?,?,?,?,?,?,?,1)
            ON CONFLICT(codigo) DO UPDATE SET
              nome=excluded.nome, preco_custo=excluded.preco_custo,
              imposto=excluded.imposto, lucro=excluded.lucro,
              preco_venda=excluded.preco_venda, estoque=excluded.estoque, ativo=1
        """, (codigo, nome, custo, imposto, lucro, preco, estoque))
        conn.execute("""
            INSERT INTO movimentos_estoque(codigo_produto,nome_produto,tipo,quantidade,observacao)
            VALUES(?,?,?,?,?)
        """, (codigo, nome, "ENTRADA", estoque, "Cadastro/atualização de estoque"))

def listar_produtos(apenas_ativos=False):
    with conectar() as conn:
        sql = "SELECT * FROM produtos"
        if apenas_ativos:
            sql += " WHERE ativo=1"
        return conn.execute(sql + " ORDER BY nome").fetchall()

def buscar_produto(codigo):
    with conectar() as conn:
        return conn.execute("SELECT * FROM produtos WHERE codigo=? AND ativo=1", (codigo.strip(),)).fetchone()

def ajustar_estoque(codigo, quantidade, observacao="Reposição manual"):
    if quantidade <= 0:
        raise ValueError("A entrada precisa ser maior que zero.")
    with conectar() as conn:
        p = conn.execute("SELECT nome FROM produtos WHERE codigo=? AND ativo=1", (codigo,)).fetchone()
        if not p:
            raise ValueError("Produto não encontrado.")
        conn.execute("UPDATE produtos SET estoque=estoque+? WHERE codigo=?", (quantidade, codigo))
        conn.execute("""
            INSERT INTO movimentos_estoque(codigo_produto,nome_produto,tipo,quantidade,observacao)
            VALUES(?,?,?,?,?)
        """, (codigo, p["nome"], "ENTRADA", quantidade, observacao))
