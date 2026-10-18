"""Tela de login."""
import tkinter as tk
from tkinter import messagebox
from banco import conectar
from seguranca import verificar_senha

def tela_login(ao_entrar):
    janela = tk.Tk()
    janela.title("Comercial Bela Vista • Acesso")
    janela.geometry("420x300")
    janela.resizable(False, False)
    janela.configure(bg="#102A43")

    tk.Label(janela, text="COMERCIAL BELA VISTA", font=("Segoe UI", 21, "bold"),
             fg="white", bg="#102A43").pack(pady=(25, 8))
    tk.Label(janela, text="Entre com sua conta", font=("Segoe UI", 10),
             fg="#D9E2EC", bg="#102A43").pack()

    corpo = tk.Frame(janela, bg="#F0F4F8", padx=25, pady=20)
    corpo.pack(fill="x", padx=25, pady=18)
    tk.Label(corpo, text="Usuário", bg="#F0F4F8").grid(row=0, column=0, sticky="w")
    usuario = tk.Entry(corpo, font=("Segoe UI", 11))
    usuario.grid(row=1, column=0, sticky="ew", pady=(2, 10))
    tk.Label(corpo, text="Senha", bg="#F0F4F8").grid(row=2, column=0, sticky="w")
    senha = tk.Entry(corpo, show="*", font=("Segoe UI", 11))
    senha.grid(row=3, column=0, sticky="ew", pady=(2, 12))
    corpo.columnconfigure(0, weight=1)

    def validar(event=None):
        with conectar() as conn:
            u = conn.execute("SELECT * FROM usuarios WHERE usuario=? AND ativo=1",
                             (usuario.get().strip(),)).fetchone()
        if u and verificar_senha(senha.get(), u["senha_hash"]):
            janela.destroy()
            ao_entrar(dict(u))
        else:
            messagebox.showerror("Acesso negado", "Usuário ou senha inválidos.", parent=janela)
            senha.delete(0, tk.END)
            senha.focus_set()

    tk.Button(corpo, text="ENTRAR", command=validar, bg="#167D5A", fg="white",
              font=("Segoe UI", 10, "bold"), relief="flat", pady=8).grid(row=4, column=0, sticky="ew")
    janela.bind("<Return>", validar)
    usuario.focus_set()
    janela.mainloop()
