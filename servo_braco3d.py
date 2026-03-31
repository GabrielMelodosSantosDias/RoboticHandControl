from pyfirmata import Arduino, SERVO
import time

ANGULOS_ABERTO  = 0    
ANGULO_POLEGAR  = 150  
ANGULO_INDICADOR= 180 
ANGULO_PADRAO   = 140  

ANGULOS_FECHADO: dict[int, int] = {
    10: ANGULO_POLEGAR,
    9:  ANGULO_INDICADOR,
    8:  ANGULO_PADRAO,
    7:  ANGULO_PADRAO,
    6:  ANGULO_PADRAO,
}


NOME_DEDO: dict[int, str] = {
    10: "Polegar",
    9:  "Indicador",
    8:  "Médio",
    7:  "Anelar",
    6:  "Mínimo",
}


class MaoRobotica:


    PINOS = [10, 9, 8, 7, 6]  # polegar → mínimo

    def __init__(self, porta: str = "COM3") -> None:
        print(f"[MaoRobotica] Conectando ao Arduino em {porta}...")
        self.board = Arduino(porta)
        self._configurar_servos()

        # Cache do último estado enviado para evitar comandos redundantes
        # True = aberto, False = fechado
        self._estado: dict[int, bool | None] = {pino: None for pino in self.PINOS}

        print("[MaoRobotica] Pronto.")


    def _configurar_servos(self) -> None:
        """Coloca todos os pinos no modo SERVO."""
        for pino in self.PINOS:
            self.board.digital[pino].mode = SERVO


    def _mover_servo(self, pino: int, angulo: int) -> None:
        """
        Envia um ângulo para um servo específico.

        Parâmetros
        ----------
        pino   : número do pino digital do Arduino
        angulo : ângulo desejado em graus (0–180)
        """
        self.board.digital[pino].write(angulo)
        time.sleep(0.015)  # pequena pausa para o servo responder

 

    def definir_dedo(self, pino: int, aberto: bool) -> None:
        
        if self._estado[pino] == aberto:
            return  # sem mudança, não faz nada

        angulo = ANGULOS_ABERTO if aberto else ANGULOS_FECHADO[pino]
        self._mover_servo(pino, angulo)
        self._estado[pino] = aberto

    def abrir_todos(self) -> None:
        """Abre todos os dedos (posição de repouso)."""
        for pino in self.PINOS:
            self._mover_servo(pino, ANGULOS_ABERTO)
            self._estado[pino] = True

    def fechar_todos(self) -> None:
        """Fecha todos os dedos."""
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

        print("[Teste] Concluído.")

    def encerrar(self) -> None:
        """Abre todos os dedos e encerra a conexão com o Arduino com segurança."""
        print("[MaoRobotica] Encerrando — abrindo dedos e fechando porta serial...")
        self.abrir_todos()
        time.sleep(0.5)
        self.board.exit()
        print("[MaoRobotica] Conexão encerrada.")
