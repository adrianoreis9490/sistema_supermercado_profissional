"""Aplicativo principal do sistema de supermercado."""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import calendar
import os
import sys
import subprocess
from pathlib import Path

from banco import inicializar_banco, conectar
from login import tela_login
from produtos import salvar_produto, listar_produtos, buscar_produto, ajustar_estoque
from vendas import concluir_venda
from recibo import gerar_recibo
from historico import listar_vendas, itens_da_venda
from relatorios import exportar_excel, exportar_pdf
from funcionarios import listar_funcionarios, salvar_funcionario, alterar_ativo

PASTA = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
RECURSOS = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))

def dinheiro(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def abrir_arquivo(caminho):
    try:
        os.startfile(str(caminho))  # Windows: abre PDF/Excel no aplicativo padrão.
    except AttributeError:
        subprocess.Popen(["cmd", "/c", "start", "", str(caminho)], shell=True)

class Aplicativo:
    def __init__(self, usuario):
        self.usuario = usuario
        self.carrinho = []
        self.janela = tk.Tk()
        self.janela.title("Comercial Bela Vista • Sistema de Caixa")
        self.janela.geometry("1180x760")
        self.janela.minsize(980, 650)
        self.janela.configure(bg="#EDF2F7")
        self._estilo()
        self._montar()
        self.atualizar_tabela_produtos()
        self.atualizar_historico()
        self.janela.mainloop()

    def _estilo(self):
        estilo = ttk.Style()
        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass
        estilo.configure("Treeview", rowheight=27, font=("Segoe UI", 10))
        estilo.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        estilo.configure("TNotebook.Tab", padding=(16, 9), font=("Segoe UI", 10, "bold"))

    def _botao(self, pai, texto, comando, cor="#167D5A"):
        return tk.Button(pai, text=texto, command=comando, bg=cor, fg="white",
                         activebackground=cor, activeforeground="white",
                         relief="flat", padx=12, pady=8, font=("Segoe UI", 10, "bold"),
                         cursor="hand2")

    def _montar(self):
        topo = tk.Frame(self.janela, bg="#102A43", height=68)
        topo.pack(fill="x")
        tk.Label(topo, text="🛒 Comercial Bela Vista", font=("Segoe UI", 20, "bold"),
                 fg="white", bg="#102A43").pack(side="left", padx=22, pady=14)
        self.status = tk.Label(topo, text=f"Funcionário: {self.usuario['nome']}  •  Perfil: {self.usuario['perfil'].upper()}",
                               fg="#D9E2EC", bg="#102A43", font=("Segoe UI", 10))
        self.status.pack(side="right", padx=20)

        self.abas = ttk.Notebook(self.janela)
        self.abas.pack(fill="both", expand=True, padx=12, pady=12)
        self.aba_vendas = ttk.Frame(self.abas)
        self.aba_produtos = ttk.Frame(self.abas)
        self.aba_historico = ttk.Frame(self.abas)
        self.aba_relatorios = ttk.Frame(self.abas)
        self.abas.add(self.aba_vendas, text="Caixa / Vendas")
        self.abas.add(self.aba_produtos, text="Produtos / Estoque")
        self.abas.add(self.aba_historico, text="Histórico")
        self.abas.add(self.aba_relatorios, text="Relatórios")
        self._montar_vendas()
        self._montar_produtos()
        self._montar_historico()
        self._montar_relatorios()
        if self.usuario["perfil"] == "gerente":
            self.aba_funcionarios = ttk.Frame(self.abas)
            self.abas.add(self.aba_funcionarios, text="Funcionários")
            self._montar_funcionarios()
        self.janela.bind("<F2>", lambda e: self.codigo.focus_set())
        self.janela.bind("<F4>", lambda e: self.abrir_pagamento())
        self.janela.bind("<F5>", lambda e: self.proximo_cliente())
        self.janela.bind("<Key>", self._atalhos)
        self.janela.protocol("WM_DELETE_WINDOW", self.janela.destroy)

    def _atalhos(self, event):
        # Evita trocar pagamento quando o usuário está digitando em outro campo.
        if self.abas.select() != str(self.aba_vendas):
            return
        if event.char in ("1", "2", "3", "4") and self.janela.focus_get() not in (
            self.codigo, self.quantidade
        ):
            self.forma.set({"1":"Dinheiro", "2":"Débito", "3":"Crédito", "4":"Pix"}[event.char])

    def _montar_vendas(self):
        raiz = self.aba_vendas
        raiz.columnconfigure(0, weight=3)
        raiz.columnconfigure(1, weight=2)
        raiz.rowconfigure(1, weight=1)
        tk.Label(raiz, text="CAIXA DE VENDAS", font=("Segoe UI", 18, "bold"),
                 bg="#F0F4F8", fg="#102A43", anchor="w", padx=18, pady=12).grid(
                 row=0, column=0, columnspan=2, sticky="ew")
        esquerda = tk.Frame(raiz, bg="#FFFFFF", padx=16, pady=14)
        esquerda.grid(row=1, column=0, sticky="nsew", padx=(12, 6), pady=8)
        direita = tk.Frame(raiz, bg="#D9EAF7", padx=18, pady=18)
        direita.grid(row=1, column=1, sticky="nsew", padx=(6, 12), pady=8)
        self.imagem_carrinho = tk.PhotoImage(
            file=str(RECURSOS / "assets" / "carrinho_compras.png")
        )
        fundo_carrinho = tk.Label(direita, image=self.imagem_carrinho, bg="#D9EAF7")
        fundo_carrinho.place(relx=0.5, rely=1.0, anchor="s", y=-8)
        fundo_carrinho.lower()

        tk.Label(esquerda, text="Código do produto / código de barras", bg="white",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.codigo = tk.Entry(esquerda, font=("Segoe UI", 15))
        self.codigo.pack(fill="x", pady=(4, 10))
        tk.Label(esquerda, text="Quantidade", bg="white", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.quantidade = tk.Entry(esquerda, font=("Segoe UI", 13))
        self.quantidade.insert(0, "1")
        self.quantidade.pack(fill="x", pady=(4, 10))
        self._botao(esquerda, "ADICIONAR PRODUTO  (Enter)", self.adicionar_produto).pack(fill="x")
        cols = ("codigo", "nome", "qtd", "preco", "subtotal")
        self.tabela_carrinho = ttk.Treeview(esquerda, columns=cols, show="headings", height=12)
        for col, titulo, largura in [
            ("codigo","Código",85),("nome","Produto",210),("qtd","Qtd.",55),
            ("preco","Preço",90),("subtotal","Subtotal",100)]:
            self.tabela_carrinho.heading(col, text=titulo)
            self.tabela_carrinho.column(col, width=largura, anchor="w" if col=="nome" else "e")
        self.tabela_carrinho.pack(fill="both", expand=True, pady=12)
        linha = tk.Frame(esquerda, bg="white")
        linha.pack(fill="x")
        self._botao(linha, "Remover item selecionado", self.remover_item, "#B83227").pack(side="left")
        self._botao(linha, "Limpar carrinho", self.limpar_carrinho, "#627D98").pack(side="right")

        tk.Label(direita, text="TOTAL DA COMPRA", font=("Segoe UI", 12, "bold"),
                 bg="#D9EAF7", fg="#102A43").pack(anchor="w")
        self.label_total = tk.Label(direita, text=dinheiro(0), font=("Segoe UI", 30, "bold"),
                                    bg="#D9EAF7", fg="#167D5A")
        self.label_total.pack(anchor="w", pady=(4, 20))
        tk.Label(direita, text="Forma de pagamento", font=("Segoe UI", 12, "bold"),
                 bg="#D9EAF7").pack(anchor="w")
        self.forma = tk.StringVar(value="Dinheiro")
        for texto, valor in [("1  •  Dinheiro","Dinheiro"),("2  •  Débito","Débito"),
                             ("3  •  Crédito","Crédito"),("4  •  Pix","Pix")]:
            tk.Radiobutton(direita, text=texto, variable=self.forma, value=valor,
                           font=("Segoe UI", 12), bg="#D9EAF7", activebackground="#D9EAF7").pack(anchor="w", pady=3)
        self._botao(direita, "PAGAR  (F4)", self.abrir_pagamento, "#1565C0").pack(fill="x", pady=(20, 8))
        self._botao(direita, "PRÓXIMO CLIENTE  (F5)", self.proximo_cliente, "#B7791F").pack(fill="x")
        tk.Label(direita, text="Scanner USB: conecte e leia o código no campo Código.\nF2: focar código • F4: pagar • F5: próximo cliente",
                 bg="#D9EAF7", fg="#334E68", justify="left", wraplength=280).pack(anchor="w", pady=18)
        self.codigo.bind("<Return>", lambda e: self.adicionar_produto())
        self.quantidade.bind("<Return>", lambda e: self.adicionar_produto())

    def total(self):
        return round(sum(i["preco"] * i["quantidade"] for i in self.carrinho), 2)

    def adicionar_produto(self):
        codigo = self.codigo.get().strip()
        try:
            qtd = int(self.quantidade.get())
            if qtd <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Quantidade inválida", "Digite uma quantidade inteira maior que zero.")
            self.quantidade.focus_set()
            return
        p = buscar_produto(codigo)
        if not p:
            messagebox.showerror("Produto não encontrado", f"Não existe produto ativo com código {codigo}.")
            self.codigo.focus_set()
            return
        ja_no_carrinho = sum(i["quantidade"] for i in self.carrinho if i["codigo"] == codigo)
        if ja_no_carrinho + qtd > p["estoque"]:
            messagebox.showerror("Estoque insuficiente", f"Disponível: {p['estoque']} unidade(s).")
            return
        item = next((i for i in self.carrinho if i["codigo"] == codigo), None)
        if item:
            item["quantidade"] += qtd
        else:
            self.carrinho.append({"codigo":codigo, "nome":p["nome"], "preco":p["preco_venda"], "quantidade":qtd})
        self.atualizar_carrinho()
        self.codigo.delete(0, tk.END)
        self.quantidade.delete(0, tk.END)
        self.quantidade.insert(0, "1")
        self.codigo.focus_set()

    def atualizar_carrinho(self):
        self.tabela_carrinho.delete(*self.tabela_carrinho.get_children())
        for i in self.carrinho:
            self.tabela_carrinho.insert("", "end", values=(
                i["codigo"], i["nome"], i["quantidade"], dinheiro(i["preco"]),
                dinheiro(i["preco"] * i["quantidade"])))
        self.label_total.config(text=dinheiro(self.total()))

    def remover_item(self):
        selecionado = self.tabela_carrinho.selection()
        if not selecionado:
            messagebox.showwarning("Selecione", "Selecione um item do carrinho.")
            return
        codigo = str(self.tabela_carrinho.item(selecionado[0], "values")[0])
        self.carrinho = [i for i in self.carrinho if i["codigo"] != codigo]
        self.atualizar_carrinho()

    def limpar_carrinho(self):
        if self.carrinho and messagebox.askyesno("Limpar", "Remover todos os itens do carrinho?"):
            self.carrinho.clear()
            self.atualizar_carrinho()

    def abrir_pagamento(self):
        total = self.total()
        if total <= 0:
            messagebox.showwarning("Carrinho vazio", "Adicione produtos antes de pagar.")
            return
        pag = tk.Toplevel(self.janela)
        pag.title("Pagamento")
        pag.geometry("420x360")
        pag.transient(self.janela)
        pag.grab_set()
        pag.configure(bg="#F0F4F8")
        tk.Label(pag, text="CONFIRMAR PAGAMENTO", font=("Segoe UI", 16, "bold"),
                 bg="#F0F4F8", fg="#102A43").pack(pady=15)
        tk.Label(pag, text=f"Valor da compra: {dinheiro(total)}", font=("Segoe UI", 14, "bold"),
                 bg="#F0F4F8").pack(pady=5)
        metodo = self.forma.get()
        if metodo == "Dinheiro":
            tk.Label(pag, text="Valor recebido (R$)", bg="#F0F4F8").pack(pady=(12, 2))
            recebido = tk.Entry(pag, font=("Segoe UI", 14))
            recebido.pack()
            resultado = tk.Label(pag, text="Restante: " + dinheiro(total), bg="#F0F4F8",
                                 font=("Segoe UI", 11, "bold"))
            resultado.pack(pady=12)
            def calcular(event=None):
                try:
                    valor = float(recebido.get().strip().replace(",", "."))
                    if valor < 0:
                        raise ValueError
                except ValueError:
                    messagebox.showerror("Valor inválido", "Digite um valor numérico, como 50,00.", parent=pag)
                    return
                restante = round(total - valor, 2)
                if restante > 0:
                    resultado.config(text=f"Restante a pagar: {dinheiro(restante)}")
                    return
                troco = round(valor - total, 2)
                resultado.config(text=f"Troco: {dinheiro(troco)}")
                self.finalizar_venda(metodo, valor, troco)
                pag.destroy()
            self._botao(pag, "CONFIRMAR DINHEIRO", calcular).pack(pady=5)
            recebido.bind("<Return>", calcular)
            recebido.focus_set()
        else:
            tk.Label(pag, text=f"Forma escolhida: {metodo}\nConfirme após receber a autorização do pagamento.",
                     bg="#F0F4F8", font=("Segoe UI", 11), justify="center").pack(pady=20)
            def confirmar(event=None):
                self.finalizar_venda(metodo, None, 0)
                pag.destroy()
            self._botao(pag, "CONFIRMAR  (Enter)", confirmar, "#1565C0").pack(pady=8)
            pag.bind("<Return>", confirmar)

    def finalizar_venda(self, metodo, recebido, troco):
        try:
            venda_id, total = concluir_venda(self.carrinho, metodo, self.usuario["id"])
            itens_recibo = [(i["nome"], i["quantidade"], i["preco"], i["preco"]*i["quantidade"])
                            for i in self.carrinho]
            arquivo = gerar_recibo(itens_recibo, total, metodo, venda_id, recebido, troco)
            self.carrinho.clear()
            self.atualizar_carrinho()
            self.atualizar_tabela_produtos()
            self.atualizar_historico()
            messagebox.showinfo("Compra finalizada", f"Compra #{venda_id} finalizada!\nTroco: {dinheiro(troco)}\n\nRecibo: {arquivo}")
            if messagebox.askyesno("Recibo", "Deseja abrir o recibo PDF agora?"):
                abrir_arquivo(arquivo)
            self.codigo.focus_set()
        except Exception as exc:
            messagebox.showerror("Não foi possível finalizar", str(exc))

    def proximo_cliente(self):
        if self.carrinho:
            if not messagebox.askyesno("Próximo cliente", "O carrinho tem itens. Deseja descartá-los?"):
                return
            self.carrinho.clear()
            self.atualizar_carrinho()
        self.status.config(text=f"Funcionário: {self.usuario['nome']}  •  PRÓXIMO CLIENTE")
        self.codigo.focus_set()

    def _montar_produtos(self):
        f = self.aba_produtos
        topo = tk.Frame(f, padx=12, pady=12)
        topo.pack(fill="x")
        tk.Label(topo, text="Cadastro e entrada de estoque", font=("Segoe UI", 16, "bold")).grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 10))
        campos = [
            ("Código / barras", "codigo"), ("Nome", "nome"), ("Preço de custo", "custo"),
            ("Imposto (%)", "imposto"), ("Lucro (%)", "lucro"), ("Estoque inicial", "estoque")
        ]
        self.campos_produto = {}
        for idx, (rotulo, chave) in enumerate(campos):
            r, c = 1 + idx // 3, (idx % 3) * 2
            tk.Label(topo, text=rotulo).grid(row=r, column=c, sticky="w", padx=(0, 6), pady=5)
            ent = tk.Entry(topo, width=22)
            ent.grid(row=r, column=c+1, sticky="ew", padx=(0, 14), pady=5)
            self.campos_produto[chave] = ent
        for c in range(6):
            topo.columnconfigure(c, weight=1)
        linha = tk.Frame(f, padx=12)
        linha.pack(fill="x")
        self._botao(linha, "Salvar produto", self.salvar_produto_ui).pack(side="left", padx=(0, 8))
        self._botao(linha, "Limpar campos", self.limpar_campos_produto, "#627D98").pack(side="left", padx=8)
        tk.Label(linha, text="Para repor estoque: informe o código e a quantidade na caixa abaixo.",
                 fg="#486581").pack(side="left", padx=12)
        rep = tk.Frame(f, padx=12, pady=8)
        rep.pack(fill="x")
        tk.Label(rep, text="Código").pack(side="left")
        self.rep_codigo = tk.Entry(rep, width=18)
        self.rep_codigo.pack(side="left", padx=5)
        tk.Label(rep, text="Quantidade de entrada").pack(side="left")
        self.rep_qtd = tk.Entry(rep, width=10)
        self.rep_qtd.pack(side="left", padx=5)
        self._botao(rep, "Registrar entrada", self.entrada_estoque).pack(side="left", padx=8)
        cols = ("codigo","nome","custo","imposto","lucro","preco","estoque")
        self.tabela_produtos = ttk.Treeview(f, columns=cols, show="headings")
        titulos = {"codigo":"Código","nome":"Produto","custo":"Custo","imposto":"Imposto %","lucro":"Lucro %",
                   "preco":"Preço venda","estoque":"Estoque"}
        larguras = {"codigo":110,"nome":240,"custo":95,"imposto":90,"lucro":80,"preco":110,"estoque":80}
        for c in cols:
            self.tabela_produtos.heading(c, text=titulos[c])
            self.tabela_produtos.column(c, width=larguras[c], anchor="w" if c=="nome" else "e")
        self.tabela_produtos.pack(fill="both", expand=True, padx=12, pady=12)

    def salvar_produto_ui(self):
        try:
            c = self.campos_produto
            codigo, nome = c["codigo"].get(), c["nome"].get()
            custo = float(c["custo"].get().replace(",", "."))
            imposto = float(c["imposto"].get().replace(",", "."))
            lucro = float(c["lucro"].get().replace(",", "."))
            estoque = int(c["estoque"].get())
            salvar_produto(codigo, nome, custo, imposto, lucro, estoque)
            self.atualizar_tabela_produtos()
            messagebox.showinfo("Produto salvo", "Produto cadastrado/atualizado.")
        except Exception as exc:
            messagebox.showerror("Cadastro inválido", str(exc))

    def limpar_campos_produto(self):
        for ent in self.campos_produto.values():
            ent.delete(0, tk.END)

    def entrada_estoque(self):
        try:
            codigo = self.rep_codigo.get().strip()
            qtd = int(self.rep_qtd.get())
            ajustar_estoque(codigo, qtd)
            self.atualizar_tabela_produtos()
            messagebox.showinfo("Estoque", "Entrada registrada.")
            self.rep_qtd.delete(0, tk.END)
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))

    def atualizar_tabela_produtos(self):
        if not hasattr(self, "tabela_produtos"):
            return
        self.tabela_produtos.delete(*self.tabela_produtos.get_children())
        for p in listar_produtos():
            self.tabela_produtos.insert("", "end", values=(
                p["codigo"], p["nome"], dinheiro(p["preco_custo"]), f'{p["imposto"]:.2f}',
                f'{p["lucro"]:.2f}', dinheiro(p["preco_venda"]), p["estoque"]))

    def _montar_historico(self):
        barra = tk.Frame(self.aba_historico, padx=12, pady=12)
        barra.pack(fill="x")
        tk.Label(barra, text="Últimas vendas", font=("Segoe UI", 16, "bold")).pack(side="left")
        self._botao(barra, "Atualizar", self.atualizar_historico, "#627D98").pack(side="right")
        cols = ("id","data","total","pagamento","funcionario")
        self.tabela_historico = ttk.Treeview(self.aba_historico, columns=cols, show="headings")
        for c, titulo, largura in [
            ("id","Venda",70),("data","Data",180),("total","Total",120),
            ("pagamento","Pagamento",120),("funcionario","Funcionário",200)]:
            self.tabela_historico.heading(c, text=titulo)
            self.tabela_historico.column(c, width=largura)
        self.tabela_historico.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self._botao(self.aba_historico, "Ver itens da venda selecionada", self.ver_itens).pack(anchor="w", padx=12, pady=(0, 12))

    def atualizar_historico(self):
        if not hasattr(self, "tabela_historico"):
            return
        self.tabela_historico.delete(*self.tabela_historico.get_children())
        for v in listar_vendas():
            self.tabela_historico.insert("", "end", values=(
                v["id"], v["data"], dinheiro(v["total"]), v["pagamento"], v["funcionario"]))

    def ver_itens(self):
        sel = self.tabela_historico.selection()
        if not sel:
            messagebox.showwarning("Selecione", "Selecione uma venda.")
            return
        venda_id = int(self.tabela_historico.item(sel[0], "values")[0])
        itens = itens_da_venda(venda_id)
        texto = "\n".join(f'{i["nome_produto"]} — {i["quantidade"]} x {dinheiro(i["preco_unitario"])} = {dinheiro(i["subtotal"])}'
                          for i in itens)
        messagebox.showinfo(f"Itens da venda #{venda_id}", texto or "Sem itens registrados.")

    def _montar_relatorios(self):
        f = self.aba_relatorios
        corpo = tk.Frame(f, padx=24, pady=24)
        corpo.pack(anchor="nw")
        tk.Label(corpo, text="Relatórios mensais", font=("Segoe UI", 18, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 16))
        agora = datetime.now()
        tk.Label(corpo, text="Ano").grid(row=1, column=0, sticky="w")
        self.ano_rel = tk.Entry(corpo, width=12)
        self.ano_rel.insert(0, str(agora.year))
        self.ano_rel.grid(row=2, column=0, sticky="w", pady=(2, 12))
        tk.Label(corpo, text="Mês (1 a 12)").grid(row=1, column=1, sticky="w", padx=15)
        self.mes_rel = tk.Entry(corpo, width=12)
        self.mes_rel.insert(0, str(agora.month))
        self.mes_rel.grid(row=2, column=1, sticky="w", padx=15, pady=(2, 12))
        self._botao(corpo, "Exportar PDF", lambda: self.exportar_relatorio("pdf"), "#1565C0").grid(
            row=3, column=0, sticky="ew", pady=6)
        self._botao(corpo, "Exportar Excel", lambda: self.exportar_relatorio("xlsx")).grid(
            row=3, column=1, sticky="ew", padx=15, pady=6)
        tk.Label(corpo, text="Os arquivos serão salvos na pasta relatorios.",
                 fg="#486581").grid(row=4, column=0, columnspan=2, sticky="w", pady=12)

    def exportar_relatorio(self, tipo):
        try:
            ano, mes = int(self.ano_rel.get()), int(self.mes_rel.get())
            if ano < 2000 or mes < 1 or mes > 12:
                raise ValueError("Informe um ano válido e um mês entre 1 e 12.")
            arquivo = exportar_pdf(ano, mes) if tipo == "pdf" else exportar_excel(ano, mes)
            messagebox.showinfo("Relatório gerado", f"Arquivo criado:\n{arquivo}")
            if messagebox.askyesno("Abrir arquivo", "Deseja abrir o relatório agora?"):
                abrir_arquivo(arquivo)
        except Exception as exc:
            messagebox.showerror("Erro no relatório", str(exc))

    def _montar_funcionarios(self):
        f = self.aba_funcionarios
        topo = tk.Frame(f, padx=16, pady=16)
        topo.pack(fill="x")
        tk.Label(topo, text="Cadastro de funcionários", font=("Segoe UI", 16, "bold")).grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 12))
        self.fun_usuario = tk.Entry(topo, width=18)
        self.fun_nome = tk.Entry(topo, width=22)
        self.fun_senha = tk.Entry(topo, width=18, show="*")
        self.fun_perfil = tk.StringVar(value="caixa")
        for col, (label, widget) in enumerate([
            ("Usuário", self.fun_usuario), ("Nome", self.fun_nome), ("Senha inicial", self.fun_senha),
            ("Perfil", ttk.Combobox(topo, textvariable=self.fun_perfil, values=("caixa","gerente"), state="readonly", width=12))
        ]):
            tk.Label(topo, text=label).grid(row=1, column=col, sticky="w", padx=4)
            widget.grid(row=2, column=col, padx=4, pady=5, sticky="ew")
        self._botao(topo, "Cadastrar funcionário", self.salvar_funcionario_ui).grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=8)
        self.tabela_func = ttk.Treeview(f, columns=("id","usuario","nome","perfil","ativo"), show="headings")
        for c, t in [("id","ID"),("usuario","Usuário"),("nome","Nome"),("perfil","Perfil"),("ativo","Ativo")]:
            self.tabela_func.heading(c, text=t)
        self.tabela_func.pack(fill="both", expand=True, padx=16, pady=10)
        self._botao(f, "Ativar/desativar selecionado", self.toggle_funcionario, "#B7791F").pack(anchor="w", padx=16, pady=(0, 12))
        self.atualizar_funcionarios()

    def salvar_funcionario_ui(self):
        try:
            salvar_funcionario(self.fun_usuario.get(), self.fun_nome.get(),
                               self.fun_senha.get(), self.fun_perfil.get())
            self.fun_senha.delete(0, tk.END)
            self.atualizar_funcionarios()
            messagebox.showinfo("Funcionário", "Funcionário cadastrado.")
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))

    def atualizar_funcionarios(self):
        if not hasattr(self, "tabela_func"):
            return
        self.tabela_func.delete(*self.tabela_func.get_children())
        for u in listar_funcionarios():
            self.tabela_func.insert("", "end", values=(u["id"],u["usuario"],u["nome"],u["perfil"],
                                                        "Sim" if u["ativo"] else "Não"))

    def toggle_funcionario(self):
        sel = self.tabela_func.selection()
        if not sel:
            messagebox.showwarning("Selecione", "Selecione um funcionário.")
            return
        valores = self.tabela_func.item(sel[0], "values")
        funcionario_id, ativo = int(valores[0]), valores[4] == "Sim"
        if funcionario_id == self.usuario["id"]:
            messagebox.showwarning("Atenção", "Não é possível desativar a própria conta durante a sessão.")
            return
        alterar_ativo(funcionario_id, not ativo)
        self.atualizar_funcionarios()

def iniciar():
    inicializar_banco()
    tela_login(lambda usuario: Aplicativo(usuario))

if __name__ == "__main__":
    iniciar()
