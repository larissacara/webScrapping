#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para converter arquivo JSON de cursos do SENAC em PDF
"""

import json
import os
import re
import html
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Preformatted, Indenter
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER

# ============================================================================
# CONFIGURAÇÕES - MODIFIQUE AQUI PARA PERSONALIZAR
# ============================================================================

# Nome base dos arquivos (sem extensão)
FILE_BASE_NAME = "graduacao"

# ============================================================================
# FUNÇÕES
# ============================================================================

def clean_html_text(html_text):
    """Remove HTML e limpa o texto"""
    if not html_text:
        return ""
    
    # Decodifica entidades HTML
    text = html.unescape(html_text)
    
    # Remove tags HTML
    text = re.sub(r'<[^>]+>', '', text)
    
    # Limpa espaços e quebras de linha
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    
    return text.strip()

def ensure_absolute_url(url_value):
    """Retorna URL absoluta quando possível."""
    if not url_value:
        return ""
    url_value = url_value.strip()
    if url_value.startswith('http://') or url_value.startswith('https://'):
        return url_value
    if url_value.startswith('/'):
        return f"https://www.sp.senac.br{url_value}"
    return url_value

def collapse_whitespace(text):
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def split_into_sentences(text):
    if not text:
        return []
    text = re.sub(r"\s*\n\s*", " ", text).strip()
    parts = re.split(r"(?<=[\.!?])\s+", text)
    return [p.strip() for p in parts if p and p.strip()]

def chunk_to_range(text, min_len=80, max_len=140):
    words = text.split()
    chunks = []
    current = []
    for w in words:
        tentative = (" ".join(current + [w])).strip()
        if len(tentative) <= max_len:
            current.append(w)
        else:
            if current:
                chunks.append(" ".join(current))
            current = [w]
    if current:
        chunks.append(" ".join(current))
    merged = []
    i = 0
    while i < len(chunks):
        cur = chunks[i]
        if len(cur) < min_len and i + 1 < len(chunks):
            combo = f"{cur} {chunks[i+1]}"
            if len(combo) <= max_len * 2:
                merged.append(combo)
                i += 2
                continue
        merged.append(cur)
        i += 1
    return merged

def bullets_from_text(text, min_len=80, max_len=140):
    sentences = split_into_sentences(text)
    if not sentences:
        return []
    bullets = []
    for sent in sentences:
        sent = collapse_whitespace(sent)
        if not sent:
            continue
        if len(sent) > max_len:
            for piece in chunk_to_range(sent, min_len=min_len, max_len=max_len):
                bullets.append(f"- {piece}")
        elif len(sent) < min_len and bullets:
            prev = bullets[-1][2:]
            combined = f"{prev} {sent}".strip()
            if len(combined) <= max_len:
                bullets[-1] = f"- {combined}"
            else:
                bullets.append(f"- {sent}")
        else:
            bullets.append(f"- {sent}")
    return bullets

def prepare_field_text(field_name, raw_text):
    if not raw_text:
        return ""
    if field_name == 'oqueVouAprender':
        prepared = format_disciplines(raw_text)
    else:
        prepared = clean_html_text(raw_text)
    prepared = prepared.replace('|', ' ')
    prepared = re.sub(r"\n\s*\n+", "\n", prepared)
    return prepared.strip()

def format_section_block(field_name, raw_text):
    text = prepare_field_text(field_name, raw_text)
    if not text:
        return None
    normalized = collapse_whitespace(text)
    if 400 <= len(normalized) <= 900:
        return normalized
    bullets = bullets_from_text(text, min_len=80, max_len=140)
    if bullets:
        return "\n".join(bullets)
    return normalized[:900]

def chunk_text_range(text, min_chars=400, max_chars=900):
    """Divide texto em blocos entre min_chars e max_chars, preferindo limites de sentença."""
    sentences = split_into_sentences(text)
    chunks = []
    current = []
    current_len = 0
    for sent in sentences:
        s = sent.strip()
        if not s:
            continue
        add_len = len(s) + (1 if current else 0)
        if current and current_len + add_len > max_chars:
            chunks.append(" ".join(current))
            current = [s]
            current_len = len(s)
        else:
            current.append(s)
            current_len += add_len
        # Se ficou muito pequeno, continua juntando; se passou do mínimo e próximo passaria do máximo, corta
    if current:
        if len(" ".join(current)) < min_chars and chunks:
            prev = chunks[-1]
            merged = f"{prev} {' '.join(current)}".strip()
            if len(merged) <= max_chars * 2:
                chunks[-1] = merged
            else:
                chunks.append(" ".join(current))
        else:
            chunks.append(" ".join(current))
    # Ajuste final: garante que nenhum bloco ultrapasse max_chars; se ultrapassar, corta duro
    fixed = []
    for c in chunks:
        if len(c) <= max_chars:
            fixed.append(c)
        else:
            # fallback duro por caracteres
            start = 0
            while start < len(c):
                end = min(len(c), start + max_chars)
                fixed.append(c[start:end].strip())
                start = end
    return [f for f in (x.strip() for x in fixed) if f]

def split_oque_vou_aprender_sections(raw_text):
    """Quebra 'oqueVouAprender' por semestres; se longos, divide em ~400–900 chars,
    repetindo o cabeçalho do semestre em cada bloco."""
    formatted = format_disciplines(raw_text)
    if not formatted:
        return []

    lines = [l.strip() for l in formatted.split("\n")]
    semesters = []
    current = []
    sem_re = re.compile(r"\d+º\s+semestre", re.IGNORECASE)

    # 1) Agrupa por semestre
    for line in lines:
        if not line:
            continue
        if sem_re.match(line):
            if current:
                semesters.append("\n".join(current).strip())
                current = []
            current.append(line)
        else:
            current.append(line)
    if current:
        semesters.append("\n".join(current).strip())

    chunks = []

    # 2) Para cada semestre, repetir o cabeçalho em todos os pedaços
    for block in semesters:
        block_lines = [l for l in block.split("\n") if l.strip()]
        if not block_lines:
            continue

        semestre_header = block_lines[0]              # ex: "4º semestre ..."
        resto_lines = block_lines[1:]

        if not resto_lines:
            # só cabeçalho, sem disciplinas
            header_only = collapse_whitespace(semestre_header)
            if header_only:
                chunks.append(header_only)
            continue

        resto_text = collapse_whitespace(" ".join(resto_lines))
        if not resto_text:
            continue

        # bloco completo (semestre + disciplinas)
        full = collapse_whitespace(f"{semestre_header} {resto_text}")

        if len(full) <= 900:
            # cabe inteiro num chunk só
            chunks.append(full)
        else:
            # é grande demais: quebra o "resto" e cola o cabeçalho em cada subchunk
            for sub in chunk_text_range(resto_text, 400, 900):
                composed = collapse_whitespace(f"{semestre_header} {sub}")
                chunks.append(composed)

    return chunks


def build_yaml_header(curso):
    lines = ["---course"]
    article_id = str(curso.get('articleId') or '').strip()
    title = (curso.get('title') or curso.get('toDisplay', {}).get('title') or '').strip()
    to_display = curso.get('toDisplay', {}) or {}
    formato = (curso.get('formatoName') or to_display.get('formatoName') or '').strip()
    duracao = (curso.get('modalidadeSecundariaDuracao') or to_display.get('modalidadeSecundariaDuracao') or '').strip()
    tipo = (curso.get('tipoName') or to_display.get('tipoName') or '').strip()
    url = ensure_absolute_url(curso.get('url') or '')

    if article_id:
        lines.append(f"articleId: {article_id}")
    if title:
        lines.append(f"nomeCurso: {title}")
    if formato:
        lines.append(f"formatoName: {formato}")
    if duracao:
        lines.append(f"modalidadeSecundariaDuracao: {duracao}")
    if tipo:
        lines.append(f"tipoName: {tipo}")
    if url:
        lines.append(f"url: {url}")
    lines.append("---")
    return "\n".join(lines)

def format_disciplines(text):
    """Formata as disciplinas com hierarquia visual: semestres, disciplinas e descrições"""
    if not text:
        return ""
    
    # Limpa o HTML
    text = clean_html_text(text)
    
    # Quebra em linhas
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Remove separadores
        if line == '|' or line == '||':
            continue
            
        # Identifica semestres (1º semestre, 2º semestre, etc.)
        if re.match(r'\d+º\s+semestre', line, re.IGNORECASE):
            formatted_lines.append(f'\n{line}')
            
        # Se a linha começa com letra maiúscula e não é uma descrição, é título da disciplina
        elif (re.match(r'^[A-Z][^:]*:', line) and 
              len(line) > 5 and 
              not re.match(r'\d+º\s+semestre', line, re.IGNORECASE) and
              not line.startswith('Você ') and
              not line.startswith('Esta disciplina') and
              not line.startswith('Aqui, você') and
              not line.startswith('Um dos diferenciais') and
              not line.startswith('Disciplinas')):
            # Título da disciplina
            formatted_lines.append(f'\n{line}')
            
        # Também captura linhas que começam com letra maiúscula sem dois pontos (títulos simples)
        elif (re.match(r'^[A-Z][^:]+$', line) and 
              len(line) > 5 and 
              not re.match(r'\d+º\s+semestre', line, re.IGNORECASE) and
              not line.startswith('Você ') and
              not line.startswith('Esta disciplina') and
              not line.startswith('Aqui, você') and
              not line.startswith('Um dos diferenciais') and
              not line.startswith('Disciplinas')):
            # Título da disciplina
            formatted_lines.append(f'\n{line}')
        else:
            # Descrição da disciplina
            formatted_lines.append(line)
    
    # Junta as linhas
    result = '\n'.join(formatted_lines)
    
    # Limpa espaços excessivos
    result = re.sub(r'\n\s*\n\s*\n', '\n\n', result)
    
    return result.strip()

def create_pdf(json_file_path, output_pdf_path):
    """Cria o PDF a partir do arquivo JSON em texto puro, um curso por página."""

    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Margens simétricas para centralizar visualmente o conteúdo
    page_width, page_height = A4
    left_margin = right_margin = top_margin = bottom_margin = 72  # 1 inch
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=A4,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin,
    )
    story = []

    styles = getSampleStyleSheet()
    pre_style = styles['Code']
    pre_style.fontSize = 9
    pre_style.leading = 12

    cursos = data.get('cursos', [])

    # Funções auxiliares para quebrar linhas longas (evita corte visual no PDF)
    def _wrap_line(line: str, width: int = 100) -> str:
        if len(line) <= width:
            return line
        words = line.split()
        out_lines = []
        cur = []
        cur_len = 0
        for w in words:
            add_len = len(w) + (1 if cur else 0)
            if cur and cur_len + add_len > width:
                out_lines.append(" ".join(cur))
                cur = [w]
                cur_len = len(w)
            else:
                cur.append(w)
                cur_len += add_len
        if cur:
            out_lines.append(" ".join(cur))
        return "\n".join(out_lines)

    def _wrap_text_by_lines(text: str, width: int = 100) -> str:
        return "\n".join(_wrap_line(l, width) for l in text.splitlines())

    for i, curso in enumerate(cursos, 1):
        page_lines = []
        # Cabeçalho YAML original (mantido para compatibilidade com o RAG)
        page_lines.append(build_yaml_header(curso))

        # Metadados do curso para repetir em cada seção
        article_id = str(curso.get('articleId') or '').strip()
        title = (curso.get('title') or curso.get('toDisplay', {}).get('title') or '').strip()
        to_display = curso.get('toDisplay', {}) or {}
        formato = (curso.get('formatoName') or to_display.get('formatoName') or '').strip()
        duracao = (curso.get('modalidadeSecundariaDuracao') or to_display.get('modalidadeSecundariaDuracao') or '').strip()
        tipo = (curso.get('tipoName') or to_display.get('tipoName') or '').strip()
        url = ensure_absolute_url(curso.get('url') or '')

        def section_header_lines():
            """Linhas de contexto repetidas em cada SECTION."""
            lines = []
            if title:
                lines.append(f"Curso: {title}")
            if tipo:
                lines.append(f"Tipo: {tipo}")
            if formato:
                lines.append(f"Formato: {formato}")
            if duracao:
                lines.append(f"Duração / modalidade: {duracao}")
            if url:
                lines.append(f"URL: {url}")
            if article_id:
                lines.append(f"ID do curso: {article_id}")
            return lines

        # objetivo, metodologia, requisitos seguem regra de 400–900 ou bullets
        for field_name in ('objetivoComercial', 'comoVouAprender', 'possoFazerEsseCurso'):
            raw_value = curso.get(field_name, '')
            content = format_section_block(field_name, raw_value)
            if content:
                page_lines.append(f"<<<SECTION:{field_name}>>>")
                # repete contexto do curso aqui
                page_lines.extend(section_header_lines())
                page_lines.append("")  # linha em branco
                page_lines.append(content)
                page_lines.append("<<<END_SECTION>>>")

        # oqueVouAprender: quebrar por semestre/sub-blocos
        oq_raw = curso.get('oqueVouAprender', '')
        if oq_raw:
            oq_chunks = split_oque_vou_aprender_sections(oq_raw)
            for idx, chunk_text in enumerate(oq_chunks, start=1):
                page_lines.append(f"<<<SECTION:oqueVouAprender:{idx}>>>")
                # repete contexto do curso aqui também
                page_lines.extend(section_header_lines())
                page_lines.append("")  # linha em branco
                page_lines.append(chunk_text)
                page_lines.append("<<<END_SECTION>>>")

        page_lines.append("=== END_COURSE ===")

        full_text = "\n".join(page_lines).strip() + "\n"
        full_text_wrapped = _wrap_text_by_lines(full_text, width=100)
        # Centraliza horizontalmente reduzindo a largura útil e usando Indenter
        frame_width = doc.width
        col_width = max(360, int(frame_width * 0.85))
        indent_left = (frame_width - col_width) / 2.0

        # Ajusta a largura de wrap de acordo com a largura da "coluna" e tamanho da fonte monoespaçada
        approx_char_width = pre_style.fontSize * 0.6
        wrap_cols = max(60, min(120, int(col_width / max(approx_char_width, 1))))
        full_text_wrapped = _wrap_text_by_lines(full_text, width=wrap_cols)

        story.append(Indenter(indent_left, 0))
        story.append(Preformatted(full_text_wrapped, pre_style))
        story.append(Indenter(-indent_left, 0))
        if i < len(cursos):
            story.append(PageBreak())


    doc.build(story)
    print(f"PDF criado com sucesso: {output_pdf_path}")

def main():
    """Função principal"""
    # Caminhos base
    script_dir = os.path.dirname(os.path.abspath(__file__))
    requested_json = f"{FILE_BASE_NAME}.json"
    output_pdf = os.path.join(script_dir, f"{FILE_BASE_NAME}.pdf")
    
    # Resolve arquivo JSON com fallback
    candidates = [
        requested_json,
        "cursos_filtrados.json",
        "graduacao.json",
        "pos_graduacao.json",
    ]
    json_file = None
    for name in candidates:
        candidate_path = os.path.join(script_dir, name)
        if os.path.exists(candidate_path):
            json_file = candidate_path
            break
    
    # Verifica se conseguiu resolver o arquivo JSON
    if not json_file:
        print(f"Erro: Arquivo {requested_json} não encontrado!")
        print("Certifique-se de que o arquivo está no mesmo diretório deste script.")
        return
    
    try:
        create_pdf(json_file, output_pdf)
        print("\nConversão concluída.")
        print(f"Arquivo PDF criado: {output_pdf}")
        print(f"Total de cursos processados: {len(json.load(open(json_file, 'r', encoding='utf-8'))['cursos'])}")
        print("Saída em texto puro, um curso por página, conforme especificação.")
        
    except Exception as e:
        # Se o arquivo estiver aberto/bloqueado, tenta salvar com outro nome
        msg = str(e)
        if isinstance(e, PermissionError) or 'Permission denied' in msg or 'Permissão negada' in msg:
            alt_output = output_pdf[:-4] + "_wrapped.pdf"
            try:
                create_pdf(json_file, alt_output)
                print("\nConversão concluída (arquivo original bloqueado).")
                print(f"Arquivo PDF criado: {alt_output}")
                print(f"Total de cursos processados: {len(json.load(open(json_file, 'r', encoding='utf-8'))['cursos'])}")
                print("Saída em texto puro, um curso por página, conforme especificação.")
                return
            except Exception as e2:
                print(f"Erro durante a conversão (fallback): {e2}")
        print(f"Erro durante a conversão: {msg}")
        print("Verifique se o arquivo JSON está no formato correto e feche o PDF se estiver aberto.")

if __name__ == "__main__":
    main()
