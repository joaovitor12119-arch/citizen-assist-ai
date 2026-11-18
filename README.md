# Citizen Assist AI

Assistente de terminal, em Python, que orienta **jovens no primeiro emprego** com informações
verificadas, mostrando fonte, data de verificação e avisos, sem coletar dados pessoais.

GS2026.2 - Pensamento Computacional e Automação com Python (desafio CitizenTech).

## Integrantes

| Nome | RM |
|---|---|
| Júlia Konishi | 569506 |
| João Vitor Giadans | 571608 |
| João Victor Scheren | 568883 |

## Público e problema

**Público:** jovens que estão arrumando o primeiro emprego.

**Problema:** quem começa a trabalhar precisa de CPF, conta gov.br, Carteira de Trabalho Digital,
título de eleitor, alistamento militar (homens) e precisa entender direitos básicos, FGTS e salário.
A informação existe, mas está espalhada, em linguagem técnica e misturada com sites que parecem
oficiais e não são. O assistente reúne tudo em respostas curtas, em linguagem simples, com a fonte oficial.

## ODS relacionados

- **ODS 8** - Trabalho decente e crescimento econômico (entrada segura no mercado de trabalho).
- **ODS 10** - Redução das desigualdades (informação clara para quem tem menos acesso a orientação).
- **ODS 16** - Paz, justiça e instituições eficazes (acesso à informação e serviços públicos transparentes).

## Como executar

Requisitos: Python 3.8 ou superior. Não usa bibliotecas externas.

```bash
git clone <link-do-repositorio>
cd citizen-assist-ai
python main.py
```

Menu: 1 perguntar em texto livre, 2 navegar por categorias, 3 ver indicadores,
4 exportar CSV, 0 sair (pede a nota de facilidade de 1 a 5).

## Estrutura

```
citizen-assist-ai/
├── README.md
├── main.py               # inicia o programa
├── orientacao.py         # classe Orientacao
├── base_conhecimento.py  # classe BaseConhecimento + normalizar()
├── assistente.py         # classe Assistente
└── data/
    ├── base_conhecimento.json   # 13 orientações, 4 categorias
    ├── historico.json           # atendimentos registrados
    └── atendimentos.csv         # exportação dos atendimentos
```

Composição: `Assistente` tem uma `BaseConhecimento`, que tem uma lista de objetos `Orientacao`.

## Regra de pontuação usada

A pergunta é normalizada (minúsculas, sem acentos e sem pontuação) e comparada com cada orientação:

| Regra | Pontos |
|---|---|
| Cada palavra-chave da orientação que aparece na pergunta | +3 |
| Cada palavra da pergunta (4 letras ou mais) que aparece no título | +1 |

| Melhor pontuação | Resultado |
|---|---|
| 6 ou mais | Confiança **ALTA** |
| 3 a 5 | Confiança **MÉDIA** |
| menos de 3 | "Não encontrei": sugere palavras e as categorias |

`buscar()` devolve uma lista de tuplas `(pontos, orientacao)` da maior para a menor pontuação.
O assistente mostra a melhor orientação e até duas alternativas.

Exemplo: "Como tirar o CPF?" -> palavra-chave `cpf` (+3) e `tirar o cpf` (+3) = **6 pontos, ALTA**.

**Ajuste do grupo:** palavras muito comuns (como, para, fazer, tirar, quero...) não valem ponto no
título, para que perguntas diferentes não ganhem pontos só por usarem verbos parecidos.
Os pesos e limites são os do enunciado.

## Regras de atendimento

- Entradas inválidas (opção fora da faixa, letras, vazio, s/n inválido) não encerram o programa.
- Pergunta com 8 ou mais dígitos ou com `@` é recusada e **não é registrada**.
- Toda resposta mostra fonte, data de verificação e o aviso de que o assistente não é canal oficial.
- JSON da base ausente ou corrompido não trava: o programa avisa e encerra com mensagem.
  Histórico corrompido é guardado como `historico.corrompido.json` e recomeçado.

## Histórico, indicadores e CSV

Cada atendimento é salvo em `data/historico.json` com: data, sessão, origem (pergunta ou categoria),
pergunta, id da orientação, se encontrou, se ajudou, tentativas, tempo em segundos e nota de facilidade.
Um atendimento de pergunta continua até a pessoa ser ajudada ou desistir (0); cada nova tentativa soma 1.

Indicadores: resposta encontrada (%), taxa de acerto (%), tempo médio para encontrar, tentativas por
atendimento, facilidade de uso (média das notas por sessão) e lista de dúvidas sem solução.
Os atendimentos são exportados para `data/atendimentos.csv` com `csv.DictWriter`.

## Integrações com outras disciplinas

Nenhuma integração nesta versão (a busca por pontuação é a parte avaliada em PCP).

## Fontes consultadas

- Receita Federal: https://www.gov.br/receitafederal
- gov.br: https://www.gov.br
- Ministério do Trabalho e Emprego: https://www.gov.br/trabalho-e-emprego
- Caixa (FGTS): https://www.caixa.gov.br/beneficios-trabalhador/fgts/Paginas/default.aspx
- Banco Central (Cidadania Financeira): https://www.bcb.gov.br/cidadaniafinanceira
- Tribunal Superior Eleitoral: https://www.tse.jus.br
- Ministério da Defesa: https://www.gov.br/defesa

Todas as orientações foram conferidas em 2026-11-17 (campo `verificado_em`).

## Teste com usuários

> PREENCHER depois de testar com pelo menos 3 pessoas de fora do grupo (10 atendimentos ou mais).
> Não registrar nomes nem dados dessas pessoas.

| Indicador | Resultado |
|---|---|
| Pessoas testadas | _ |
| Atendimentos | _ |
| Resposta encontrada (%) | _ |
| Taxa de acerto (%) | _ |
| Tempo médio para encontrar (s) | _ |
| Tentativas por atendimento | _ |
| Facilidade de uso (1 a 5) | _ |

**Dúvidas sem solução:** _ (copiar da lista de indicadores)

**Melhoria feita a partir do teste:** _ (ex.: nova palavra-chave incluída para a dúvida "...")

## Limitações

- A busca é por regras: só entende palavras-chave parecidas com as do JSON (não entende sinônimos nem erros de digitação).
- Responde apenas o que está na base (13 orientações); regras e prazos podem mudar, por isso cada resposta traz a fonte e a data de verificação.
- O tempo de atendimento inclui o tempo de leitura e digitação da pessoa.
- Não é canal oficial e não substitui o atendimento dos órgãos públicos.

## Vídeo técnico

Link: _ (colar o link do YouTube não listado)
