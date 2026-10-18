"""Geração de recibo em PDF."""
from pathlib import Path
from datetime import datetime
import sys
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

BASE = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
PASTA = BASE / "recibos"
PASTA.mkdir(exist_ok=True)

def gerar_recibo(itens, total, pagamento, venda_id, valor_pago=None, troco=0):
    arquivo = PASTA / f"recibo_{venda_id}_{datetime.now():%Y%m%d_%H%M%S}.pdf"
    pdf = canvas.Canvas(str(arquivo), pagesize=A4)
    largura, altura = A4
    y = altura - 55
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(45, y, "SUPERMERCADO - RECIBO")
    y -= 28
    pdf.setFont("Helvetica", 10)
    pdf.drawString(45, y, f"Venda: {venda_id}   Data: {datetime.now():%d/%m/%Y %H:%M}")
    y -= 25
    pdf.drawString(45, y, "Produto")
    pdf.drawString(310, y, "Qtd.")
    pdf.drawString(365, y, "Unitário")
    pdf.drawString(455, y, "Subtotal")
    y -= 12
    pdf.line(45, y, largura - 45, y)
    y -= 18
    for item in itens:
        if y < 90:
            pdf.showPage()
            y = altura - 55
        nome, qtd, preco, subtotal = item
        pdf.drawString(45, y, str(nome)[:42])
        pdf.drawRightString(340, y, str(qtd))
        pdf.drawRightString(425, y, f"R$ {preco:.2f}")
        pdf.drawRightString(545, y, f"R$ {subtotal:.2f}")
        y -= 18
    y -= 12
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawRightString(545, y, f"TOTAL: R$ {total:.2f}")
    y -= 22
    pdf.setFont("Helvetica", 10)
    pdf.drawString(45, y, f"Pagamento: {pagamento}")
    if valor_pago is not None:
        y -= 17
        pdf.drawString(45, y, f"Valor recebido: R$ {valor_pago:.2f}    Troco: R$ {troco:.2f}")
    y -= 35
    pdf.drawString(45, y, "Obrigado pela preferência!")
    pdf.save()
    return arquivo
