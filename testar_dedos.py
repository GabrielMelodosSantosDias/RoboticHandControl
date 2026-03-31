import argparse
import sys

from servo_braco3d import MaoRobotica, NOME_DEDO


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Testa os servos da mão robótica via Arduino."
    )
    parser.add_argument(
        "--porta", default="COM3",
        help="Porta serial do Arduino (padrão: COM3)"
    )
    parser.add_argument(
        "--dedo",
        choices=["polegar", "indicador", "medio", "anelar", "minimo", "todos"],
        default="todos",
        help="Qual dedo testar (padrão: todos)"
    )
    return parser.parse_args()

PINO_POR_NOME = {
    "polegar":   10,
    "indicador":  9,
    "medio":      8,
    "anelar":     7,
    "minimo":     6,
}


def main() -> None:
    args = parse_args()

    try:
        mao = MaoRobotica(porta=args.porta)
    except Exception as e:
        print(f"[ERRO] Não foi possível conectar ao Arduino: {e}")
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

            import time
            mao.definir_dedo(pino, False)   # fecha
            time.sleep(1)
            mao.definir_dedo(pino, True)    # abre
            time.sleep(1)
            print(f"[Teste] {nome} OK.")

    except KeyboardInterrupt:
        print("\n[Teste] Interrompido pelo usuário.")

    finally:
        mao.encerrar()


if __name__ == "__main__":
    main()
