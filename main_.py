"""
main.py
Captura vídeo da webcam, detecta a posição dos dedos com MediaPipe e envia
comandos para a mão robótica via Arduino/pyFirmata.

Pressione 'q' para encerrar o programa com segurança.
"""

import sys
import cv2
import mediapipe as mp

from servo_braco3d import MaoRobotica

PORTA_ARDUINO   = "COM3"  
CAMERA_INDEX    = 0        
LARGURA_FRAME   = 640      
ALTURA_FRAME    = 480      


LIMIAR_POLEGAR   = 80   
LIMIAR_INDICADOR = 1   
LIMIAR_MEDIO     = 1   
LIMIAR_ANELAR    = 1    
LIMIAR_MINIMO    = 1    


def dedos_abertos(pontos: list[tuple[int, int]]) -> dict[str, bool]:
    dist_polegar   = abs(pontos[17][0] - pontos[4][0])
    dist_indicador = pontos[5][1]  - pontos[8][1]
    dist_medio     = pontos[9][1]  - pontos[12][1]
    dist_anelar    = pontos[13][1] - pontos[16][1]
    dist_minimo    = pontos[17][1] - pontos[20][1]

    return {
        "polegar":   dist_polegar   < LIMIAR_POLEGAR,   
        "indicador": dist_indicador >= LIMIAR_INDICADOR,
        "medio":     dist_medio     >= LIMIAR_MEDIO,
        "anelar":    dist_anelar    >= LIMIAR_ANELAR,
        "minimo":    dist_minimo    >= LIMIAR_MINIMO,
    }


def iniciar_camera(indice: int) -> cv2.VideoCapture:
    """
    Abre a câmera e configura a resolução.
    Lança RuntimeError se a câmera não estiver disponível.
    """
    cap = cv2.VideoCapture(indice, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise RuntimeError(
            f"Não foi possível abrir a câmera de índice {indice}. "
            "Verifique se ela está conectada e não está em uso."
        )
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  LARGURA_FRAME)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, ALTURA_FRAME)
    return cap


def main() -> None:
    try:
        mao = MaoRobotica(porta=PORTA_ARDUINO)
    except Exception as e:
        print(f"[ERRO] Falha ao conectar ao Arduino: {e}")
        sys.exit(1)

    # --- Inicialização da câmera ---
    try:
        cap = iniciar_camera(CAMERA_INDEX)
    except RuntimeError as e:
        print(f"[ERRO] {e}")
        mao.encerrar()
        sys.exit(1)
    mp_hands    = mp.solutions.hands
    mp_desenho  = mp.solutions.drawing_utils
    detector    = mp_hands.Hands(max_num_hands=1)

    DEDO_PINO = {
        "polegar":   10,
        "indicador":  9,
        "medio":      8,
        "anelar":     7,
        "minimo":     6,
    }
    
    print("[main] Iniciando captura. Pressione 'q' para sair.")

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("[AVISO] Frame inválido recebido da câmera — tentando novamente...")
                continue


            frame_rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            resultados = detector.process(frame_rgb)

            landmarks_maos = resultados.multi_hand_landmarks
            h, w, _ = frame.shape
            pontos: list[tuple[int, int]] = []

            if landmarks_maos:
                for landmarks in landmarks_maos:
                    mp_desenho.draw_landmarks(frame, landmarks, mp_hands.HAND_CONNECTIONS)

                    # Converte coordenadas normalizadas (0–1) em pixels
                    for _, lm in enumerate(landmarks.landmark):
                        cx = int(lm.x * w)
                        cy = int(lm.y * h)
                        cv2.circle(frame, (cx, cy), 4, (255, 0, 0), -1)
                        pontos.append((cx, cy))

                if len(pontos) == 21:
                    estado = dedos_abertos(pontos)

                    for nome_dedo, aberto in estado.items():
                        pino = DEDO_PINO[nome_dedo]
                        mao.definir_dedo(pino, aberto)

            cv2.imshow("Mão Robótica — pressione Q para sair", frame)

            # Encerra ao pressionar 'q'
            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("[main] Tecla 'q' pressionada — encerrando...")
                break

    except KeyboardInterrupt:
        print("[main] Interrompido pelo usuário (Ctrl+C).")

    finally:
        cap.release()
        cv2.destroyAllWindows()
        mao.encerrar()
        print("[main] Programa encerrado com sucesso.")


if __name__ == "__main__":
    main()
