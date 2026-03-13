#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para atualizar dados de mercado extraindo de APIs confiáveis.
Fontes: BCB (SGS), Yahoo Finance v8, CoinGecko
Versão CORRIGIDA - endpoints validados em 13/03/2026
"""

import json
from datetime import datetime, timedelta, timezone
import sys

def get_market_data():
    """
    Coleta dados de mercado com fallback para valores estáticos.
    """
    brt = timezone(timedelta(hours=-3))
    now_brt = datetime.now(brt)

    market_data = {
        'timestamp': now_brt.isoformat(),
        'last_update': now_brt.strftime('%d/%m/%Y %H:%M:%S'),
        'data': {}
    }

    # Valores de fallback (usados quando a API falha)
    default_data = {
        'dollar':   {'value': 5.20, 'date': now_brt.strftime('%d/%m/%Y'), 'change': 0.0},
        'selic':    {'value': 15.00, 'date': now_brt.strftime('%d/%m/%Y'), 'change': 0.0},
        'ipca':     {'value': 3.81, 'date': now_brt.strftime('%d/%m/%Y'), 'change': 0.0},
        'ibovespa': {'value': 130000, 'change': 0.0, 'currency': 'BRL'},
        'bitcoin':  {'value': 370000, 'change': 0.0, 'currency': 'BRL'},
        'euro':     {'value': 5.90, 'date': now_brt.strftime('%d/%m/%Y'), 'change': 0.0},
    }

    print("=" * 60)
    print("ATUALIZANDO DADOS DE MERCADO")
    print("=" * 60)

    try:
        import requests

        # ─────────────────────────────────────────────
        # 1. DÓLAR PTAX VENDA — BCB SGS série 10813
        # ─────────────────────────────────────────────
        try:
            print("   - Dólar (BCB SGS 10813)...", end=" ", flush=True)
            url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.10813/dados/ultimos/2?formato=json"
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if len(data) >= 1:
                    curr = float(data[-1]['valor'])
                    default_data['dollar']['value'] = curr
                    default_data['dollar']['date'] = data[-1]['data']
                    if len(data) >= 2:
                        prev = float(data[-2]['valor'])
                        default_data['dollar']['change'] = round(((curr - prev) / prev) * 100, 2)
                    print("✓")
                else:
                    print("✗ (dados vazios)")
            else:
                print(f"✗ (HTTP {resp.status_code})")
        except Exception as e:
                print(f"✗ ({str(e)[:40]})")

        # ─────────────────────────────────────────────
        # 2. SELIC META — BCB SGS série 432
        # ─────────────────────────────────────────────
        try:
            print("   - Selic (BCB SGS 432)...", end=" ", flush=True)
            url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json"
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if data:
                    default_data['selic']['value'] = float(data[-1]['valor'])
                    default_data['selic']['date'] = data[-1]['data']
                    print("✓")
                else:
                    print("✗ (dados vazios)")
            else:
                print(f"✗ (HTTP {resp.status_code})")
        except Exception as e:
            print(f"✗ ({str(e)[:40]})")

        # ─────────────────────────────────────────────
        # 3. IPCA ACUMULADO 12 MESES — BCB SGS série 13522
        # ─────────────────────────────────────────────
        try:
            print("   - IPCA 12M (BCB SGS 13522)...", end=" ", flush=True)
            url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.13522/dados/ultimos/2?formato=json"
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if data:
                    curr = float(data[-1]['valor'])
                    default_data['ipca']['value'] = curr
                    default_data['ipca']['date'] = data[-1]['data']
                    if len(data) >= 2:
                        prev = float(data[-2]['valor'])
                        default_data['ipca']['change'] = round(curr - prev, 2)
                    print("✓")
                else:
                    print("✗ (dados vazios)")
            else:
                print(f"✗ (HTTP {resp.status_code})")
        except Exception as e:
            print(f"✗ ({str(e)[:40]})")

        # ─────────────────────────────────────────────
        # 4. EURO/BRL — BCB SGS série 21619
        # ─────────────────────────────────────────────
        try:
            print("   - Euro (BCB SGS 21619)...", end=" ", flush=True)
            url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.21619/dados/ultimos/2?formato=json"
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if data:
                    curr = float(data[-1]['valor'])
                    default_data['euro']['value'] = curr
                    default_data['euro']['date'] = data[-1]['data']
                    if len(data) >= 2:
                        prev = float(data[-2]['valor'])
                        default_data['euro']['change'] = round(((curr - prev) / prev) * 100, 2)
                    print("✓")
                else:
                    print("✗ (dados vazios)")
            else:
                print(f"✗ (HTTP {resp.status_code})")
        except Exception as e:
            print(f"✗ ({str(e)[:40]})")

        # ─────────────────────────────────────────────
        # 5. IBOVESPA — HG Brasil Finance (primário) + Yahoo Finance v8 (fallback)
        # ─────────────────────────────────────────────
        ibovespa_ok = False
        try:
            print("   - Ibovespa (HG Brasil Finance)...", end=" ", flush=True)
            url = "https://api.hgbrasil.com/finance?format=json&key=free"
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                d = resp.json()
                ibov = d.get('results', {}).get('stocks', {}).get('IBOVESPA', {})
                price = ibov.get('points')
                variation = ibov.get('variation')
                if price:
                    default_data['ibovespa']['value'] = int(price)
                    if variation is not None:
                        default_data['ibovespa']['change'] = round(float(variation), 2)
                    print("✓")
                    ibovespa_ok = True
                else:
                    print("✗ (preço não encontrado)")
            else:
                print(f"✗ (HTTP {resp.status_code})")
        except Exception as e:
            print(f"✗ ({str(e)[:40]})")

        if not ibovespa_ok:
            try:
                print("   - Ibovespa (Yahoo Finance v8 fallback)...", end=" ", flush=True)
                url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EBVSP?interval=1d&range=5d"
                headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0'}
                resp = requests.get(url, timeout=15, headers=headers)
                if resp.status_code == 200:
                    d = resp.json()
                    result = d.get('chart', {}).get('result', [])
                    if result:
                        meta = result[0].get('meta', {})
                        price = meta.get('regularMarketPrice')
                        prev_close = meta.get('previousClose') or meta.get('chartPreviousClose')
                        if price:
                            default_data['ibovespa']['value'] = int(price)
                            if prev_close and prev_close > 0:
                                change_pct = ((price - prev_close) / prev_close) * 100
                                default_data['ibovespa']['change'] = round(change_pct, 2)
                            print("✓")
                        else:
                            print("✗ (preço não encontrado)")
                    else:
                        print("✗ (resultado vazio)")
                else:
                    print(f"✗ (HTTP {resp.status_code})")
            except Exception as e:
                print(f"✗ ({str(e)[:40]})")

        # ─────────────────────────────────────────────
        # 6. BITCOIN/BRL — CoinGecko
        # ─────────────────────────────────────────────
        try:
            print("   - Bitcoin (CoinGecko)...", end=" ", flush=True)
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=brl&include_24hr_change=true"
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if 'bitcoin' in data and 'brl' in data['bitcoin']:
                    default_data['bitcoin']['value'] = int(data['bitcoin']['brl'])
                    change = data['bitcoin'].get('brl_24h_change', 0)
                    default_data['bitcoin']['change'] = round(change, 2)
                    print("✓")
                else:
                    print("✗ (dados vazios)")
            else:
                print(f"✗ (HTTP {resp.status_code})")
        except Exception as e:
            print(f"✗ ({str(e)[:40]})")

    except ImportError:
        print("\n⚠ Módulo 'requests' não disponível. Usando fallback.")
    except Exception as e:
        print(f"\n⚠ Erro geral: {e}. Usando fallback.")

    market_data['data'] = default_data
    return market_data


def save_data(market_data, filename='market_data.json'):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(market_data, f, ensure_ascii=False, indent=2)
        print(f"\n✓ Dados salvos em {filename}")
        return True
    except Exception as e:
        print(f"\n✗ Erro ao salvar: {e}")
        return False


def main():
    try:
        market_data = get_market_data()

        if save_data(market_data):
            print("\n" + "=" * 60)
            print("✓ ATUALIZAÇÃO CONCLUÍDA COM SUCESSO!")
            print("=" * 60)
            print(f"Timestamp: {market_data['last_update']}")
            print("\nDados coletados:")
            for key, value in market_data['data'].items():
                val = value.get('value', 'N/A')
                change = value.get('change', 0)
                if key == 'ibovespa':
                    print(f"  • {key.upper():10s}: {val:>12,.0f}  ({change:+.2f}%)")
                elif key == 'bitcoin':
                    print(f"  • {key.upper():10s}: R$ {val:>10,.0f}  ({change:+.2f}%)")
                else:
                    print(f"  • {key.upper():10s}: {val:>10.4f}  ({change:+.2f}%)")
            print("=" * 60)
            return 0
        else:
            return 1

    except Exception as e:
        print(f"\n✗ Erro geral: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
