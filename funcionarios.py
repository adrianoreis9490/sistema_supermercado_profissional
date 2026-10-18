"""Cadastro de funcionários e perfis de acesso."""
from banco import conectar
from seguranca import gerar_hash

def listar_funcionarios():
    with conectar() as conn:
        return conn.execute("SELECT id,usuario,nome,perfil,ativo FROM usuarios ORDER BY nome").fetchall()

def salvar_funcionario(usuario, nome, senha, perfil):
    usuario, nome = usuario.strip(), nome.strip()
    if not usuario or not nome or not senha:
        raise ValueError("Preencha usuário, nome e senha.")
    if perfil not in ("gerente", "caixa"):
        raise ValueError("Perfil inválido.")
    with conectar() as conn:
        conn.execute("""
            INSERT INTO usuarios(usuario,nome,senha_hash,perfil,ativo)
            VALUES(?,?,?,?,1)
        """, (usuario, nome, gerar_hash(senha), perfil))

def alterar_ativo(funcionario_id, ativo):
    with conectar() as conn:
        conn.execute("UPDATE usuarios SET ativo=? WHERE id=?", (1 if ativo else 0, funcionario_id))
