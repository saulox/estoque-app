"""Gerador de PDF para Pedidos de Compra."""
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

BROWN_DARK  = colors.HexColor("#2e2010")
BROWN_MID   = colors.HexColor("#6b4c2a")
ACCENT      = colors.HexColor("#d4894a")
CREAM       = colors.HexColor("#f5e6d3")
CREAM2      = colors.HexColor("#f0e0cc")
TEXT_DARK   = colors.HexColor("#1a1208")
TEXT_MUTED  = colors.HexColor("#9a7d65")

def fmt_brl(v):
    return f"R$ {v:,.2f}".replace(",","X").replace(".",",").replace("X",".")

def gerar_pdf_pedido(pedido) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                             leftMargin=18*mm, rightMargin=18*mm,
                             topMargin=15*mm, bottomMargin=20*mm)
    W = A4[0] - 36*mm

    def sty(name, **kw):
        base = dict(fontName="Helvetica", fontSize=9, textColor=TEXT_DARK, leading=13)
        base.update(kw); return ParagraphStyle(name, **base)

    s_title = sty("t", fontName="Helvetica-Bold", fontSize=18, textColor=BROWN_DARK)
    s_sub   = sty("s", fontSize=9, textColor=BROWN_MID)
    s_label = sty("l", fontName="Helvetica-Bold", fontSize=7, textColor=TEXT_MUTED, leading=10)
    s_val   = sty("v", fontSize=9)
    s_vb    = sty("vb", fontName="Helvetica-Bold", fontSize=9)
    s_small = sty("sm", fontSize=7.5, textColor=TEXT_MUTED)
    s_foot  = sty("f",  fontSize=7,   textColor=TEXT_MUTED,
                  alignment=1)  # CENTER

    story = []
    forn  = pedido.fornecedor

    # Cabeçalho
    hdr = Table([[
        [Paragraph("PEDIDO DE COMPRA", s_title),
         Paragraph(f"Nº {pedido.numero_formatado}", sty("nf", fontName="Helvetica-Bold", fontSize=13, textColor=BROWN_MID)),
         Spacer(1,2),
         Paragraph(pedido.criado_em.strftime("%d/%m/%Y"), s_sub)],
        [Paragraph("STATUS", s_label),
         Paragraph(pedido.status.value.upper(),
                   sty("st", fontName="Helvetica-Bold", fontSize=14, textColor=ACCENT))],
    ]], colWidths=[W*0.65, W*0.35])
    hdr.setStyle(TableStyle([
        ("BACKGROUND",    (1,0),(1,0), BROWN_DARK),
        ("VALIGN",        (0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",    (1,0),(1,0), 12),("BOTTOMPADDING",(1,0),(1,0),12),
        ("LEFTPADDING",   (1,0),(1,0), 16),("RIGHTPADDING",(0,0),(0,0),8),
    ]))
    story += [hdr, Spacer(1,5*mm)]

    # Fornecedor
    forn_t = Table([[
        Table([[[Paragraph("FORNECEDOR", s_label),
                 Paragraph(forn.nome, s_vb),
                 Paragraph(forn.endereco or "", s_small)]]],
              colWidths=[W*0.45]),
        Table([[[Paragraph("CNPJ", s_label), Paragraph(forn.cnpj or "—", s_val),
                 Spacer(1,2),
                 Paragraph("CONTATO", s_label), Paragraph(forn.telefone or forn.email or "—", s_val)]]],
              colWidths=[W*0.3]),
        Table([[[Paragraph("OBSERVAÇÃO", s_label),
                 Paragraph(pedido.observacao or "—", s_val)]]],
              colWidths=[W*0.25]),
    ]], colWidths=[W*0.45, W*0.3, W*0.25])
    forn_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), CREAM),
        ("BOX",           (0,0),(-1,-1), 0.5, BROWN_MID),
        ("LINEAFTER",     (0,0),(1,0),   0.3, BROWN_MID),
        ("TOPPADDING",    (0,0),(-1,-1), 8),("BOTTOMPADDING",(0,0),(-1,-1),8),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),("VALIGN",(0,0),(-1,-1),"TOP"),
    ]))
    story += [forn_t, Spacer(1,5*mm)]

    # Itens
    header_row = [
        Paragraph(t, sty(f"h{i}", fontName="Helvetica-Bold", fontSize=8,
                          textColor=colors.white, alignment=a))
        for i,(t,a) in enumerate([
            ("ITEM",1),("DESCRIÇÃO",0),("PRODUTO VINCULADO",0),
            ("QTD",1),("UN",1),("VALOR UNIT.",2),("TOTAL",2)
        ])
    ]
    cw = [9*mm, W-9*mm-40*mm-14*mm-12*mm-26*mm-26*mm, 40*mm, 14*mm, 12*mm, 26*mm, 26*mm]
    rows = [header_row]
    for i, it in enumerate(pedido.itens):
        pnome = it.produto.nome if it.produto else "—"
        rows.append([
            Paragraph(str(i+1), sty(f"n{i}", fontSize=8, alignment=1)),
            Paragraph(it.descricao, sty(f"d{i}", fontSize=8.5)),
            Paragraph(pnome, sty(f"p{i}", fontSize=8, textColor=TEXT_MUTED)),
            Paragraph(f"{it.quantidade:g}", sty(f"q{i}", fontSize=8, alignment=1)),
            Paragraph(it.unidade, sty(f"u{i}", fontSize=8, alignment=1)),
            Paragraph(fmt_brl(it.preco_unit), sty(f"v{i}", fontSize=8, alignment=2)),
            Paragraph(fmt_brl(it.total), sty(f"t{i}", fontName="Helvetica-Bold", fontSize=8, alignment=2)),
        ])
    it_t = Table(rows, colWidths=cw, repeatRows=1)
    ts   = TableStyle([
        ("BACKGROUND",    (0,0),(-1,0), BROWN_DARK),
        ("TOPPADDING",    (0,0),(-1,0), 7),("BOTTOMPADDING",(0,0),(-1,0),7),
        ("TOPPADDING",    (0,1),(-1,-1),5),("BOTTOMPADDING",(0,1),(-1,-1),5),
        ("LEFTPADDING",   (0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),
        ("VALIGN",        (0,0),(-1,-1),"MIDDLE"),
        ("BOX",           (0,0),(-1,-1),0.5, BROWN_MID),
        ("LINEBELOW",     (0,0),(-1,-2),0.3, BROWN_MID),
    ])
    for i in range(1, len(rows)):
        ts.add("BACKGROUND",(0,i),(-1,i), CREAM if i%2==1 else CREAM2)
    it_t.setStyle(ts); story += [it_t, Spacer(1,4*mm)]

    # Total
    tot_t = Table([["", "TOTAL DO PEDIDO", fmt_brl(pedido.total)]],
                  colWidths=[W*0.55, W*0.27, W*0.18])
    tot_t.setStyle(TableStyle([
        ("ALIGN",         (1,0),(-1,-1),"RIGHT"),
        ("FONTNAME",      (1,0),(-1,-1),"Helvetica-Bold"),
        ("FONTSIZE",      (1,0),(-1,-1),11),
        ("TEXTCOLOR",     (1,0),(-1,-1), BROWN_DARK),
        ("BACKGROUND",    (1,0),(-1,-1), CREAM),
        ("LINEABOVE",     (1,0),(-1,-1),1.0, BROWN_MID),
        ("TOPPADDING",    (0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("RIGHTPADDING",  (2,0),(2,-1), 8),
    ]))
    story += [tot_t, Spacer(1,8*mm)]

    story += [HRFlowable(width=W, thickness=0.3, color=BROWN_MID), Spacer(1,2*mm),
              Paragraph(f"Pedido gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} · EstoqueApp v1.0",
                        s_foot)]
    doc.build(story)
    return buf.getvalue()
