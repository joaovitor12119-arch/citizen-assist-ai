"""Classe Assistente: faz o atendimento, guarda o histórico e calcula indicadores."""
import csv
import json
import os
import time
from datetime import datetime

from base_conhecimento import LIMITE_MEDIA

AVISO_OFICIAL = "Aviso: este assistente NÃO é um canal oficial."
AVISO_DADOS = "Atenção: não digite CPF, telefone ou e-mail. Reescreva."

CAMPOS_CSV = ["data", "sessao", "origem", "pergunta", "id_orientacao",
              "encontrou", "ajudou", "tentativas", "tempo_segundos",
              "nota_facilidade"]


def tem_dado_pessoal(texto):
    """True se o texto tem 8 ou mais dígitos ou um @ (CPF, telefone, e-mail)."""
    digitos = sum(1 for letra in texto if letra.isdigit())
    return digitos >= 8 or "@" in texto


class Assistente:
    """Quem conversa com o cidadão. Tem uma BaseConhecimento (composição)."""

    def __init__(self, nome, base, pasta_dados="data"):
        self.nome = nome
        self.base = base
        self.caminho_historico = os.path.join(pasta_dados, "historico.json")
        self.caminho_csv = os.path.join(pasta_dados, "atendimentos.csv")
        self.sessao = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.historico = []
        self.carregar_historico()

    # ------------------------------------------------------------------
    # Leitura segura de entradas (nunca encerram o programa por erro)
    # ------------------------------------------------------------------
    def ler_opcao(self, texto_pedido, maximo, minimo=0):
        """Pede um número entre minimo e maximo, repetindo até ser válido."""
        while True:
            entrada = input(texto_pedido).strip()
            try:
                numero = int(entrada)
            except ValueError:
                print(f"Opção inválida: digite um número de {minimo} a {maximo}.")
                continue
            if numero < minimo or numero > maximo:
                print(f"Opção inválida: digite um número de {minimo} a {maximo}.")
                continue
            return numero

    def ler_sn(self, texto_pedido):
        """Pede s ou n, repetindo até ser válido. Devolve True para 's'."""
        while True:
            entrada = input(texto_pedido).strip().lower()
            if entrada in ("s", "sim"):
                return True
            if entrada in ("n", "nao", "não"):
                return False
            print("Resposta inválida: digite apenas s (sim) ou n (não).")

    # ------------------------------------------------------------------
    # Menu principal
    # ------------------------------------------------------------------
    def menu(self):
        print(f"\n=== {self.nome} ===")
        print(AVISO_OFICIAL)
        while True:
            print("\nMENU")
            print("  1 - Fazer uma pergunta")
            print("  2 - Navegar por categorias")
            print("  3 - Ver indicadores")
            print("  4 - Exportar atendimentos para CSV")
            print("  0 - Sair")
            opcao = self.ler_opcao("Escolha uma opção: ", 4)
            if opcao == 1:
                self.perguntar()
            elif opcao == 2:
                self.navegar()
            elif opcao == 3:
                self.indicadores()
            elif opcao == 4:
                self.exportar_csv()
            else:
                break
        self.encerrar()

    # ------------------------------------------------------------------
    # Atendimento por pergunta em texto livre
    # ------------------------------------------------------------------
    def perguntar(self):
        while True:
            texto = input("\nDigite sua dúvida (0 para voltar): ").strip()
            if texto == "0":
                return
            if not texto:
                print("Atenção: a dúvida não pode ficar vazia.")
                continue
            if tem_dado_pessoal(texto):
                print(AVISO_DADOS)   # bloqueado: não é registrado
                continue
            self._atender(texto)

    def _atender(self, primeira_pergunta):
        """Um atendimento: repete até a pessoa ser ajudada ou desistir."""
        inicio = time.time()
        pergunta = primeira_pergunta
        tentativas = 1
        encontrou = False
        ajudou = False
        id_final = None

        while True:
            resultados = self.base.buscar(pergunta)
            if resultados and resultados[0][0] >= LIMITE_MEDIA:
                encontrou = True
                pontos, melhor = resultados[0]
                id_final = melhor.id
                print(f"\nConfiança da resposta: "
                      f"{self.base.confianca(pontos)} ({pontos} pontos)")
                melhor.exibir()
                self._mostrar_alternativas(resultados[1:3])
                ajudou = self.ler_sn(
                    "\nEssa orientação respondeu sua dúvida? (s/n): ")
                if ajudou:
                    break
                pedido = ("Reescreva sua dúvida com outras palavras "
                          "(0 para encerrar): ")
            else:
                print("\nNão encontrei uma orientação para essa dúvida.")
                self._mostrar_alternativas(resultados[:2])
                self._sugerir_palavras()
                pedido = "Tente com outras palavras (0 para encerrar): "

            pergunta = self._ler_nova_pergunta(pedido)
            if pergunta is None:
                break
            tentativas += 1

        tempo = round(time.time() - inicio, 1)
        self.registrar("pergunta", primeira_pergunta, id_final, encontrou,
                       ajudou, tentativas, tempo)

    def _ler_nova_pergunta(self, pedido):
        """Lê uma nova tentativa. Devolve None se a pessoa digitar 0."""
        while True:
            texto = input(pedido).strip()
            if texto == "0":
                return None
            if not texto:
                print("Atenção: a dúvida não pode ficar vazia.")
                continue
            if tem_dado_pessoal(texto):
                print(AVISO_DADOS)
                continue
            return texto

    def _mostrar_alternativas(self, alternativas):
        if alternativas:
            print("\nOutras orientações que podem ajudar:")
            for pontos, orientacao in alternativas:
                rotulo = "ponto" if pontos == 1 else "pontos"
                print(f"  - {orientacao.titulo} ({pontos} {rotulo})")

    def _sugerir_palavras(self):
        """Sugere palavras-chave de exemplo e lembra da navegação por categorias."""
        exemplos = []
        for categoria in self.base.categorias():
            primeira = self.base.por_categoria(categoria)[0]
            exemplos.append(primeira.palavras_chave[0])
        print("Dica: use palavras como " + ", ".join(exemplos[:4]) +
              " ou escolha a opção 'Navegar por categorias' no menu.")

    # ------------------------------------------------------------------
    # Navegação por categorias
    # ------------------------------------------------------------------
    def navegar(self):
        categorias = self.base.categorias()
        while True:
            print("\nCATEGORIAS")
            for numero, categoria in enumerate(categorias, 1):
                total = len(self.base.por_categoria(categoria))
                print(f"  {numero} - {categoria} ({total})")
            print("  0 - Voltar")
            escolha = self.ler_opcao("Escolha a categoria: ", len(categorias))
            if escolha == 0:
                return
            self._navegar_categoria(categorias[escolha - 1])

    def _navegar_categoria(self, categoria):
        orientacoes = self.base.por_categoria(categoria)
        inicio = time.time()
        while True:
            print(f"\n{categoria.upper()}")
            for numero, orientacao in enumerate(orientacoes, 1):
                print(f"  {numero} - {orientacao.titulo}")
            print("  0 - Voltar")
            escolha = self.ler_opcao("Escolha a orientação: ", len(orientacoes))
            if escolha == 0:
                return
            orientacao = orientacoes[escolha - 1]
            orientacao.exibir()
            ajudou = self.ler_sn(
                "\nEssa orientação respondeu sua dúvida? (s/n): ")
            tempo = round(time.time() - inicio, 1)
            self.registrar("categoria", orientacao.titulo, orientacao.id,
                           True, ajudou, 1, tempo)
            inicio = time.time()

    # ------------------------------------------------------------------
    # Histórico (data/historico.json)
    # ------------------------------------------------------------------
    def carregar_historico(self):
        """Lê o histórico salvo. Arquivo ausente ou corrompido não trava."""
        if not os.path.exists(self.caminho_historico):
            return
        try:
            with open(self.caminho_historico, "r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
            if not isinstance(dados, list):
                raise ValueError("o histórico deve ser uma lista")
            self.historico = [a for a in dados if isinstance(a, dict)]
        except (json.JSONDecodeError, ValueError, OSError):
            backup = self.caminho_historico.replace(".json", ".corrompido.json")
            print("Aviso: o histórico estava corrompido e será recomeçado "
                  f"(cópia salva em {os.path.basename(backup)}).")
            try:
                os.replace(self.caminho_historico, backup)
            except OSError:
                pass
            self.historico = []

    def salvar_historico(self):
        try:
            os.makedirs(os.path.dirname(self.caminho_historico) or ".",
                        exist_ok=True)
            with open(self.caminho_historico, "w", encoding="utf-8") as arquivo:
                json.dump(self.historico, arquivo, ensure_ascii=False, indent=2)
        except OSError as problema:
            print(f"Aviso: não foi possível salvar o histórico ({problema}).")

    def registrar(self, origem, pergunta, id_orientacao, encontrou, ajudou,
                  tentativas, tempo_segundos):
        """Guarda um atendimento no histórico e salva o arquivo."""
        atendimento = {
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sessao": self.sessao,
            "origem": origem,
            "pergunta": pergunta,
            "id_orientacao": id_orientacao,
            "encontrou": encontrou,
            "ajudou": ajudou,
            "tentativas": tentativas,
            "tempo_segundos": tempo_segundos,
            "nota_facilidade": None,
        }
        self.historico.append(atendimento)
        self.salvar_historico()
        return atendimento

    # ------------------------------------------------------------------
    # Indicadores
    # ------------------------------------------------------------------
    def indicadores(self):
        """Calcula, exibe e devolve os indicadores dos atendimentos."""
        total = len(self.historico)
        if total == 0:
            print("\nAinda não há atendimentos registrados.")
            return None

        encontrados = [a for a in self.historico if a.get("encontrou")]
        ajudados = [a for a in self.historico if a.get("ajudou")]
        pct_encontrou = len(encontrados) / total * 100
        pct_ajudou = len(ajudados) / total * 100

        if encontrados:
            tempo_medio = sum(a.get("tempo_segundos", 0)
                              for a in encontrados) / len(encontrados)
        else:
            tempo_medio = 0.0
        tentativas_medias = sum(a.get("tentativas", 1)
                                for a in self.historico) / total

        # uma nota por sessão (a mesma nota vale para todos os atendimentos dela)
        notas = {}
        for a in self.historico:
            if a.get("nota_facilidade") is not None:
                notas[a.get("sessao")] = a["nota_facilidade"]
        facilidade = sum(notas.values()) / len(notas) if notas else None

        sem_solucao = []
        for a in self.historico:
            if not a.get("ajudou") and a.get("pergunta") not in sem_solucao:
                sem_solucao.append(a.get("pergunta"))

        print("\n=== INDICADORES ===")
        print(f"Atendimentos registrados:    {total}")
        print(f"Resposta encontrada:         {pct_encontrou:.0f}%")
        print(f"Taxa de acerto (ajudou):     {pct_ajudou:.0f}%")
        print(f"Tempo médio p/ encontrar:    {tempo_medio:.1f} s")
        print(f"Tentativas por atendimento:  {tentativas_medias:.1f}")
        if facilidade is None:
            print("Facilidade de uso (1 a 5):   sem notas ainda")
        else:
            print(f"Facilidade de uso (1 a 5):   {facilidade:.1f} "
                  f"({len(notas)} sessões avaliadas)")
        print("Dúvidas sem solução:")
        if sem_solucao:
            for duvida in sem_solucao:
                print(f"  - {duvida}")
        else:
            print("  (nenhuma)")

        return {"total": total, "encontrou_pct": pct_encontrou,
                "ajudou_pct": pct_ajudou, "tempo_medio": tempo_medio,
                "tentativas_medias": tentativas_medias,
                "facilidade": facilidade, "sem_solucao": sem_solucao}

    # ------------------------------------------------------------------
    # Exportação para CSV (data/atendimentos.csv)
    # ------------------------------------------------------------------
    def exportar_csv(self):
        try:
            os.makedirs(os.path.dirname(self.caminho_csv) or ".", exist_ok=True)
            with open(self.caminho_csv, "w", newline="",
                      encoding="utf-8") as arquivo:
                escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_CSV)
                escritor.writeheader()
                for a in self.historico:
                    escritor.writerow({
                        "data": a.get("data", ""),
                        "sessao": a.get("sessao", ""),
                        "origem": a.get("origem", ""),
                        "pergunta": a.get("pergunta", ""),
                        "id_orientacao": a.get("id_orientacao") or "",
                        "encontrou": "sim" if a.get("encontrou") else "nao",
                        "ajudou": "sim" if a.get("ajudou") else "nao",
                        "tentativas": a.get("tentativas", ""),
                        "tempo_segundos": a.get("tempo_segundos", ""),
                        "nota_facilidade": a.get("nota_facilidade") or "",
                    })
            print(f"CSV exportado: {len(self.historico)} atendimento(s) em "
                  f"{self.caminho_csv}")
        except OSError as problema:
            print(f"Aviso: não foi possível exportar o CSV ({problema}).")

    # ------------------------------------------------------------------
    # Saída
    # ------------------------------------------------------------------
    def encerrar(self):
        """Pede a nota de facilidade, mostra indicadores e exporta o CSV."""
        da_sessao = [a for a in self.historico if a.get("sessao") == self.sessao]
        if da_sessao:
            nota = self.ler_opcao(
                "\nAntes de sair: de 1 a 5, quão fácil foi usar o assistente? ",
                5, minimo=1)
            for a in da_sessao:
                a["nota_facilidade"] = nota
            self.salvar_historico()
            self.indicadores()
        self.exportar_csv()
        print("\nObrigado por usar o Citizen Assist AI. Até a próxima!")
