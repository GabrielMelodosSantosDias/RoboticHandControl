"""
main.py
Captura video da webcam, detecta a posicao dos dedos com MediaPipe
e envia comandos para a mao robotica via Arduino/pyFirmata2.

Pressione 'q' para encerrar o programa com seguranca.
"""

import argparse
import os
import sys

import cv2
import mediapipe as mp

from servo_braco3d import MaoRobotica


def _ler_int_env(nome: str, padrao: int) -> int:
    valor = os.getenv(nome)
    if valor is None:
        return padrao

    try:
        return int(valor)
    except ValueError:
        return padrao


DEFAULT_ARDUINO_PORT = os.getenv("ARDUINO_PORT")
DEFAULT_CAMERA_INDEX = _ler_int_env("CAMERA_INDEX", 0)
LARGURA_FRAME = 640
ALTURA_FRAME = 480

LIMIAR_POLEGAR = 80
LIMIAR_INDICADOR = 1
LIMIAR_MEDIO = 1
LIMIAR_ANELAR = 1
LIMIAR_MINIMO = 1

DEDO_PINO = {
    "polegar": 10,
    "indicador": 9,
    "medio": 8,
    "anelar": 7,
    "minimo": 6,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Controla a mao robotica com MediaPipe + Arduino."
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
        "--camera",
        type=int,
        default=DEFAULT_CAMERA_INDEX,
        help="Indice da webcam (padrao: 0 ou variavel CAMERA_INDEX).",
    )
    return parser.parse_args()


def validar_mediapipe() -> None:
    if not hasattr(mp, "solutions") or not hasattr(mp.solutions, "hands"):
        raise RuntimeError(
            "Versao do MediaPipe incompativel com este projeto. "
            "Use Python 3.10 e instale mediapipe==0.10.21."
        )


def dedos_abertos(pontos: list[tuple[int, int]]) -> dict[str, bool]:
    dist_polegar = abs(pontos[17][0] - pontos[4][0])
    dist_indicador = pontos[5][1] - pontos[8][1]
    dist_medio = pontos[9][1] - pontos[12][1]
    dist_anelar = pontos[13][1] - pontos[16][1]
    dist_minimo = pontos[17][1] - pontos[20][1]

    return {
        "polegar": dist_polegar < LIMIAR_POLEGAR,
        "indicador": dist_indicador >= LIMIAR_INDICADOR,
        "medio": dist_medio >= LIMIAR_MEDIO,
        "anelar": dist_anelar >= LIMIAR_ANELAR,
        "minimo": dist_minimo >= LIMIAR_MINIMO,
    }


def iniciar_camera(indice: int) -> cv2.VideoCapture:
    """
    Abre a camera e configura a resolucao.
    Tenta primeiro via DirectShow e depois no backend padrao.
    """
    tentativas = (
        ("DirectShow", lambda: cv2.VideoCapture(indice, cv2.CAP_DSHOW)),
        ("padrao", lambda: cv2.VideoCapture(indice)),
    )

    for nome_backend, criar_captura in tentativas:
        cap = criar_captura()
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, LARGURA_FRAME)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, ALTURA_FRAME)
            if nome_backend != "DirectShow":
                print(f"[AVISO] Camera aberta com backend {nome_backend}.")
            return cap
        cap.release()

    raise RuntimeError(
        f"Nao foi possivel abrir a camera de indice {indice}. "
        "Verifique se ela esta conectada e nao esta em uso."
    )


def main() -> None:
    args = parse_args()

    try:
        validar_mediapipe()
    except RuntimeError as erro:
        print(f"[ERRO] {erro}")
        sys.exit(1)

    try:
        mao = MaoRobotica(porta=args.porta)
    except Exception as erro:
        print(f"[ERRO] Falha ao conectar ao Arduino na porta {args.porta}: {erro}")
        sys.exit(1)

    try:
        cap = iniciar_camera(args.camera)
    except RuntimeError as erro:
        print(f"[ERRO] {erro}")
        mao.encerrar()
        sys.exit(1)

    mp_hands = mp.solutions.hands
    mp_desenho = mp.solutions.drawing_utils

    print(
        f"[main] Iniciando captura na camera {args.camera} "
        f"com Arduino em {args.porta}. Pressione 'q' para sair."
    )

    try:
        with mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        ) as detector:
            while True:
                ok, frame = cap.read()
                if not ok:
                    print("[AVISO] Frame invalido recebido da camera; tentando novamente...")
                    continue

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                resultados = detector.process(frame_rgb)

                landmarks_maos = resultados.multi_hand_landmarks
                h, w, _ = frame.shape
                pontos: list[tuple[int, int]] = []

                if landmarks_maos:
                    for landmarks in landmarks_maos:
                        mp_desenho.draw_landmarks(
                            frame,
                            landmarks,
                            mp_hands.HAND_CONNECTIONS,
                        )

                        for lm in landmarks.landmark:
                            cx = int(lm.x * w)
                            cy = int(lm.y * h)
                            cv2.circle(frame, (cx, cy), 4, (255, 0, 0), -1)
                            pontos.append((cx, cy))

                    if len(pontos) == 21:
                        estado = dedos_abertos(pontos)
                        for nome_dedo, aberto in estado.items():
                            pino = DEDO_PINO[nome_dedo]
                            mao.definir_dedo(pino, aberto)

                cv2.imshow("Mao Robotica - pressione Q para sair", frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    print("[main] Tecla 'q' pressionada; encerrando...")
                    break

    except KeyboardInterrupt:
        print("[main] Interrompido pelo usuario (Ctrl+C).")

    finally:
        cap.release()
        cv2.destroyAllWindows()
        mao.encerrar()
        print("[main] Programa encerrado com sucesso.")


if __name__ == "__main__":
    main()
