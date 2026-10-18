"""Operações de venda com baixa de estoque e gravação atômica."""
from banco import conectar
from banco import registrar_movimento

def concluir_venda(carrinho, pagamento, funcionario_id):
    """Grava venda/itens e baixa estoque dentro de uma transação."""
    if not carrinho:
        raise ValueError("O carrinho está vazio.")
    total = round(sum(item["preco"] * item["quantidade"] for item in carrinho), 2)
    with conectar() as conn:
        # Confere estoque novamente para evitar vender unidades inexistentes.
        for item in carrinho:
            p = conn.execute("SELECT nome,estoque FROM produtos WHERE codigo=? AND ativo=1",
                             (item["codigo"],)).fetchone()
            if not p:
                raise ValueError(f"Produto {item['codigo']} não está disponível.")
            if p["estoque"] < item["quantidade"]:
                raise ValueError(f"Estoque insuficiente para {p['nome']}.")
        cur = conn.execute(
            "INSERT INTO vendas(total,pagamento,funcionario_id) VALUES(?,?,?)",
            (total, pagamento, funcionario_id))
        venda_id = cur.lastrowid
        for item in carrinho:
            qtd = item["quantidade"]
            conn.execute("""
                INSERT INTO itens_venda(venda_id,codigo_produto,nome_produto,quantidade,preco_unitario,subtotal)
                VALUES(?,?,?,?,?,?)
            """, (venda_id, item["codigo"], item["nome"], qtd, item["preco"],
                  round(item["preco"] * qtd, 2)))
            conn.execute("UPDATE produtos SET estoque=estoque-? WHERE codigo=?", (qtd, item["codigo"]))
            conn.execute("""
                INSERT INTO movimentos_estoque(codigo_produto,nome_produto,tipo,quantidade,observacao)
                VALUES(?,?,?,?,?)
            """, (item["codigo"], item["nome"], "SAIDA", qtd, f"Venda {venda_id}"))
    return venda_id, total
