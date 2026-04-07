import argparse
import os
import sys
import time

from servo_braco3d import MaoRobotica, NOME_DEDO


DEFAULT_ARDUINO_PORT = os.getenv("ARDUINO_PORT")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Testa os servos da mao robotica via Arduino."
    )
    parser.add_argument(
        "--porta",
        default=DEFAULT_ARDUINO_PORT,
        help=(
            "Porta serial do Arduino. Se omitida, usa ARDUINO_PORT "
            "ou tenta detectar automaticamente."
        ),
    )
    parser.add_argument(
        "--dedo",
        choices=["polegar", "indicador", "medio", "anelar", "minimo", "todos"],
        default="todos",
        help="Qual dedo testar (padrao: todos).",
    )
    return parser.parse_args()


PINO_POR_NOME = {
    "polegar": 10,
    "indicador": 9,
    "medio": 8,
    "anelar": 7,
    "minimo": 6,
}


def main() -> None:
    args = parse_args()

    try:
        mao = MaoRobotica(porta=args.porta)
    except Exception as erro:
        print(f"[ERRO] Nao foi possivel conectar ao Arduino na porta {args.porta}: {erro}")
        sys.exit(1)

    try:
        if args.dedo == "todos":
            print("[Teste] Testando todos os dedos sequencialmente...")
            mao.testar_todos()
        else:
            pino = PINO_POR_NOME[args.dedo]
            nome = NOME_DEDO[pino]
            print(f"[Teste] Testando apenas: {nome} (pino {pino})")

            mao.abrir_todos()
            mao.definir_dedo(pino, False)
            time.sleep(1)
            mao.definir_dedo(pino, True)
            time.sleep(1)
            print(f"[Teste] {nome} OK.")

    except KeyboardInterrupt:
        print("\n[Teste] Interrompido pelo usuario.")

    finally:
        mao.encerrar()


if __name__ == "__main__":
    main()
