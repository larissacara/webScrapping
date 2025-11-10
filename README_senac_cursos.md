# senac_cursos.py — Coletor de cursos (API Senac SP)

Este script consulta o serviço público do site do Senac SP e salva um JSON consolidado com os principais campos de cada curso. Ele já faz correção básica de textos com encoding incorreto (mojibake) e produz um arquivo pronto para indexação/uso em RAG.

## Pré-requisitos

- Python 3.8+
- Biblioteca `requests` instalada

Instalação rápida:
```bash
pip install requests
```

## Como funciona

- Endpoint consultado (com paginação alta):
  - `https://www.sp.senac.br/o/senac-content-services/cursosPorCategoriasComFiltrosBolsaECompra/20125/0/0/0/0/100?categoryIds={CATEGORY_ID}`
- O `CATEGORY_ID` define o catálogo:
  - 40488 = Graduação
  - 40495 = Pós-graduação (padrão atual do script)
- Campos salvos por curso (lista `CAMPOS` no script):
  - `articleId`, `toDisplay`, `formatoName`, `modalidadeSecundariaDuracao`, `botaoInscricoesAbertas`,
    `oqueVouAprender`, `comoVouAprender`, `possoFazerEsseCurso`, `title`, `url`, `objetivoComercial`
- O arquivo final é salvo em `senac/cursos_filtrados.json` (UTF-8, com indentação).

## Uso

Dentro da pasta `senac/`:
```bash
python senac_cursos.py
```
Saída esperada:
```
OK! Salvo em: G:\...\senac\cursos_filtrados.json
```

Para coletar Graduação em vez de Pós, edite no topo do arquivo:
```python
# 40488 = graduacao
# 40495 = pos-graduacao
CATEGORY_ID = "40488"  # mude para 40488
```

## Estrutura do JSON de saída

```json
{
  "cursos": [
    {
      "articleId": "102580582",
      "toDisplay": {
        "formatoName": "Presencial",
        "modalidadeSecundariaDuracao": "Pós Graduação (Lato Sensu) - 360 horas",
        "tipoName": "Pós-graduação",
        "title": "Big Data"
      },
      "formatoName": null,
      "modalidadeSecundariaDuracao": null,
      "oqueVouAprender": "<p>…</p>",
      "comoVouAprender": "<p>…</p>",
      "possoFazerEsseCurso": "<p>…</p>",
      "title": "Big Data",
      "url": "/pos-graduacao/pos-em-big-data",
      "objetivoComercial": "<p>…</p>"
    }
  ],
  "total": 123
}
```

Observações:
- Alguns campos aparecem duplicados (ex.: `formatoName` na raiz e dentro de `toDisplay`). O script preserva ambos como recebidos pela API.
- O texto em HTML é mantido; a limpeza/normalização pode ser feita em etapas posteriores (ex.: `json_to_pdf.py` ou `rag_index.py`).

## Tratamento de texto (anti-mojibake)

- A função `deep_fix` tenta reparar strings com encoding trocado (padrão `latin-1` → `utf-8`).
- Se não for necessário, o conteúdo permanece inalterado.

## Integração sugerida

- PDF: usar `json_to_pdf.py` para gerar um PDF “texto puro” com cabeçalho YAML e seções marcadas.
- RAG: usar `rag_index.py`/`rag_cli.py` para criar índice FAISS com metadados por curso e consultar via embeddings.

## Solução de problemas

- Erro de rede/timeout: verifique sua conexão e tente novamente.
- Mudanças na API: se o endpoint/estrutura mudar, ajuste `URL`, `CAMPOS` e/ou o tratamento de resposta.
- Permissões de escrita: certifique-se de ter permissão na pasta `senac/`.

## Licença e uso

Este coletor depende de um serviço público do site do Senac SP e se destina a fins de estudo/integração interna. Respeite os termos de uso e políticas do site.
