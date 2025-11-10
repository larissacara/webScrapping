# json_to_pdf.py — Gerador de PDF em texto puro (pronto para RAG)

Este script converte um arquivo JSON de cursos do Senac no formato de um PDF em texto puro, com metadados estruturados e marcadores de seção, ideal para indexação por embeddings e recuperação via RAG.

## Principais características

- Um curso por página (recomendado para QA humano).
- Cabeçalho YAML entre `---course` e `---` com metadados do curso.
- Seções de conteúdo marcadas com `<<<SECTION:{campo}>>> ... <<<END_SECTION>>>`.
- Quebra específica de `oqueVouAprender` por partes numeradas: `<<<SECTION:oqueVouAprender:1>>>`, `:2`, etc.
- Regras de tamanho:
  - Texto corrido por seção entre ~400 e 900 caracteres; ou
  - Bullets entre ~80 e 140 caracteres (quando o texto for muito longo/desestruturado).
- URLs absolutas sempre que possível (prefixo `https://www.sp.senac.br` quando vierem relativas).
- Encerramento de cada página com `=== END_COURSE ===`.
- Layout centralizado no A4, com quebra automática de linhas (wrap) para evitar corte visual.
- Fallback automático de nome do PDF quando o arquivo original estiver aberto/bloqueado.

## Instalação

Requisitos mínimos:
- Python 3.8+
- ReportLab

Instale as dependências:
```bash
pip install -r requirements.txt
```
Ou diretamente:
```bash
pip install reportlab
```

## Entrada esperada (JSON)

O script lê um arquivo com a chave `cursos` (lista de cursos). Campos utilizados por curso:
- `articleId`
- `title` (ou `toDisplay.title`)
- `url`
- `toDisplay.formatoName`, `toDisplay.modalidadeSecundariaDuracao`, `toDisplay.tipoName`
- `objetivoComercial`, `oqueVouAprender`, `comoVouAprender`, `possoFazerEsseCurso` (HTML permitido)

O arquivo padrão é resolvido automaticamente em ordem de preferência:
1) `{FILE_BASE_NAME}.json`
2) `cursos_filtrados.json`
3) `graduacao.json`
4) `pos_graduacao.json`

Você pode ajustar `FILE_BASE_NAME` no topo do script.

## Saída (PDF em texto puro)

Para cada curso, o PDF contém:
- Cabeçalho YAML:
  ```
  ---course
  articleId: 102580582
  nomeCurso: Big Data
  formatoName: Presencial
  modalidadeSecundariaDuracao: Pós Graduação (Lato Sensu) - 360 horas
  tipoName: Pós-graduação
  url: https://www.sp.senac.br/pos-graduação/pos-em-big-data
  ---
  ```
- Seções marcadas:
  ```
  <<<SECTION:objetivoComercial>>>
  ... texto corrido (400–900) ou bullets (80–140) ...
  <<<END_SECTION>>>

  <<<SECTION:oqueVouAprender:1>>>
  ... parte 1 (preferencialmente por semestre) ...
  <<<END_SECTION>>>
  ```
- Encerramento:
  ```
  === END_COURSE ===
  ```

Observações:
- `oqueVouAprender` é normalizado e quebrado por semestres; blocos extensos são fatiados para ~400–900 caracteres por trecho e numerados sequencialmente (:1, :2, ...).
- URLs relativas em `url` são convertidas para absolutas (`https://www.sp.senac.br/...`).

## Uso

No diretório `senac/`:
```bash
python json_to_pdf.py
```
Saídas típicas:
- `graduacao.pdf` (ou
- `graduacao_wrapped.pdf` quando o arquivo original estiver bloqueado/aberto)

Você pode alterar `FILE_BASE_NAME` no script para mudar os nomes padrão dos arquivos de entrada/saída.

## Layout e quebras de linhas

- O conteúdo é centralizado horizontalmente usando recuo dinâmico (Indenter) com ~85% da largura útil.
- A largura de quebra de linhas é calculada automaticamente a partir do tamanho de fonte monoespaçada, evitando linhas muito longas.
- Se desejar personalizar:
  - Largura da “coluna” central: ajuste o fator `0.85` em `json_to_pdf.py`.
  - Largura do wrap (colunas): ajuste o cálculo do `wrap_cols` no mesmo bloco.

## Integração com RAG

- O PDF gerado é “texto puro” e inclui metadados claros (YAML + marcadores), facilitando chunking e extração de metadados por curso.
- Use `rag_index.py`/`rag_cli.py` para:
  - Construir um índice vetorial FAISS a partir do JSON diretamente (mais recomendado) ou do texto extraído do PDF, se desejado.
  - Consultar por tema/pergunta e recuperar trechos com `articleId`, `nomeCurso`, `campo` (tipo), `field` e `score`.

## Dicas de qualidade

- Prefira indexar diretamente o JSON via `rag_index.py` para preservar metadados e reduzir ruído.
- Use o PDF para auditoria humana e compatibilidade com pipelines que exigem PDF.
- Mantenha as seções entre 400–900 caracteres quando possível; em textos muito longos, o script converte para bullets (80–140) por sentença/tópico.

## Problemas comuns

- “Permission denied” ao salvar PDF: feche o arquivo PDF aberto. O script tenta salvar automaticamente como `*_wrapped.pdf` se detectar bloqueio.
- “Arquivo não encontrado”: verifique o nome base e os candidatos de entrada listados acima.
- Quebras de linhas: o wrap é automático, mas pode ser ajustado conforme instruído em “Layout e quebras de linhas”.

## Licença e uso

Este gerador foi pensado para uso interno e estudos com RAG. Respeite os termos do site do Senac e as políticas de uso de dados.
