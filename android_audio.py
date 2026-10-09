from kivy.utils import platform


class AndroidAudioEngine:

    REQUEST_AUDIO = 4817

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
        self.current_uri = None
        self.current_name = None

        self._activity_module = None
        self._activity = None

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


    # =====================================================
    # SELETOR DE MÚSICA
    # =====================================================

    def open_picker(self):

        if not self.available:
            self._erro(
                "Seletor disponível somente "
                "no Android."
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

            self._persistir_permissao(uri)

            self.load_uri(uri)

        except Exception as exc:
            self._erro(exc)


    # =====================================================
    # CARREGAMENTO
    # =====================================================

    def load_uri(self, uri):

        if not self.available:
            return False

        try:
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
                str(
                    uri.getLastPathSegment()
                )
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


    # =====================================================
    # PLAYER
    # =====================================================

    def play(self):

        if self.player is None:
            return False

        try:
            self.player.start()
            return True

        except Exception as exc:
            self._erro(exc)
            return False


    def pause(self):

        if self.player is None:
            return False

        try:
            if self.player.isPlaying():
                self.player.pause()

            return True

        except Exception as exc:
            self._erro(exc)
            return False


    def play_pause(self):

        if self.player is None:
            return False

        try:
            if self.player.isPlaying():
                self.player.pause()
            else:
                self.player.start()

            return True

        except Exception as exc:
            self._erro(exc)
            return False


    def stop(self):

        if self.player is None:
            return False

        try:
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

        if self.player is None:
            return False

        try:
            destino = int(
                max(
                    0,
                    milliseconds
                )
            )

            duracao = self.duration_ms

            if duracao > 0:
                destino = min(
                    destino,
                    duracao
                )

            self.player.seekTo(
                destino
            )

            return True

        except Exception as exc:
            self._erro(exc)
            return False


    # =====================================================
    # ESTADO
    # =====================================================

    @property
    def is_loaded(self):

        return (
            self.player is not None
        )


    @property
    def is_playing(self):

        if self.player is None:
            return False

        try:
            return bool(
                self.player.isPlaying()
            )

        except Exception:
            return False


    @property
    def position_ms(self):

        if self.player is None:
            return 0

        try:
            return max(
                0,
                int(
                    self.player
                    .getCurrentPosition()
                )
            )

        except Exception:
            return 0


    @property
    def duration_ms(self):

        if self.player is None:
            return 0

        try:
            return max(
                0,
                int(
                    self.player.getDuration()
                )
            )

        except Exception:
            return 0


    # =====================================================
    # URI / NOME
    # =====================================================

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


    # =====================================================
    # FINALIZAÇÃO
    # =====================================================

    def _release_player(self):

        if self.player is None:
            return

        try:
            self.player.release()
        except Exception:
            pass

        self.player = None


    def release(self):

        self._release_player()

        if self._activity_module:

            try:
                self._activity_module.unbind(
                    on_activity_result=
                    self._on_activity_result
                )
            except Exception:
                pass


    # =====================================================
    # ERRO
    # =====================================================

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
