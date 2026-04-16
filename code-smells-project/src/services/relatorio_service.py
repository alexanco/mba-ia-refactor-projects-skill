from src.models import pedido_model

DISCOUNT_TIER_HIGH = 10000
DISCOUNT_TIER_MID = 5000
DISCOUNT_TIER_LOW = 1000
DISCOUNT_RATE_HIGH = 0.10
DISCOUNT_RATE_MID = 0.05
DISCOUNT_RATE_LOW = 0.02


def calcular_desconto(faturamento):
    if faturamento > DISCOUNT_TIER_HIGH:
        return faturamento * DISCOUNT_RATE_HIGH
    if faturamento > DISCOUNT_TIER_MID:
        return faturamento * DISCOUNT_RATE_MID
    if faturamento > DISCOUNT_TIER_LOW:
        return faturamento * DISCOUNT_RATE_LOW
    return 0


def gerar_relatorio_vendas():
    dados = pedido_model.relatorio_vendas()
    faturamento = dados["faturamento_bruto"]
    desconto = calcular_desconto(faturamento)
    dados["desconto_aplicavel"] = round(desconto, 2)
    dados["faturamento_liquido"] = round(faturamento - desconto, 2)
    return dados
