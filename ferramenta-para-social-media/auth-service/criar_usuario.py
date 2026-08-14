"""
Script de setup: cria o ÚNICO usuário permitido no sistema.

Rode este script UMA VEZ (ou sempre que precisar resetar sua senha):
    python criar_usuario.py

Esse projeto não tem endpoint público de cadastro de propósito —
é uma ferramenta pessoal, e você é o único usuário possível.
"""

import getpass

from app.database import Base, engine, SessionLocal
from app.models import Usuario
from app.auth import gerar_hash_senha


def criar_tabelas():
    """Cria as tabelas no banco (se ainda não existirem), com base nos models."""
    Base.metadata.create_all(bind=engine)
    print("Tabelas verificadas/criadas com sucesso.")


def criar_ou_atualizar_usuario():
    db = SessionLocal()
    try:
        usuario_existente = db.query(Usuario).first()

        if usuario_existente:
            print(f"\nJá existe um usuário cadastrado: {usuario_existente.email}")
            resposta = input("Deseja RESETAR a senha desse usuário? (s/n): ").strip().lower()
            if resposta != "s":
                print("Nada foi alterado.")
                return

            nova_senha = getpass.getpass("Nova senha: ")
            confirmacao = getpass.getpass("Confirme a nova senha: ")
            if nova_senha != confirmacao:
                print("As senhas não coincidem. Operação cancelada.")
                return

            usuario_existente.senha_hash = gerar_hash_senha(nova_senha)
            db.commit()
            print("Senha atualizada com sucesso.")
            return

        # Não existe usuário ainda -> vamos criar o único usuário do sistema
        print("\nNenhum usuário encontrado. Vamos criar o seu.\n")
        nome = input("Seu nome: ").strip()
        email = input("Seu e-mail: ").strip()
        senha = getpass.getpass("Senha: ")
        confirmacao = getpass.getpass("Confirme a senha: ")

        if senha != confirmacao:
            print("As senhas não coincidem. Operação cancelada.")
            return

        novo_usuario = Usuario(
            nome=nome,
            email=email,
            senha_hash=gerar_hash_senha(senha),
        )
        db.add(novo_usuario)
        db.commit()
        print(f"\nUsuário '{nome}' criado com sucesso! Já pode fazer login com {email}.")

    finally:
        db.close()


if __name__ == "__main__":
    criar_tabelas()
    criar_ou_atualizar_usuario()