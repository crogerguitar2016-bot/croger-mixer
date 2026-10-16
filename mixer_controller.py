import threading
import time
from pathlib import Path

from kivy.clock import Clock
from motor_client import CrogerMotorClient

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

        self.motor = CrogerMotorClient()

        self.job_id = None
        self.processando = False
        self.exportando = False
        self.status_message = None

        self.analysis_data = {}
        self.acordes_timeline = []
        self.bpm_decimal = 0.0

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
        self.status_message = None

        self.analysis_data = {}
        self.acordes_timeline = []

        self.tonalidade = "--"
        self.bpm = 0
        self.bpm_decimal = 0.0
        self.compasso = "--"

        self.campo_harmonico = []

        self.acorde_atual = "--"
        self.proximos_acordes = []

        self.numero_compasso = 0
        self.tempo_compasso = 0

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

        try:
            engine.sync_stems()
        except Exception:
            pass

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

        self._sincronizar_analise_posicao()


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
                1.0
            )
        )

        self.stems[stem]["volume"] = volume

        self._aplicar_mix_real()

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

        self._aplicar_mix_real()

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

        self._aplicar_mix_real()

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


    def _aplicar_mix_real(self):

        engine = self.audio_engine

        if (
            engine is None
            or not getattr(
                engine,
                "stems_loaded",
                False
            )
        ):
            return

        for stem in self.STEMS:

            engine.set_stem_volume(
                stem,
                self.volume_efetivo(
                    stem
                )
            )


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


    def aplicar_analise_servidor(
        self,
        analise
    ):

        if not isinstance(
            analise,
            dict
        ):
            return False

        self.analysis_data = dict(
            analise
        )

        self.tonalidade = str(
            analise.get(
                "tonalidade",
                "--"
            )
            or "--"
        )

        try:

            self.bpm_decimal = float(
                analise.get(
                    "bpm_decimal",
                    analise.get(
                        "bpm",
                        0
                    )
                )
                or 0
            )

        except Exception:

            self.bpm_decimal = 0.0

        try:

            self.bpm = int(
                round(
                    float(
                        analise.get(
                            "bpm",
                            self.bpm_decimal
                        )
                        or 0
                    )
                )
            )

        except Exception:

            self.bpm = 0

        self.compasso = str(
            analise.get(
                "compasso",
                "--"
            )
            or "--"
        )

        campo = analise.get(
            "campo_harmonico",
            []
        )

        self.campo_harmonico = (
            list(campo)
            if isinstance(
                campo,
                list
            )
            else []
        )

        acordes = analise.get(
            "acordes",
            []
        )

        self.acordes_timeline = (
            list(acordes)
            if isinstance(
                acordes,
                list
            )
            else []
        )

        self._sincronizar_analise_posicao()

        return True


    def _sincronizar_analise_posicao(
        self
    ):

        timeline = (
            self.acordes_timeline
        )

        if not timeline:

            self.acorde_atual = "--"
            self.proximos_acordes = []
            return

        posicao = max(
            0.0,
            float(
                self.position
            )
        )

        indice_atual = 0

        for indice, item in enumerate(
            timeline
        ):

            try:

                inicio = float(
                    item.get(
                        "inicio",
                        0
                    )
                )

                fim = float(
                    item.get(
                        "fim",
                        inicio
                    )
                )

            except Exception:
                continue

            if (
                inicio
                <= posicao
                < fim
            ):

                indice_atual = indice
                break

            if posicao >= inicio:

                indice_atual = indice

        item_atual = timeline[
            indice_atual
        ]

        self.acorde_atual = str(
            item_atual.get(
                "acorde",
                "--"
            )
        )

        proximos = []

        for item in timeline[
            indice_atual + 1:
        ]:

            acorde = str(
                item.get(
                    "acorde",
                    ""
                )
            )

            if not acorde:
                continue

            if (
                acorde
                ==
                self.acorde_atual
            ):
                continue

            if (
                proximos
                and
                acorde
                ==
                proximos[-1]
            ):
                continue

            proximos.append(
                acorde
            )

            if len(
                proximos
            ) >= 4:
                break

        self.proximos_acordes = (
            proximos
        )


    # =====================================================
    # PROCESSAMENTO FUTURO
    # =====================================================

    def analisar_e_mixar(self):

        if self.processando:
            return False

        if not self.music_path:
            self.audio_error(
                "Selecione uma música primeiro."
            )
            return False

        self.processando = True
        self.last_error = None
        self.status_message = (
            "Procurando stems separados..."
        )

        self._notify()

        threading.Thread(
            target=self._carregar_stems_worker,
            daemon=True
        ).start()

        return True


    def _status_worker(
        self,
        mensagem
    ):

        self.status_message = str(
            mensagem
        )

        Clock.schedule_once(
            lambda dt:
            self._notify(),
            0
        )


    def _carregar_stems_worker(self):

        try:

            self._status_worker(
                "Consultando motor CROGER MIXER..."
            )

            dados = self.motor.state()

            jobs = dados.get(
                "jobs",
                {}
            )

            nome_alvo = Path(
                self.music_name
            ).name

            job = None

            # ----------------------------------------------
            # PROCURAR SEPARAÇÃO JÁ EXISTENTE
            # ----------------------------------------------

            encontrados = []

            for item in jobs.values():

                if (
                    item.get("status")
                    != "concluido"
                ):
                    continue

                arquivo = item.get(
                    "arquivo",
                    ""
                )

                if (
                    Path(arquivo).name
                    == nome_alvo
                ):

                    encontrados.append(
                        item
                    )

            if encontrados:

                job = max(
                    encontrados,
                    key=lambda x:
                    x.get(
                        "finalizado_em",
                        0
                    )
                )

                job_id = job["id"]

                self._status_worker(
                    "Separação existente encontrada."
                )

            else:

                # ------------------------------------------
                # MÚSICA NOVA
                # ------------------------------------------

                self._status_worker(
                    "Preparando música para envio..."
                )

                pasta_upload = (
                    Path(
                        self.audio_engine
                        .app_files_dir
                    )
                    /
                    "croger_upload"
                )

                pasta_upload.mkdir(
                    parents=True,
                    exist_ok=True
                )

                arquivo_local = (
                    pasta_upload
                    /
                    nome_alvo
                )

                self.audio_engine.copy_selected_audio_to(
                    arquivo_local
                )

                self._status_worker(
                    "Enviando música ao motor..."
                )

                def progresso_upload(
                    enviado,
                    total
                ):

                    if total <= 0:
                        return

                    percentual = int(
                        enviado
                        * 100
                        / total
                    )

                    self._status_worker(
                        f"Enviando música: "
                        f"{percentual}%"
                    )

                resposta_upload = (
                    self.motor.upload_file(
                        arquivo_local,
                        filename=nome_alvo,
                        progresso=progresso_upload
                    )
                )

                if not resposta_upload.get(
                    "ok"
                ):

                    raise RuntimeError(
                        "Falha no envio da música."
                    )

                self._status_worker(
                    "Iniciando separação Demucs..."
                )

                resposta = (
                    self.motor
                    .iniciar_separacao_por_nome(
                        nome_alvo
                    )
                )

                job_id = resposta.get(
                    "job_id"
                )

                if not job_id:

                    raise RuntimeError(
                        "Motor não retornou job_id."
                    )

                self.job_id = job_id

                # ------------------------------------------
                # ESPERAR DEMUCS
                # ------------------------------------------

                while True:

                    dados_job = (
                        self.motor.job(
                            job_id
                        )
                    )

                    job = dados_job.get(
                        "job",
                        {}
                    )

                    status = job.get(
                        "status"
                    )

                    progresso = job.get(
                        "progresso",
                        0
                    )

                    mensagem = job.get(
                        "mensagem",
                        status
                    )

                    self._status_worker(
                        f"{mensagem} "
                        f"({progresso}%)"
                    )

                    if status == "concluido":
                        break

                    if status == "erro":

                        raise RuntimeError(
                            job.get(
                                "erro",
                                mensagem
                            )
                        )

                    time.sleep(
                        15
                    )

            # ----------------------------------------------
            # BAIXAR STEMS
            # ----------------------------------------------

            self._status_worker(
                "Baixando Voz, Bateria, "
                "Baixo e Outros..."
            )

            pasta = (
                Path(
                    self.audio_engine
                    .app_files_dir
                )
                /
                "croger_stems"
                /
                job_id
            )

            caminhos = (
                self.motor.baixar_stems(
                    job_id,
                    pasta
                )
            )

            analise = None

            try:

                self._status_worker(
                    "Carregando análise musical..."
                )

                resposta_analise = (
                    self.motor.analysis(
                        job_id
                    )
                )

                analise = (
                    resposta_analise.get(
                        "analysis"
                    )
                )

            except Exception:

                analise = None

            Clock.schedule_once(
                lambda dt:
                self._finalizar_stems(
                    job_id,
                    caminhos,
                    analise
                ),
                0
            )

        except Exception as exc:

            mensagem = str(
                exc
            )

            Clock.schedule_once(
                lambda dt:
                self._erro_processamento(
                    mensagem
                ),
                0
            )


    def _finalizar_stems(
        self,
        job_id,
        caminhos,
        analise=None
    ):

        if not self.audio_engine.load_stems(
            caminhos
        ):

            self.processando = False
            return

        self.job_id = job_id

        self._aplicar_mix_real()

        if analise:

            self.aplicar_analise_servidor(
                analise
            )

        self.position = 0.0

        self.duration = (
            self.audio_engine
            .duration_ms
            / 1000.0
        )

        self.playing = False
        self.processando = False
        self.last_error = None

        if analise:

            self.status_message = (
                "Mixer e análise prontos: "
                f"{self.tonalidade} • "
                f"{self.bpm} BPM"
            )

        else:

            self.status_message = (
                "Mixer pronto. "
                "Análise musical ainda não disponível."
            )

        self._notify()


    def _erro_processamento(
        self,
        mensagem
    ):

        self.processando = False
        self.status_message = None

        self.audio_error(
            mensagem
        )


    def salvar_exportar(self):

        if self.exportando:
            return False

        if not self.job_id:

            self.audio_error(
                "Analise e misture a música antes de exportar."
            )

            return False

        if self.audio_engine is None:

            self.audio_error(
                "Motor de áudio não disponível."
            )

            return False

        app_files_dir = getattr(
            self.audio_engine,
            "app_files_dir",
            None
        )

        if not app_files_dir:

            self.audio_error(
                "Diretório interno do aplicativo não disponível."
            )

            return False

        volumes = {
            stem: float(
                self.volume_efetivo(
                    stem
                )
            )
            for stem in self.STEMS
        }

        nome_base = (
            Path(
                self.music_name
            )
            .stem
            .strip()
        )

        if not nome_base:

            nome_base = (
                "CROGER_MIX"
            )

        destino = (
            Path(
                app_files_dir
            )
            /
            "croger_exports"
            /
            (
                nome_base
                + "_CROGER_MIX.mp3"
            )
        )

        self.exportando = True
        self.last_error = None

        self.status_message = (
            "Preparando mix final..."
        )

        self._notify()

        threading.Thread(
            target=self._salvar_exportar_worker,
            args=(
                volumes,
                destino
            ),
            daemon=True
        ).start()

        return True


    def _salvar_exportar_worker(
        self,
        volumes,
        destino
    ):

        try:

            self._status_worker(
                "Gerando mix final..."
            )

            resposta = (
                self.motor.exportar_mix(
                    self.job_id,
                    volumes
                )
            )

            if not resposta.get(
                "ok"
            ):

                raise RuntimeError(
                    resposta.get(
                        "erro",
                        "Falha ao gerar mix final."
                    )
                )

            self._status_worker(
                "Baixando mix final..."
            )

            arquivo = (
                self.motor.baixar_mix(
                    self.job_id,
                    destino
                )
            )

            self.exportando = False

            self._status_worker(
                "Mix exportado com sucesso: "
                + str(
                    arquivo
                )
            )

        except Exception as exc:

            self.exportando = False

            mensagem = (
                "Falha ao exportar mix: "
                + str(
                    exc
                )
            )

            Clock.schedule_once(
                lambda dt, msg=mensagem:
                self.audio_error(
                    msg
                ),
                0
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
