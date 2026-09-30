"""
Pipeline Automatizado - Conclusão do Experimento Decimal para gemini-3.1-pro-preview
Executa e monitora os jobs da Batch API do OpenRouter para as 320 requisições restantes.
"""

import os
import sys
import json
import time
import argparse
import subprocess
import logging
from datetime import datetime

PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
PASTA_3_FASE = os.path.dirname(os.path.dirname(PASTA_SCRIPT))
SCRIPT_ENVIAR = os.path.join(PASTA_SCRIPT, "enviar_chamadas_decimal.py")
SCRIPT_SALVAR = os.path.join(PASTA_SCRIPT, "salvar_resultados_decimal.py")
ARQUIVO_CONTROLE = os.path.join(PASTA_3_FASE, "jobs", "jobs_decimal", "controle_jobs_batch.json")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def executar_envio(dry_run=False):
    cmd = [sys.executable, SCRIPT_ENVIAR, "--modelo", "gemini-3.1-pro-preview"]
    if dry_run:
        cmd.append("--dry-run")
    logging.info(f"Executando envio de lote: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print(res.stderr, file=sys.stderr)
    return res.returncode == 0

def verificar_e_salvar():
    cmd = [sys.executable, SCRIPT_SALVAR]
    logging.info(f"Executando checagem e salvamento: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print(res.stderr, file=sys.stderr)
    return res.returncode == 0

def main():
    parser = argparse.ArgumentParser(description="Pipeline Batch para gemini-3.1-pro-preview (Multiplicação Decimal)")
    parser.add_argument("--dry-run", action="store_true", help="Valida os payloads sem submeter à API")
    parser.add_argument("--status", action="store_true", help="Apenas verifica status do job e salva se concluído")
    args = parser.parse_args()

    if args.status:
        verificar_e_salvar()
        return

    logging.info("=== Iniciando Pipeline para gemini-3.1-pro-preview (Decimal) ===")
    sucesso = executar_envio(dry_run=args.dry_run)
    if not sucesso:
        logging.error("Falha ao submeter lote. Verifique os logs.")
        return

    if args.dry_run:
        logging.info("Dry-run concluído com sucesso. Nenhuma requisição enviada.")
        return

    logging.info("Lote submetido. Verificando status inicial...")
    verificar_e_salvar()

if __name__ == "__main__":
    main()
