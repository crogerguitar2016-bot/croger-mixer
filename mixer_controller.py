class MixerController:

    STEMS = (
        "voz",
        "bateria",
        "baixo",
        "outros",
    )

    def __init__(self):

        self.music_path = None
        self.music_name = "Nenhuma música selecionada"

        self.playing = False
        self.position = 0.0
        self.duration = 0.0

        self.tonalidade = "--"
        self.bpm = 0
        self.compasso = "--"

        self.campo_harmonico = []

        self.acorde_atual = "--"
        self.proximos_acordes = []

        self.numero_compasso = 0
        self.tempo_compasso = 0

        self.transposicao = 0

        self.metronomo_ligado = False
        self.metronomo_volume = 0.70

        self.audio_engine = None
        self.last_error = None

        self.stems = {

            "voz": {
                "volume": 0.85,
                "mute": False,
                "solo": False,
            },

            "bateria": {
                "volume": 0.70,
                "mute": False,
                "solo": False,
            },

            "baixo": {
                "volume": 0.60,
                "mute": False,
                "solo": False,
            },

            "outros": {
                "volume": 0.50,
                "mute": False,
                "solo": False,
            },

        }

        self.on_change = None


    # =====================================================
    # INTERFACE
    # =====================================================

    def _notify(self):

        if callable(self.on_change):
            self.on_change()


    # =====================================================
    # MOTOR DE ÁUDIO
    # =====================================================

    def attach_audio_engine(
        self,
        engine
    ):

        self.audio_engine = engine


    def selecionar_musica(self):

        self.last_error = None

        if self.audio_engine is None:
            self.audio_error(
                "Motor de áudio não disponível."
            )
            return False

        return self.audio_engine.open_picker()


    def audio_loaded(
        self,
        nome,
        caminho,
        duracao
    ):

        self.music_path = caminho
        self.music_name = nome

        self.position = 0.0
        self.duration = float(duracao)

        self.playing = False
        self.last_error = None

        self._notify()


    def audio_error(
        self,
        mensagem
    ):

        self.last_error = str(
            mensagem
        )

        print(
            "CROGER MIXER:",
            self.last_error
        )

        self._notify()


    def sync_audio_state(self):

        engine = self.audio_engine

        if (
            engine is None
            or not engine.is_loaded
        ):
            return

        self.playing = (
            engine.is_playing
        )

        self.position = (
            engine.position_ms
            / 1000.0
        )

        self.duration = (
            engine.duration_ms
            / 1000.0
        )


    # =====================================================
    # PLAYER REAL
    # =====================================================

    def play_pause(self):

        engine = self.audio_engine

        if (
            engine is None
            or not engine.is_loaded
        ):
            self.audio_error(
                "Selecione uma música primeiro."
            )
            return False

        resultado = (
            engine.play_pause()
        )

        if resultado:
            self.last_error = None
            self.sync_audio_state()
            self._notify()

        return resultado


    def parar(self):

        engine = self.audio_engine

        if (
            engine is None
            or not engine.is_loaded
        ):
            return False

        resultado = engine.stop()

        if resultado:
            self.playing = False
            self.position = 0.0
            self._notify()

        return resultado


    def avancar(
        self,
        segundos=10
    ):

        engine = self.audio_engine

        if (
            engine is None
            or not engine.is_loaded
        ):
            return False

        atual = (
            engine.position_ms
            / 1000.0
        )

        destino = (
            atual
            + float(segundos)
        )

        if self.duration > 0:
            destino = min(
                destino,
                self.duration
            )

        resultado = engine.seek_to(
            int(destino * 1000)
        )

        if resultado:
            self.position = destino
            self._notify()

        return resultado


    def voltar(
        self,
        segundos=10
    ):

        engine = self.audio_engine

        if (
            engine is None
            or not engine.is_loaded
        ):
            return False

        atual = (
            engine.position_ms
            / 1000.0
        )

        destino = max(
            0.0,
            atual - float(segundos)
        )

        resultado = engine.seek_to(
            int(destino * 1000)
        )

        if resultado:
            self.position = destino
            self._notify()

        return resultado


    def seek(
        self,
        position
    ):

        engine = self.audio_engine

        if (
            engine is None
            or not engine.is_loaded
        ):
            return False

        position = max(
            0.0,
            float(position)
        )

        if self.duration > 0:
            position = min(
                position,
                self.duration
            )

        resultado = engine.seek_to(
            int(position * 1000)
        )

        if resultado:
            self.position = position
            self._notify()

        return resultado


    # =====================================================
    # STEMS / MIXER
    # =====================================================

    def set_volume(
        self,
        stem,
        volume
    ):

        if stem not in self.stems:
            return

        volume = max(
            0.0,
            min(
                float(volume),
                1.5
            )
        )

        self.stems[stem]["volume"] = volume

        self._notify()


    def toggle_mute(
        self,
        stem
    ):

        if stem not in self.stems:
            return

        atual = self.stems[stem]["mute"]

        self.stems[stem]["mute"] = (
            not atual
        )

        self._notify()


    def toggle_solo(
        self,
        stem
    ):

        if stem not in self.stems:
            return

        atual = self.stems[stem]["solo"]

        self.stems[stem]["solo"] = (
            not atual
        )

        self._notify()


    def volume_efetivo(
        self,
        stem
    ):

        if stem not in self.stems:
            return 0.0

        dados = self.stems[stem]

        if dados["mute"]:
            return 0.0

        existe_solo = any(
            item["solo"]
            for item in self.stems.values()
        )

        if (
            existe_solo
            and
            not dados["solo"]
        ):
            return 0.0

        return dados["volume"]


    # =====================================================
    # TRANSPOSIÇÃO
    # =====================================================

    def set_transposicao(
        self,
        semitons
    ):

        semitons = int(
            semitons
        )

        semitons = max(
            -12,
            min(
                12,
                semitons
            )
        )

        self.transposicao = (
            semitons
        )

        self._notify()


    # =====================================================
    # METRÔNOMO
    # =====================================================

    def toggle_metronomo(self):

        self.metronomo_ligado = (
            not self.metronomo_ligado
        )

        self._notify()


    def set_metronomo_volume(
        self,
        volume
    ):

        self.metronomo_volume = max(
            0.0,
            min(
                1.0,
                float(volume)
            )
        )

        self._notify()


    # =====================================================
    # ANÁLISE MUSICAL
    # =====================================================

    def aplicar_analise(
        self,
        tonalidade,
        bpm,
        compasso,
        campo_harmonico=None
    ):

        self.tonalidade = tonalidade
        self.bpm = int(bpm)
        self.compasso = compasso

        self.campo_harmonico = (
            list(campo_harmonico)
            if campo_harmonico
            else []
        )

        self._notify()


    def atualizar_posicao_musical(
        self,
        numero_compasso,
        tempo_compasso,
        acorde_atual,
        proximos=None
    ):

        self.numero_compasso = int(
            numero_compasso
        )

        self.tempo_compasso = int(
            tempo_compasso
        )

        self.acorde_atual = str(
            acorde_atual
        )

        self.proximos_acordes = (
            list(proximos)
            if proximos
            else []
        )

        self._notify()


    # =====================================================
    # PROCESSAMENTO FUTURO
    # =====================================================

    def analisar_e_mixar(self):

        print(
            "CROGER MIXER:"
            " analisar_e_mixar()"
        )


    def salvar_exportar(self):

        print(
            "CROGER MIXER:"
            " salvar_exportar()"
        )


    # =====================================================
    # FINALIZAÇÃO
    # =====================================================

    def release(self):

        if self.audio_engine is not None:

            try:
                self.audio_engine.release()
            except Exception:
                pass
