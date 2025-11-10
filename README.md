# 🎓 Web Scraping - Cursos SENAC SP

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Ferramentas para coletar, processar e indexar cursos do Senac SP usando web scraping, geração de PDF e RAG (Retrieval-Augmented Generation).

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Funcionalidades](#-funcionalidades)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação](#-instalação)
- [Uso Rápido](#-uso-rápido)
- [Documentação Detalhada](#-documentação-detalhada)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Exemplos](#-exemplos)
- [Contribuindo](#-contribuindo)
- [Licença](#-licença)

## 🎯 Visão Geral

Este repositório contém um conjunto de scripts Python para:

1. **Coleta de Dados**: Extração de informações de cursos do Senac SP via API pública
2. **Geração de PDF**: Conversão dos dados coletados em PDF estruturado, ideal para RAG
3. **Indexação RAG**: Criação de índice vetorial usando FAISS e consulta por similaridade semântica

## ✨ Funcionalidades

- ✅ Coleta automática de cursos do Senac SP (Graduação e Pós-graduação)
- ✅ Correção automática de encoding (mojibake)
- ✅ Geração de PDF em texto puro com metadados YAML
- ✅ Indexação vetorial com FAISS e sentence-transformers
- ✅ Consulta semântica por similaridade
- ✅ Chunking inteligente de texto para RAG
- ✅ Metadados estruturados por curso

## 📦 Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

## 🚀 Instalação

1. Clone o repositório:
```bash
git clone https://github.com/larissacara/webScrapping.git
cd webScrapping
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

## 🏃 Uso Rápido

### 1. Coletar cursos do Senac SP

```bash
python senac_cursos.py
```

Isso irá:
- Consultar a API do Senac SP
- Salvar os dados em `graduacao.json`
- Aplicar correções de encoding automaticamente

**Nota**: Para coletar Pós-graduação em vez de Graduação, edite `CATEGORY_ID` no arquivo `senac_cursos.py`:
```python
CATEGORY_ID = "40495"  # Pós-graduação
# CATEGORY_ID = "40488"  # Graduação
```

### 2. Gerar PDF estruturado (opcional)

```bash
python json_to_pdf.py
```

Gera um PDF em texto puro com:
- Metadados YAML por curso
- Seções marcadas para RAG
- Um curso por página

### 3. Construir índice RAG e consultar

```bash
# Construir o índice
python rag_cli.py build --json graduacao.json --out rag_index

# Consultar o índice
python rag_cli.py query "Quero cursos sobre Big Data e NoSQL" --index rag_index --k 5
```

## 📚 Documentação Detalhada

### Componentes do Sistema

#### 1. Coleta de Dados (`senac_cursos.py`)

Script para coletar cursos via API pública do Senac SP.

**Campos coletados:**
- `articleId`, `title`, `url`
- `formatoName`, `modalidadeSecundariaDuracao`
- `oqueVouAprender`, `comoVouAprender`
- `possoFazerEsseCurso`, `objetivoComercial`

📖 [Documentação completa](README_senac_cursos.md)

#### 2. Geração de PDF (`json_to_pdf.py`)

Converte JSON de cursos em PDF estruturado, ideal para RAG.

**Características:**
- Cabeçalho YAML com metadados
- Seções marcadas (`<<<SECTION:...>>>`)
- Chunking inteligente (400-900 caracteres)
- Layout centralizado e quebra automática de linhas

📖 [Documentação completa](README_json_to_pdf.md)

#### 3. Sistema RAG (`rag_index.py` + `rag_cli.py`)

Índice vetorial usando FAISS e consulta por similaridade semântica.

**Recursos:**
- Embeddings com `sentence-transformers`
- Índice FAISS otimizado
- Metadados por snippet (curso, campo, seção)
- Consulta com top-k resultados

## 📁 Estrutura do Projeto

```
webScrapping/
├── senac_cursos.py          # Coletor de cursos via API
├── json_to_pdf.py           # Gerador de PDF estruturado
├── rag_index.py             # Construção e consulta do índice RAG
├── rag_cli.py               # CLI para RAG
├── json_cursos_loader.py    # Utilitário de carregamento de JSON
├── requirements.txt         # Dependências do projeto
├── README.md                # Este arquivo
├── README_senac_cursos.md   # Docs do coletor
├── README_json_to_pdf.md    # Docs do gerador de PDF
└── .gitignore               # Arquivos ignorados pelo Git
```

## 💡 Exemplos

### Exemplo 1: Coleta e Indexação Completa

```bash
# 1. Coletar cursos
python senac_cursos.py

# 2. Construir índice RAG
python rag_cli.py build --json graduacao.json --out rag_index

# 3. Consultar
python rag_cli.py query "cursos de tecnologia" --index rag_index --k 10
```

### Exemplo 2: Usando Modelo Diferente

```bash
python rag_cli.py build \
  --json graduacao.json \
  --out rag_index \
  --model sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

python rag_cli.py query "Big Data" \
  --index rag_index \
  --model sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 \
  --k 5
```

### Exemplo 3: Consulta com Filtro por Campo

```bash
# Construir índice forçando um campo específico
python rag_cli.py build --json graduacao.json --out rag_index --campo "Graduação"

# Consultar
python rag_cli.py query "ciência de dados" --index rag_index --k 5
```

## 🔧 Configuração Avançada

### Modelos de Embedding

O sistema usa por padrão `sentence-transformers/all-MiniLM-L6-v2`. Você pode usar outros modelos:

- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (multilíngue)
- `sentence-transformers/all-mpnet-base-v2` (maior qualidade, mais lento)

### Chunking de Texto

O sistema usa chunking inteligente:
- Tamanho padrão: 400-900 caracteres
- Overlap: 150 caracteres
- Quebra preferencial em limites de sentença

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para:

1. Fazer fork do projeto
2. Criar uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abrir um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## ⚠️ Avisos

- Este projeto utiliza uma API pública do site do Senac SP
- Destina-se a fins educacionais e de estudo
- Respeite os termos de uso e políticas do site do Senac
- Use com responsabilidade e ética

## 📧 Contato

Para dúvidas ou sugestões, abra uma [issue](https://github.com/larissacara/webScrapping/issues) no repositório.

---

⭐ Se este projeto foi útil para você, considere dar uma estrela!
