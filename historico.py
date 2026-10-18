"""Consultas ao histórico de vendas."""
from banco import conectar

def listar_vendas():
    with conectar() as conn:
        return conn.execute("""
            SELECT v.id,v.data,v.total,v.pagamento,COALESCE(u.nome,'') AS funcionario
            FROM vendas v LEFT JOIN usuarios u ON u.id=v.funcionario_id
            ORDER BY v.id DESC LIMIT 1000
        """).fetchall()

def itens_da_venda(venda_id):
    with conectar() as conn:
        return conn.execute("""
            SELECT codigo_produto,nome_produto,quantidade,preco_unitario,subtotal
            FROM itens_venda WHERE venda_id=?
        """, (venda_id,)).fetchall()
