from pathlib import Path

from kivy.utils import platform


class AndroidAudioEngine:

    REQUEST_AUDIO = 4817

    STEMS = (
        "voz",
        "bateria",
        "baixo",
        "outros",
    )

    def __init__(
        self,
        on_loaded=None,
        on_error=None
    ):

        self.on_loaded = on_loaded
        self.on_error = on_error

        self.available = (
            platform == "android"
        )

        self.player = None

        self.stem_players = {}

        self.current_uri = None
        self.current_name = None

        self._activity_module = None
        self._activity = None
        self.autoclass = None

        if not self.available:
            return

        try:
            from jnius import autoclass
            from android import activity

            self.autoclass = autoclass

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            self._activity = (
                PythonActivity.mActivity
            )

            self._activity_module = activity

            activity.bind(
                on_activity_result=
                self._on_activity_result
            )

        except Exception as exc:
            self.available = False
            self._erro(exc)


    # ======================================================
    # DIRETÓRIO PRIVADO DO APK
    # ======================================================

    @property
    def app_files_dir(self):

        if not self.available:
            return "."

        return str(
            self._activity
            .getFilesDir()
            .getAbsolutePath()
        )


    # ======================================================
    # SELETOR
    # ======================================================

    def open_picker(self):

        if not self.available:
            self._erro(
                "Seletor disponível somente no Android."
            )
            return False

        try:

            Intent = self.autoclass(
                "android.content.Intent"
            )

            intent = Intent(
                Intent.ACTION_OPEN_DOCUMENT
            )

            intent.addCategory(
                Intent.CATEGORY_OPENABLE
            )

            intent.setType(
                "audio/*"
            )

            intent.addFlags(
                Intent.FLAG_GRANT_READ_URI_PERMISSION
            )

            intent.addFlags(
                Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION
            )

            self._activity.startActivityForResult(
                intent,
                self.REQUEST_AUDIO
            )

            return True

        except Exception as exc:
            self._erro(exc)
            return False


    def _on_activity_result(
        self,
        request_code,
        result_code,
        intent
    ):

        if request_code != self.REQUEST_AUDIO:
            return

        if intent is None:
            return

        try:

            Activity = self.autoclass(
                "android.app.Activity"
            )

            if result_code != Activity.RESULT_OK:
                return

            uri = intent.getData()

            if uri is None:
                return

            self._persistir_permissao(
                uri
            )

            self.load_uri(
                uri
            )

        except Exception as exc:
            self._erro(exc)


    # ======================================================
    # ORIGINAL
    # ======================================================

    def load_uri(
        self,
        uri
    ):

        if not self.available:
            return False

        try:

            self._release_stems()
            self._release_player()

            MediaPlayer = self.autoclass(
                "android.media.MediaPlayer"
            )

            player = MediaPlayer()

            player.setDataSource(
                self._activity,
                uri
            )

            player.prepare()

            self.player = player
            self.current_uri = uri

            self.current_name = (
                self._get_display_name(uri)
                or
                str(uri.getLastPathSegment())
                or
                "Música"
            )

            duracao_ms = (
                self.duration_ms
            )

            if callable(
                self.on_loaded
            ):

                self.on_loaded(
                    self.current_name,
                    str(uri.toString()),
                    duracao_ms / 1000.0
                )

            return True

        except Exception as exc:
            self._erro(exc)
            return False


    # ======================================================
    # COPIAR MÚSICA SELECIONADA
    # ======================================================

    def copy_selected_audio_to(
        self,
        destino
    ):

        if (
            not self.available
            or self.current_uri is None
        ):
            raise RuntimeError(
                "Nenhuma música selecionada."
            )

        destino = Path(
            destino
        )

        destino.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        resolver = (
            self._activity
            .getContentResolver()
        )

        entrada = (
            resolver.openInputStream(
                self.current_uri
            )
        )

        if entrada is None:
            raise RuntimeError(
                "Não foi possível abrir a música."
            )

        buffer = bytearray(
            64 * 1024
        )

        try:

            with destino.open(
                "wb"
            ) as saida:

                while True:

                    quantidade = int(
                        entrada.read(
                            buffer
                        )
                    )

                    if quantidade <= 0:
                        break

                    saida.write(
                        buffer[:quantidade]
                    )

        finally:

            try:
                entrada.close()
            except Exception:
                pass

        if (
            not destino.exists()
            or destino.stat().st_size <= 0
        ):
            raise RuntimeError(
                "A cópia da música falhou."
            )

        return str(
            destino
        )


    # ======================================================
    # 4 STEMS
    # ======================================================

    def load_stems(
        self,
        caminhos
    ):

        if not self.available:
            return False

        try:

            self._release_stems()

            MediaPlayer = self.autoclass(
                "android.media.MediaPlayer"
            )

            novos = {}

            for stem in self.STEMS:

                caminho = caminhos.get(
                    stem
                )

                if not caminho:
                    raise RuntimeError(
                        f"Caminho ausente: {stem}"
                    )

                caminho = str(
                    Path(caminho)
                )

                if not Path(caminho).exists():

                    raise FileNotFoundError(
                        caminho
                    )

                player = MediaPlayer()

                player.setDataSource(
                    caminho
                )

                player.prepare()

                novos[stem] = player

            self.stem_players = novos

            if self.player is not None:

                try:
                    if self.player.isPlaying():
                        self.player.pause()
                except Exception:
                    pass

                try:
                    self.player.seekTo(0)
                except Exception:
                    pass

            return True

        except Exception as exc:

            self._release_stems()
            self._erro(exc)

            return False


    @property
    def stems_loaded(self):

        return (
            len(self.stem_players)
            == 4
        )


    def _master_player(self):

        if self.stems_loaded:

            return (
                self.stem_players.get(
                    "outros"
                )
                or
                next(
                    iter(
                        self.stem_players.values()
                    )
                )
            )

        return self.player


    def set_stem_volume(
        self,
        stem,
        volume
    ):

        player = self.stem_players.get(
            stem
        )

        if player is None:
            return False

        try:

            volume = max(
                0.0,
                min(
                    1.0,
                    float(volume)
                )
            )

            player.setVolume(
                volume,
                volume
            )

            return True

        except Exception as exc:
            self._erro(exc)
            return False


    def sync_stems(
        self,
        tolerancia_ms=120
    ):

        if not self.stems_loaded:
            return

        master = self._master_player()

        if master is None:
            return

        try:

            referencia = int(
                master.getCurrentPosition()
            )

            tocando = bool(
                master.isPlaying()
            )

            if not tocando:
                return

            for player in (
                self.stem_players.values()
            ):

                if player == master:
                    continue

                pos = int(
                    player.getCurrentPosition()
                )

                if abs(
                    pos - referencia
                ) > tolerancia_ms:

                    player.seekTo(
                        referencia
                    )

        except Exception:
            pass


    # ======================================================
    # PLAYER
    # ======================================================

    def play(self):

        try:

            if self.stems_loaded:

                master = self._master_player()

                pos = int(
                    master.getCurrentPosition()
                )

                for player in (
                    self.stem_players.values()
                ):
                    player.seekTo(
                        pos
                    )

                for player in (
                    self.stem_players.values()
                ):
                    player.start()

                return True

            if self.player is None:
                return False

            self.player.start()

            return True

        except Exception as exc:
            self._erro(exc)
            return False


    def pause(self):

        try:

            if self.stems_loaded:

                for player in (
                    self.stem_players.values()
                ):

                    if player.isPlaying():
                        player.pause()

                return True

            if self.player is None:
                return False

            if self.player.isPlaying():
                self.player.pause()

            return True

        except Exception as exc:
            self._erro(exc)
            return False


    def play_pause(self):

        if self.is_playing:
            return self.pause()

        return self.play()


    def stop(self):

        try:

            if self.stems_loaded:

                for player in (
                    self.stem_players.values()
                ):

                    if player.isPlaying():
                        player.pause()

                    player.seekTo(0)

                return True

            if self.player is None:
                return False

            if self.player.isPlaying():
                self.player.pause()

            self.player.seekTo(0)

            return True

        except Exception as exc:
            self._erro(exc)
            return False


    def seek_to(
        self,
        milliseconds
    ):

        try:

            destino = max(
                0,
                int(milliseconds)
            )

            duracao = (
                self.duration_ms
            )

            if duracao > 0:

                destino = min(
                    destino,
                    duracao
                )

            if self.stems_loaded:

                for player in (
                    self.stem_players.values()
                ):

                    player.seekTo(
                        destino
                    )

                return True

            if self.player is None:
                return False

            self.player.seekTo(
                destino
            )

            return True

        except Exception as exc:
            self._erro(exc)
            return False


    # ======================================================
    # ESTADO
    # ======================================================

    @property
    def is_loaded(self):

        return (
            self.stems_loaded
            or
            self.player is not None
        )


    @property
    def is_playing(self):

        player = self._master_player()

        if player is None:
            return False

        try:
            return bool(
                player.isPlaying()
            )
        except Exception:
            return False


    @property
    def position_ms(self):

        player = self._master_player()

        if player is None:
            return 0

        try:
            return max(
                0,
                int(
                    player.getCurrentPosition()
                )
            )
        except Exception:
            return 0


    @property
    def duration_ms(self):

        player = self._master_player()

        if player is None:
            return 0

        try:
            return max(
                0,
                int(
                    player.getDuration()
                )
            )
        except Exception:
            return 0


    # ======================================================
    # URI
    # ======================================================

    def _persistir_permissao(
        self,
        uri
    ):

        try:

            Intent = self.autoclass(
                "android.content.Intent"
            )

            resolver = (
                self._activity
                .getContentResolver()
            )

            resolver.takePersistableUriPermission(
                uri,
                Intent.FLAG_GRANT_READ_URI_PERMISSION
            )

        except Exception:
            pass


    def _get_display_name(
        self,
        uri
    ):

        try:

            OpenableColumns = (
                self.autoclass(
                    "android.provider.OpenableColumns"
                )
            )

            resolver = (
                self._activity
                .getContentResolver()
            )

            cursor = resolver.query(
                uri,
                None,
                None,
                None,
                None
            )

            if cursor is None:
                return None

            try:

                if not cursor.moveToFirst():
                    return None

                indice = (
                    cursor.getColumnIndex(
                        OpenableColumns.DISPLAY_NAME
                    )
                )

                if indice < 0:
                    return None

                return str(
                    cursor.getString(
                        indice
                    )
                )

            finally:
                cursor.close()

        except Exception:
            return None


    # ======================================================
    # RELEASE
    # ======================================================

    def _release_stems(self):

        for player in (
            self.stem_players.values()
        ):

            try:
                player.release()
            except Exception:
                pass

        self.stem_players = {}


    def _release_player(self):

        if self.player is None:
            return

        try:
            self.player.release()
        except Exception:
            pass

        self.player = None


    def release(self):

        self._release_stems()
        self._release_player()

        if self._activity_module:

            try:
                self._activity_module.unbind(
                    on_activity_result=
                    self._on_activity_result
                )
            except Exception:
                pass


    # ======================================================
    # ERRO
    # ======================================================

    def _erro(
        self,
        erro
    ):

        mensagem = str(
            erro
        )

        print(
            "CROGER MIXER AUDIO:",
            mensagem
        )

        if callable(
            self.on_error
        ):

            self.on_error(
                mensagem
            )
