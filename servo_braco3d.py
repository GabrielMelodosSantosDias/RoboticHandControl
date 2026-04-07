import os
import time

from pyfirmata2 import Arduino, SERVO
from serial.tools import list_ports


DEFAULT_ARDUINO_PORT = os.getenv("ARDUINO_PORT")
ARDUINO_HINTS = ("arduino", "usb serial", "ch340", "cp210", "ftdi", "wch")

ANGULOS_ABERTO = 0
ANGULO_POLEGAR = 150
ANGULO_INDICADOR = 180
ANGULO_PADRAO = 140

ANGULOS_FECHADO: dict[int, int] = {
    10: ANGULO_POLEGAR,
    9: ANGULO_INDICADOR,
    8: ANGULO_PADRAO,
    7: ANGULO_PADRAO,
    6: ANGULO_PADRAO,
}

NOME_DEDO: dict[int, str] = {
    10: "Polegar",
    9: "Indicador",
    8: "Medio",
    7: "Anelar",
    6: "Minimo",
}


class MaoRobotica:
    PINOS = [10, 9, 8, 7, 6]

    def __init__(self, porta: str | None = DEFAULT_ARDUINO_PORT) -> None:
        self.porta = self._resolver_porta(porta)
        print(f"[MaoRobotica] Conectando ao Arduino em {self.porta}...")
        self.board = Arduino(self.porta)
        self._configurar_servos()
        self._estado: dict[int, bool | None] = {pino: None for pino in self.PINOS}
        print("[MaoRobotica] Pronto.")

    @staticmethod
    def _resolver_porta(porta_informada: str | None) -> str:
        if porta_informada:
            return porta_informada

        for porta in list_ports.comports():
            texto = " ".join(
                parte for parte in (
                    porta.device,
                    porta.description,
                    porta.manufacturer,
                )
                if parte
            ).lower()
            if any(hint in texto for hint in ARDUINO_HINTS):
                print(
                    "[MaoRobotica] Porta detectada automaticamente: "
                    f"{porta.device} ({porta.description})"
                )
                return porta.device

        portas_disponiveis = [
            f"{porta.device} ({porta.description})" for porta in list_ports.comports()
        ]
        portas_texto = ", ".join(portas_disponiveis) if portas_disponiveis else "nenhuma"
        raise RuntimeError(
            "Nao foi possivel detectar o Arduino automaticamente. "
            f"Portas encontradas: {portas_texto}. "
            "Use --porta COMx ou defina ARDUINO_PORT."
        )

    def _configurar_servos(self) -> None:
        for pino in self.PINOS:
            self.board.digital[pino].mode = SERVO

    def _validar_pino(self, pino: int) -> None:
        if pino not in self.PINOS:
            raise ValueError(f"Pino de servo invalido: {pino}")

    def _mover_servo(self, pino: int, angulo: int) -> None:
        self._validar_pino(pino)
        self.board.digital[pino].write(angulo)
        time.sleep(0.015)

    def definir_dedo(self, pino: int, aberto: bool) -> None:
        self._validar_pino(pino)

        if self._estado[pino] == aberto:
            return

        angulo = ANGULOS_ABERTO if aberto else ANGULOS_FECHADO[pino]
        self._mover_servo(pino, angulo)
        self._estado[pino] = aberto

    def abrir_todos(self) -> None:
        for pino in self.PINOS:
            self._mover_servo(pino, ANGULOS_ABERTO)
            self._estado[pino] = True

    def fechar_todos(self) -> None:
        for pino in self.PINOS:
            self._mover_servo(pino, ANGULOS_FECHADO[pino])
            self._estado[pino] = False

    def testar_todos(self) -> None:
        print("[Teste] Abrindo todos os dedos...")
        self.abrir_todos()
        time.sleep(1)

        for pino in self.PINOS:
            nome = NOME_DEDO.get(pino, f"pino {pino}")
            print(f"[Teste] Testando {nome}...")
            angulo_fechado = ANGULOS_FECHADO[pino]
            self._mover_servo(pino, angulo_fechado)
            time.sleep(1)
            self._mover_servo(pino, ANGULOS_ABERTO)
            self._estado[pino] = True
            time.sleep(1)

        print("[Teste] Concluido.")

    def encerrar(self) -> None:
        print("[MaoRobotica] Encerrando e fechando a porta serial...")
        try:
            self.abrir_todos()
            time.sleep(0.5)
        finally:
            self.board.exit()
            print("[MaoRobotica] Conexao encerrada.")
