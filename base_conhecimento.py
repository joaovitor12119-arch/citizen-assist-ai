"""Classe BaseConhecimento: lê o JSON, lista categorias e busca por pontuação."""
import json

from orientacao import Orientacao

# ---------- Normalização (6.1) ----------
ACENTOS = {"á": "a", "à": "a", "ã": "a", "â": "a", "é": "e", "ê": "e",
           "í": "i", "ó": "o", "õ": "o", "ô": "o", "ú": "u", "ç": "c",
           "º": "o", "ª": "a"}

# Palavras comuns demais para valer ponto no título (decisão técnica do grupo).
PALAVRAS_IGNORADAS = {"como", "para", "pode", "onde", "qual", "quais", "quero",
                      "preciso", "fazer", "tirar", "tenho", "minha", "meus",
                      "minhas", "sobre", "isso", "esse", "essa", "quando"}

# ---------- Regras de pontuação (6.2) ----------
PONTOS_PALAVRA_CHAVE = 3
PONTOS_TITULO = 1
LIMITE_ALTA = 6    # 6 pontos ou mais -> ALTA
LIMITE_MEDIA = 3   # 3 a 5 pontos -> MÉDIA; abaixo disso, "não encontrei"

CAMPOS_OBRIGATORIOS = ["id", "categoria", "titulo", "palavras_chave", "resposta",
                       "documentos", "onde", "fonte", "verificado_em"]


def normalizar(texto):
    """Minúsculas, sem acentos e sem pontuação, com espaço nas pontas."""
    texto = texto.lower().strip()
    for letra, troca in ACENTOS.items():
        texto = texto.replace(letra, troca)
    for sinal in "?!.,;:()":
        texto = texto.replace(sinal, " ")
    return " " + " ".join(texto.split()) + " "


class BaseConhecimento:
    """O conjunto de todas as orientações (lista de objetos Orientacao)."""

    def __init__(self, caminho):
        self.caminho = caminho
        self.orientacoes = []
        self.erro = ""      # motivo da falha, se carregar() devolver False
        self.avisos = []    # registros ignorados por estarem incompletos

    def carregar(self):
        """Lê o JSON e cria os objetos Orientacao. Nunca levanta exceção."""
        self.orientacoes = []
        self.avisos = []
        try:
            with open(self.caminho, "r", encoding="utf-8") as arquivo:
                registros = json.load(arquivo)
        except FileNotFoundError:
            self.erro = f"arquivo não encontrado: {self.caminho}"
            return False
        except json.JSONDecodeError as problema:
            self.erro = f"JSON corrompido ({problema})"
            return False
        except OSError as problema:
            self.erro = f"não foi possível ler o arquivo ({problema})"
            return False

        if not isinstance(registros, list):
            self.erro = "o JSON deve ser uma lista de orientações"
            return False

        for registro in registros:
            orientacao = self._criar_orientacao(registro)
            if orientacao is not None:
                self.orientacoes.append(orientacao)

        if not self.orientacoes:
            self.erro = "nenhuma orientação válida na base"
            return False
        return True

    def _criar_orientacao(self, registro):
        """Valida um dicionário do JSON e devolve uma Orientacao (ou None)."""
        if not isinstance(registro, dict):
            self.avisos.append("registro que não é dicionário foi ignorado")
            return None
        faltando = [c for c in CAMPOS_OBRIGATORIOS if c not in registro]
        if faltando:
            self.avisos.append(f"registro {registro.get('id', '?')} ignorado: "
                               f"faltam {faltando}")
            return None
        if not isinstance(registro["palavras_chave"], list) or \
                not isinstance(registro["documentos"], list):
            self.avisos.append(f"registro {registro['id']} ignorado: "
                               "palavras_chave e documentos devem ser listas")
            return None
        palavras = [p for p in registro["palavras_chave"]
                    if isinstance(p, str) and p.strip()]
        if not palavras:
            self.avisos.append(f"registro {registro['id']} ignorado: "
                               "sem palavras-chave")
            return None
        return Orientacao(registro["id"], registro["categoria"],
                          registro["titulo"], palavras, registro["resposta"],
                          registro["documentos"], registro["onde"],
                          registro["fonte"], registro["verificado_em"])

    def categorias(self):
        """Lista as categorias sem repetir, na ordem em que aparecem."""
        lista = []
        for orientacao in self.orientacoes:
            if orientacao.categoria not in lista:
                lista.append(orientacao.categoria)
        return lista

    def por_categoria(self, categoria):
        """Devolve as orientações de uma categoria."""
        return [o for o in self.orientacoes if o.categoria == categoria]

    def pontuar(self, orientacao, pergunta):
        """Calcula quantos pontos uma orientação ganha para a pergunta."""
        texto = normalizar(pergunta)
        pontos = 0

        # +3 por palavra-chave que aparece na pergunta
        for palavra in orientacao.palavras_chave:
            if normalizar(palavra) in texto:
                pontos += PONTOS_PALAVRA_CHAVE

        # +1 por palavra da pergunta (4+ letras) que aparece no título
        palavras_titulo = normalizar(orientacao.titulo).split()
        ja_contadas = set()
        for palavra in texto.split():
            if (len(palavra) >= 4 and palavra not in PALAVRAS_IGNORADAS
                    and palavra in palavras_titulo
                    and palavra not in ja_contadas):
                pontos += PONTOS_TITULO
                ja_contadas.add(palavra)
        return pontos

    def buscar(self, pergunta):
        """Devolve lista de tuplas (pontos, orientacao), da maior para a menor."""
        resultados = []
        for orientacao in self.orientacoes:
            pontos = self.pontuar(orientacao, pergunta)
            if pontos > 0:
                resultados.append((pontos, orientacao))
        resultados.sort(key=lambda tupla: (-tupla[0], tupla[1].id))
        return resultados

    @staticmethod
    def confianca(pontos):
        """Converte pontos em nível de confiança (ou None se for baixo)."""
        if pontos >= LIMITE_ALTA:
            return "ALTA"
        if pontos >= LIMITE_MEDIA:
            return "MÉDIA"
        return None
