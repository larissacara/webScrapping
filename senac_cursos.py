# senac_cursos.py
import json
from pathlib import Path
import requests

# 40488 = graduacao
# 40495 = pos-graduacao
CATEGORY_ID = "40488"

URL = f"https://www.sp.senac.br/o/senac-content-services/cursosPorCategoriasComFiltrosBolsaECompra/20125/0/0/0/0/100?categoryIds={CATEGORY_ID}"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.sp.senac.br/",
}

CAMPOS = [
    "articleId",
    "toDisplay",
    "formatoName",
    "modalidadeSecundariaDuracao",
    "botaoInscricoesAbertas",
    "oqueVouAprender",
    "comoVouAprender",
    "possoFazerEsseCurso",
    "title",
    "url",
    "objetivoComercial",
]

def fix_text(value):
    """Tenta corrigir mojibake (ex.: 'AÃ§Ã£o' -> 'Ação').
    Tenta reinterpretar texto como latin-1 -> utf-8 quando fizer sentido."""
    if not isinstance(value, str):
        return value
    try:
        # Se o texto parece ter sido decodificado errado (UTF-8 como Latin-1),
        # reinterpreta: str(bytes_latin1)->utf8
        repaired = value.encode("latin-1", errors="strict").decode("utf-8", errors="strict")
        # Heurística: se a versão reparada tem mais chars “bonitos”, fica com ela
        return repaired if sum(ch >= "\u0080" for ch in repaired) >= sum(ch >= "\u0080" for ch in value) else value
    except Exception:
        return value

def deep_fix(obj):
    if isinstance(obj, dict):
        return {k: deep_fix(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [deep_fix(x) for x in obj]
    return fix_text(obj)

def main():
    out_path = Path(__file__).parent / "graduacao.json"

    r = requests.get(URL, headers=HEADERS, timeout=30)
    r.raise_for_status()

    # Importante: parsear o JSON diretamente dos bytes como UTF-8
    data = json.loads(r.content.decode("utf-8", errors="strict"))

    # Corrige eventuais strings embaralhadas
    data = deep_fix(data)

    cursos = data.get("cursos", [])
    cursos_filtrados = [{k: (curso.get(k)) for k in CAMPOS} for curso in cursos]

    resultado = {
        "cursos": cursos_filtrados,
        "total": data.get("total", len(cursos_filtrados)),
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=4)

    print(f"OK! Salvo em: {out_path}")

if __name__ == "__main__":
    main()
