"""Citizen Assist AI - assistente de orientação ao cidadão (terminal).

Público: jovens no primeiro emprego.
Executar com:  python main.py
"""
import os
import sys

from base_conhecimento import BaseConhecimento
from assistente import Assistente

PASTA = os.path.dirname(os.path.abspath(__file__))
PASTA_DADOS = os.path.join(PASTA, "data")


def main():
    base = BaseConhecimento(os.path.join(PASTA_DADOS, "base_conhecimento.json"))
    if not base.carregar():
        print(f"Não foi possível iniciar o assistente: {base.erro}.")
        print("Verifique o arquivo data/base_conhecimento.json e tente de novo.")
        return 1
    for aviso in base.avisos:
        print(f"Aviso: {aviso}")

    assistente = Assistente("Citizen Assist AI", base, PASTA_DADOS)
    print("Orientações para jovens no primeiro emprego: documentos, "
          "carteira de trabalho, direitos e cidadania.")
    print("Não digite dados pessoais (CPF, telefone, e-mail).")

    try:
        assistente.menu()
    except (KeyboardInterrupt, EOFError):
        print("\n\nEncerrando... salvando os atendimentos.")
        assistente.salvar_historico()
        assistente.exportar_csv()
    return 0


if __name__ == "__main__":
    sys.exit(main())
