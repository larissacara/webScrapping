import json
from typing import List, Dict


def carregar_cursos(json_path: str) -> List[Dict]:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cursos = data.get("cursos", [])
    docs = []

    for curso in cursos:
        title = (curso.get("title") or "").strip()
        formato = (curso.get("formatoName") or "").strip()
        duracao = (curso.get("modalidadeSecundariaDuracao") or "").strip()
        url = (curso.get("url") or "").strip()
        objetivo = (curso.get("objetivoComercial") or "").strip()
        como = (curso.get("comoVouAprender") or "").strip()
        posso = (curso.get("possoFazerEsseCurso") or "").strip()
        oq = (curso.get("oqueVouAprender") or "").strip()

        # Documento geral do curso
        texto_curso = (
            f"Curso: {title}\n"
            f"Formato: {formato}\n"
            f"Duração/modalidade: {duracao}\n"
            f"URL: {url}\n\n"
            f"Objetivo do curso:\n{objetivo}\n\n"
            f"Como vou aprender:\n{como}\n\n"
            f"Quem pode fazer esse curso:\n{posso}\n\n"
            f"O que vou aprender (visão geral):\n{oq}\n"
        )

        docs.append({
            "id": f"{curso.get('articleId')}_geral",
            "text": texto_curso,
            "metadata": {
                "articleId": curso.get("articleId"),
                "title": title,
                "formatoName": formato,
                "duracao": duracao,
                "url": url,
                "tipo_doc": "curso_geral",
            },
        })

        # Opcional: quebrar o 'oqueVouAprender' em itens menores
        linhas = [linha.strip() for linha in oq.split("\n") if linha.strip()]
        for i, linha in enumerate(linhas, start=1):
            texto_disciplina = (
                f"Curso: {title}\n"
                f"Seção: O que vou aprender\n"
                f"Item {i}:\n{linha}"
            )
            docs.append({
                "id": f"{curso.get('articleId')}_oque_{i}",
                "text": texto_disciplina,
                "metadata": {
                    "articleId": curso.get("articleId"),
                    "title": title,
                    "secao": "oqueVouAprender",
                    "item": i,
                    "url": url,
                    "tipo_doc": "oque_item",
                },
            })

    return docs


if __name__ == "__main__":
    # Ajusta o caminho conforme onde o JSON está
    json_path = "graduacao.json"  # exemplo: se estiver na mesma pasta deste .py

    docs = carregar_cursos(json_path)
    print(f"Total de documentos gerados: {len(docs)}\n")

    # Salvar em um arquivo JSONL (um doc por linha)
    output_path = "cursos_docs.jsonl"
    import json

    with open(output_path, "w", encoding="utf-8") as f:
        for d in docs:
            json.dump(d, f, ensure_ascii=False)
            f.write("\n")

    print(f"Documentos salvos em: {output_path}")
