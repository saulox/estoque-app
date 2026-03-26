"""
Gerador de PDF de Nota de Serviço — EstoqueApp
Usa ReportLab com tema marrom/terracota profissional.
"""
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# ─── Paleta de cores ──────────────────────────────────────────────────────────
BROWN_DARK   = colors.HexColor("#2e2010")
BROWN_MID    = colors.HexColor("#6b4c2a")
BROWN_MAIN   = colors.HexColor("#8b5e3c")
BROWN_LIGHT  = colors.HexColor("#c4956a")
BROWN_BRIGHT = colors.HexColor("#e8b48a")
CREAM        = colors.HexColor("#f5e6d3")
CREAM_DARK   = colors.HexColor("#e8d5bc")
ACCENT       = colors.HexColor("#d4894a")
TEXT_DARK    = colors.HexColor("#1a1208")
TEXT_MID     = colors.HexColor("#4a3420")
TEXT_MUTED   = colors.HexColor("#9a7d65")
RED_CANCEL   = colors.HexColor("#c0635a")
WHITE        = colors.white


def fmt_brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def gerar_pdf_nota(nota, empresa) -> bytes:
    """Gera o PDF da nota de serviço e retorna os bytes."""
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=15*mm, bottomMargin=20*mm,
    )
    W = A4[0] - 36*mm  # largura útil

    # ─── Estilos ──────────────────────────────────────────────────────────────
    def sty(name, **kw):
        base = dict(fontName="Helvetica", fontSize=9, textColor=TEXT_DARK,
                    leading=13, spaceAfter=0, spaceBefore=0)
        base.update(kw)
        return ParagraphStyle(name, **base)

    s_title      = sty("title",  fontName="Helvetica-Bold", fontSize=20, textColor=BROWN_DARK, leading=24)
    s_subtitle   = sty("sub",    fontName="Helvetica",      fontSize=9,  textColor=BROWN_MID)
    s_label      = sty("label",  fontName="Helvetica-Bold", fontSize=7,  textColor=TEXT_MUTED,
                        leading=10, spaceAfter=1)
    s_value      = sty("value",  fontName="Helvetica",      fontSize=9,  textColor=TEXT_DARK, leading=12)
    s_value_bold = sty("vbold",  fontName="Helvetica-Bold", fontSize=9,  textColor=TEXT_DARK, leading=12)
    s_center     = sty("center", alignment=TA_CENTER)
    s_right      = sty("right",  alignment=TA_RIGHT)
    s_small      = sty("small",  fontSize=7.5, textColor=TEXT_MUTED, leading=11)
    s_footer     = sty("footer", fontSize=7,   textColor=TEXT_MUTED, alignment=TA_CENTER, leading=10)
    s_cancel     = sty("cancel", fontName="Helvetica-Bold", fontSize=28,
                        textColor=colors.HexColor("#c0635a44"), alignment=TA_CENTER)

    story = []

    # ─── Cabeçalho ────────────────────────────────────────────────────────────
    status_txt = ""
    status_cor = BROWN_MID
    if str(nota.status.value) == "emitida":
        status_txt = "EMITIDA"
        status_cor = colors.HexColor("#3a7a3a")
    elif str(nota.status.value) == "cancelada":
        status_txt = "CANCELADA"
        status_cor = RED_CANCEL
    else:
        status_txt = "RASCUNHO"
        status_cor = BROWN_MID

    header_data = [[
        [
            Paragraph(empresa.razao_social or "Empresa", s_title),
            Paragraph(empresa.nome_fantasia or "", s_subtitle),
            Spacer(1, 3),
            Paragraph(empresa.endereco or "", s_small),
            Paragraph(f"Tel: {empresa.telefone or ''}   |   {empresa.email or ''}", s_small),
            Paragraph(f"CNPJ: {empresa.cnpj or ''}   |   Insc. Mun.: {empresa.inscricao_mun or ''}", s_small),
        ],
        [
            Paragraph("NOTA DE SERVIÇO", ParagraphStyle("ns", fontName="Helvetica-Bold",
                fontSize=11, textColor=WHITE, alignment=TA_CENTER, leading=14)),
            Paragraph(f"Nº {nota.numero_formatado}", ParagraphStyle("nn", fontName="Helvetica-Bold",
                fontSize=18, textColor=WHITE, alignment=TA_CENTER, leading=22)),
            Paragraph(status_txt, ParagraphStyle("st", fontName="Helvetica-Bold",
                fontSize=9, textColor=WHITE, alignment=TA_CENTER, leading=12)),
            Paragraph(nota.data_emissao.strftime("%d/%m/%Y"), ParagraphStyle("dt", fontName="Helvetica",
                fontSize=8, textColor=colors.HexColor("#f5e6d3"), alignment=TA_CENTER, leading=11)),
        ],
    ]]
    header_table = Table(header_data, colWidths=[W * 0.62, W * 0.38])
    header_table.setStyle(TableStyle([
        ("BACKGROUND",    (1, 0), (1, 0), BROWN_DARK),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (0, 0), 0),
        ("RIGHTPADDING",  (0, 0), (0, 0), 8),
        ("LEFTPADDING",   (1, 0), (1, 0), 8),
        ("RIGHTPADDING",  (1, 0), (1, 0), 8),
        ("TOPPADDING",    (1, 0), (1, 0), 10),
        ("BOTTOMPADDING", (1, 0), (1, 0), 10),
        ("ROUNDEDCORNERS", [0, 0, 6, 6]),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 6*mm))

    # ─── Dados do cliente ─────────────────────────────────────────────────────
    cli = nota.cliente
    cli_data = [[
        [Paragraph("TOMADOR DOS SERVIÇOS", s_label),
         Paragraph(cli.nome, s_value_bold)],
        [Paragraph("CPF / CNPJ", s_label),
         Paragraph(cli.cpf_cnpj or "—", s_value)],
        [Paragraph("E-MAIL", s_label),
         Paragraph(cli.email or "—", s_value)],
        [Paragraph("TELEFONE", s_label),
         Paragraph(cli.telefone or "—", s_value)],
    ]]
    cw = [W * 0.40, W * 0.20, W * 0.25, W * 0.15]
    cli_row = [[
        Table([[
            [Paragraph("TOMADOR DOS SERVIÇOS", s_label),
             Paragraph(cli.nome, s_value_bold),
             Paragraph(cli.endereco or "", s_small)],
            [Paragraph("CPF / CNPJ", s_label),
             Paragraph(cli.cpf_cnpj or "—", s_value)],
        ]], colWidths=[W * 0.45]),
        Table([[
            [Paragraph("E-MAIL", s_label), Paragraph(cli.email or "—", s_value)],
            [Paragraph("TELEFONE", s_label), Paragraph(cli.telefone or "—", s_value)],
        ]], colWidths=[W * 0.30]),
        Table([[
            [Paragraph("CONDIÇÃO DE PAGAMENTO", s_label),
             Paragraph(nota.condicao_pagamento, s_value_bold)],
        ]], colWidths=[W * 0.25]),
    ]]
    cli_table = Table([[
        Table([[[
            Paragraph("TOMADOR DOS SERVIÇOS", s_label),
            Paragraph(cli.nome, s_value_bold),
            Paragraph(cli.endereco or "", s_small),
        ]]], colWidths=[W*0.45]),
        Table([[[
            Paragraph("CPF / CNPJ", s_label), Paragraph(cli.cpf_cnpj or "—", s_value),
            Spacer(1,3),
            Paragraph("E-MAIL", s_label), Paragraph(cli.email or "—", s_value),
        ]]], colWidths=[W*0.28]),
        Table([[[
            Paragraph("TELEFONE", s_label), Paragraph(cli.telefone or "—", s_value),
            Spacer(1,3),
            Paragraph("CONDIÇÃO DE PAGAMENTO", s_label),
            Paragraph(nota.condicao_pagamento, s_value_bold),
        ]]], colWidths=[W*0.27]),
    ]], colWidths=[W*0.45, W*0.28, W*0.27])
    cli_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), CREAM),
        ("BOX",           (0,0), (-1,-1), 0.5, BROWN_LIGHT),
        ("LINEAFTER",     (0,0), (1,-1),  0.3, BROWN_LIGHT),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("RIGHTPADDING",  (0,0), (-1,-1), 8),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
    ]))
    story.append(cli_table)
    story.append(Spacer(1, 5*mm))

    # ─── Descrição Geral ──────────────────────────────────────────────────────
    if nota.descricao_geral:
        desc_table = Table([[
            [Paragraph("DESCRIÇÃO DOS SERVIÇOS", s_label),
             Paragraph(nota.descricao_geral, s_value)]
        ]], colWidths=[W])
        desc_table.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), colors.HexColor("#f0e0cc")),
            ("BOX",           (0,0), (-1,-1), 0.5, BROWN_LIGHT),
            ("TOPPADDING",    (0,0), (-1,-1), 7),
            ("BOTTOMPADDING", (0,0), (-1,-1), 7),
            ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ]))
        story.append(desc_table)
        story.append(Spacer(1, 4*mm))

    # ─── Tabela de Itens ──────────────────────────────────────────────────────
    header_row = [
        Paragraph("ITEM", ParagraphStyle("ih", fontName="Helvetica-Bold", fontSize=8,
                  textColor=WHITE, alignment=TA_CENTER)),
        Paragraph("DESCRIÇÃO DO SERVIÇO", ParagraphStyle("dh", fontName="Helvetica-Bold",
                  fontSize=8, textColor=WHITE)),
        Paragraph("QTD", ParagraphStyle("qh", fontName="Helvetica-Bold", fontSize=8,
                  textColor=WHITE, alignment=TA_CENTER)),
        Paragraph("UN", ParagraphStyle("uh", fontName="Helvetica-Bold", fontSize=8,
                  textColor=WHITE, alignment=TA_CENTER)),
        Paragraph("VALOR UNIT.", ParagraphStyle("vh", fontName="Helvetica-Bold", fontSize=8,
                  textColor=WHITE, alignment=TA_RIGHT)),
        Paragraph("TOTAL", ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=8,
                  textColor=WHITE, alignment=TA_RIGHT)),
    ]
    cw_items = [10*mm, W - 10*mm - 15*mm - 12*mm - 28*mm - 28*mm, 15*mm, 12*mm, 28*mm, 28*mm]

    rows = [header_row]
    for i, item in enumerate(nota.itens):
        bg = CREAM if i % 2 == 0 else colors.HexColor("#f8ede0")
        rows.append([
            Paragraph(str(i + 1), ParagraphStyle("in", fontSize=8, alignment=TA_CENTER)),
            Paragraph(item.descricao, ParagraphStyle("dn", fontSize=8.5)),
            Paragraph(f"{item.quantidade:g}", ParagraphStyle("qn", fontSize=8, alignment=TA_CENTER)),
            Paragraph(item.unidade, ParagraphStyle("un_", fontSize=8, alignment=TA_CENTER)),
            Paragraph(fmt_brl(item.valor_unit), ParagraphStyle("vn", fontSize=8, alignment=TA_RIGHT)),
            Paragraph(fmt_brl(item.valor_total), ParagraphStyle("tn", fontName="Helvetica-Bold",
                      fontSize=8, alignment=TA_RIGHT)),
        ])

    items_table = Table(rows, colWidths=cw_items, repeatRows=1)
    ts = TableStyle([
        # Cabeçalho
        ("BACKGROUND",    (0, 0), (-1, 0), BROWN_DARK),
        ("TOPPADDING",    (0, 0), (-1, 0), 7),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
        ("LEFTPADDING",   (0, 0), (-1, 0), 5),
        ("RIGHTPADDING",  (0, 0), (-1, 0), 5),
        # Linhas de dados
        ("TOPPADDING",    (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        ("LEFTPADDING",   (0, 1), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 1), (-1, -1), 5),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("BOX",           (0, 0), (-1, -1), 0.5, BROWN_LIGHT),
        ("LINEBELOW",     (0, 0), (-1, -2), 0.3, BROWN_LIGHT),
    ])
    for i in range(1, len(rows)):
        bg = CREAM if i % 2 == 1 else colors.HexColor("#f0e0cc")
        ts.add("BACKGROUND", (0, i), (-1, i), bg)
    items_table.setStyle(ts)
    story.append(items_table)
    story.append(Spacer(1, 4*mm))

    # ─── Totais ───────────────────────────────────────────────────────────────
    totais_data = [
        ["", "Subtotal", fmt_brl(nota.subtotal)],
        ["", f"ISS ({nota.aliquota_iss:.1f}%) — retido na fonte", f"- {fmt_brl(nota.valor_iss)}"],
        ["", "TOTAL LÍQUIDO", fmt_brl(nota.valor_total)],
    ]
    totais_table = Table(totais_data, colWidths=[W * 0.55, W * 0.27, W * 0.18])
    totais_table.setStyle(TableStyle([
        ("ALIGN",         (1, 0), (-1, -1), "RIGHT"),
        ("FONTNAME",      (1, 0), (-1, 1),  "Helvetica"),
        ("FONTNAME",      (0, 2), (-1, 2),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("FONTSIZE",      (1, 2), (-1, 2),  11),
        ("TEXTCOLOR",     (1, 1), (-1, 1),  RED_CANCEL),
        ("TEXTCOLOR",     (1, 2), (-1, 2),  BROWN_DARK),
        ("BACKGROUND",    (1, 2), (-1, 2),  CREAM),
        ("LINEABOVE",     (1, 2), (-1, 2),  1.0, BROWN_MID),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (2, 0), (2, -1),  8),
    ]))
    story.append(totais_table)
    story.append(Spacer(1, 5*mm))

    # ─── Impostos / Regime ────────────────────────────────────────────────────
    imp_data = [[
        [Paragraph("REGIME TRIBUTÁRIO", s_label),
         Paragraph(empresa.regime_tributario, s_value)],
        [Paragraph("ALÍQUOTA ISS", s_label),
         Paragraph(f"{nota.aliquota_iss:.1f}%", s_value)],
        [Paragraph("VALOR ISS RETIDO", s_label),
         Paragraph(fmt_brl(nota.valor_iss), s_value_bold)],
        [Paragraph("TOTAL A RECEBER", s_label),
         Paragraph(fmt_brl(nota.valor_total), ParagraphStyle("tr", fontName="Helvetica-Bold",
                   fontSize=11, textColor=BROWN_DARK))],
    ]]
    imp_table = Table([[
        Table([[[Paragraph("REGIME TRIBUTÁRIO", s_label), Paragraph(empresa.regime_tributario, s_value)]]],
              colWidths=[W*0.25]),
        Table([[[Paragraph("ALÍQUOTA ISS", s_label), Paragraph(f"{nota.aliquota_iss:.1f}%", s_value)]]],
              colWidths=[W*0.18]),
        Table([[[Paragraph("ISS RETIDO", s_label), Paragraph(fmt_brl(nota.valor_iss), s_value_bold)]]],
              colWidths=[W*0.22]),
        Table([[[Paragraph("TOTAL A RECEBER", s_label),
                 Paragraph(fmt_brl(nota.valor_total),
                           ParagraphStyle("tr2", fontName="Helvetica-Bold", fontSize=12, textColor=BROWN_DARK))]]],
              colWidths=[W*0.35]),
    ]], colWidths=[W*0.25, W*0.18, W*0.22, W*0.35])
    imp_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (2,0), colors.HexColor("#f0e0cc")),
        ("BACKGROUND",    (3,0), (3,0), CREAM),
        ("BOX",           (0,0), (-1,-1), 0.5, BROWN_LIGHT),
        ("LINEAFTER",     (0,0), (2,0),  0.3, BROWN_LIGHT),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(imp_table)
    story.append(Spacer(1, 5*mm))

    # ─── Observações ──────────────────────────────────────────────────────────
    obs_text = nota.observacoes or empresa.observacao_padrao or ""
    if obs_text:
        obs_table = Table([[
            [Paragraph("OBSERVAÇÕES", s_label), Paragraph(obs_text, s_small)]
        ]], colWidths=[W])
        obs_table.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), colors.HexColor("#f8ede0")),
            ("BOX",           (0,0), (-1,-1), 0.5, BROWN_LIGHT),
            ("TOPPADDING",    (0,0), (-1,-1), 7),
            ("BOTTOMPADDING", (0,0), (-1,-1), 7),
            ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ]))
        story.append(obs_table)
        story.append(Spacer(1, 4*mm))

    # ─── Assinatura ───────────────────────────────────────────────────────────
    story.append(HRFlowable(width=W, thickness=0.5, color=BROWN_LIGHT))
    story.append(Spacer(1, 10*mm))
    ass_table = Table([[
        Table([[
            Paragraph("_" * 45, s_center),
            Paragraph(empresa.razao_social or "Prestador de Serviços", ParagraphStyle(
                "as1", fontName="Helvetica-Bold", fontSize=8, alignment=TA_CENTER, textColor=TEXT_MID)),
            Paragraph("Prestador de Serviços", ParagraphStyle(
                "as2", fontSize=7, alignment=TA_CENTER, textColor=TEXT_MUTED)),
        ]], colWidths=[W*0.45]),
        Table([[
            Paragraph("_" * 45, s_center),
            Paragraph(cli.nome, ParagraphStyle(
                "at1", fontName="Helvetica-Bold", fontSize=8, alignment=TA_CENTER, textColor=TEXT_MID)),
            Paragraph("Tomador de Serviços", ParagraphStyle(
                "at2", fontSize=7, alignment=TA_CENTER, textColor=TEXT_MUTED)),
        ]], colWidths=[W*0.45]),
    ]], colWidths=[W*0.5, W*0.5])
    ass_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "BOTTOM"),
        ("ALIGN",  (0,0), (-1,-1), "CENTER"),
    ]))
    story.append(ass_table)
    story.append(Spacer(1, 6*mm))

    # ─── Rodapé ───────────────────────────────────────────────────────────────
    story.append(HRFlowable(width=W, thickness=0.3, color=BROWN_LIGHT))
    story.append(Spacer(1, 2*mm))
    rodape = (
        f"Este documento é uma nota de serviço interna. "
        f"Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}   |   "
        f"EstoqueApp v1.0   |   "
        f"Para validade fiscal, consulte a NFS-e emitida na prefeitura."
    )
    story.append(Paragraph(rodape, s_footer))

    # ─── Marca d'água cancelada ───────────────────────────────────────────────
    if str(nota.status.value) == "cancelada":
        story.insert(0, Paragraph("CANCELADA", s_cancel))

    doc.build(story)
    return buf.getvalue()
