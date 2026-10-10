from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.slider import Slider
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget

from mixer_controller import MixerController
from android_audio import AndroidAudioEngine


# ==========================================================
# CORES
# ==========================================================

BG = (0.018, 0.039, 0.075, 1)
CARD = (0.035, 0.071, 0.125, 1)
CARD_2 = (0.045, 0.09, 0.16, 1)

BORDER = (0.10, 0.23, 0.39, 1)

WHITE = (0.96, 0.98, 1.0, 1)
TEXT_2 = (0.62, 0.70, 0.84, 1)

CYAN = (0.10, 0.72, 1.00, 1)
BLUE = (0.12, 0.35, 1.00, 1)
PURPLE = (0.55, 0.12, 1.00, 1)
PINK = (1.00, 0.18, 0.78, 1)

Window.clearcolor = BG


# ==========================================================
# UTILIDADES
# ==========================================================

def tempo_texto(segundos):

    try:
        segundos = max(0, int(segundos))
    except Exception:
        segundos = 0

    minutos = segundos // 60
    segundos = segundos % 60

    return f"{minutos:02d}:{segundos:02d}"


def cor_hex(cor):

    r = int(cor[0] * 255)
    g = int(cor[1] * 255)
    b = int(cor[2] * 255)

    return f"{r:02x}{g:02x}{b:02x}"


# ==========================================================
# CARD
# ==========================================================

class Card(BoxLayout):

    def __init__(
        self,
        radius=18,
        bg_color=CARD,
        border_color=BORDER,
        **kwargs
    ):

        super().__init__(**kwargs)

        self.radius = dp(radius)

        with self.canvas.before:

            self._bg_color = Color(
                *bg_color
            )

            self._bg = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[self.radius]
            )

            self._border_color = Color(
                *border_color
            )

            self._border = Line(
                rounded_rectangle=(
                    self.x,
                    self.y,
                    self.width,
                    self.height,
                    self.radius
                ),
                width=1
            )

        self.bind(
            pos=self._update_canvas,
            size=self._update_canvas
        )


    def _update_canvas(self, *args):

        self._bg.pos = self.pos
        self._bg.size = self.size

        self._border.rounded_rectangle = (
            self.x,
            self.y,
            self.width,
            self.height,
            self.radius
        )


# ==========================================================
# BOTÃO
# ==========================================================

class MixerButton(Button):

    def __init__(
        self,
        bg=CARD_2,
        fg=WHITE,
        radius=12,
        **kwargs
    ):

        super().__init__(**kwargs)

        self.background_normal = ""
        self.background_down = ""

        self.background_color = bg
        self.color = fg

        self.border = (0, 0, 0, 0)

        self.font_size = "14sp"


# ==========================================================
# TÍTULO DE SEÇÃO
# ==========================================================

class SectionHeader(BoxLayout):

    def __init__(
        self,
        icon,
        title,
        subtitle,
        accent=CYAN,
        **kwargs
    ):

        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(52),
            spacing=dp(9),
            **kwargs
        )

        lbl_icon = Label(
            text=icon,
            size_hint_x=None,
            width=dp(38),
            font_size="25sp",
            color=accent
        )

        textos = BoxLayout(
            orientation="vertical"
        )

        titulo = Label(
            text=f"[b]{title}[/b]",
            markup=True,
            halign="left",
            valign="middle",
            font_size="16sp",
            color=WHITE
        )

        subtitulo = Label(
            text=subtitle,
            halign="left",
            valign="middle",
            font_size="11sp",
            color=TEXT_2
        )

        for lbl in (
            titulo,
            subtitulo
        ):
            lbl.bind(
                size=lambda obj, size:
                setattr(
                    obj,
                    "text_size",
                    size
                )
            )

        textos.add_widget(
            titulo
        )

        textos.add_widget(
            subtitulo
        )

        self.add_widget(
            lbl_icon
        )

        self.add_widget(
            textos
        )


# ==========================================================
# CHIP
# ==========================================================

class InfoChip(Card):

    def __init__(
        self,
        title,
        value,
        accent=CYAN,
        **kwargs
    ):

        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(45),
            padding=dp(8),
            radius=11,
            bg_color=CARD_2,
            **kwargs
        )

        self.lbl = Label(
            text=(
                f"[color=#{cor_hex(TEXT_2)}]"
                f"{title}: [/color]"
                f"[b][color=#{cor_hex(accent)}]"
                f"{value}"
                f"[/color][/b]"
            ),
            markup=True,
            font_size="12sp"
        )

        self.add_widget(
            self.lbl
        )


    def set_value(
        self,
        title,
        value,
        accent=CYAN
    ):

        self.lbl.text = (
            f"[color=#{cor_hex(TEXT_2)}]"
            f"{title}: [/color]"
            f"[b][color=#{cor_hex(accent)}]"
            f"{value}"
            f"[/color][/b]"
        )


# ==========================================================
# LINHA DO MIXER
# ==========================================================

class StemRow(Card):

    def __init__(
        self,
        controller,
        stem,
        nome,
        icon,
        accent,
        **kwargs
    ):

        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(64),
            spacing=dp(7),
            padding=(
                dp(8),
                dp(5)
            ),
            radius=11,
            bg_color=CARD_2,
            **kwargs
        )

        self.controller = controller
        self.stem = stem
        self.accent = accent

        self.lbl_icon = Label(
            text=icon,
            size_hint_x=None,
            width=dp(34),
            font_size="23sp",
            color=accent
        )

        self.lbl_nome = Label(
            text=f"[b]{nome}[/b]",
            markup=True,
            size_hint_x=None,
            width=dp(70),
            font_size="13sp",
            color=WHITE
        )

        self.slider = Slider(
            min=0,
            max=1.0,
            value=(
                controller
                .stems[stem]["volume"]
            ),
            step=0.01
        )

        self.slider.value_track = True
        self.slider.value_track_color = accent
        self.slider.cursor_size = (
            dp(20),
            dp(20)
        )

        self.lbl_percent = Label(
            text="100%",
            size_hint_x=None,
            width=dp(50),
            color=accent,
            font_size="13sp"
        )

        self.btn_mute = ToggleButton(
            text="MUDO",
            size_hint_x=None,
            width=dp(68),
            background_normal="",
            background_down="",
            background_color=CARD,
            color=WHITE,
            font_size="10sp"
        )

        self.btn_solo = ToggleButton(
            text="SOLO",
            size_hint_x=None,
            width=dp(65),
            background_normal="",
            background_down="",
            background_color=CARD,
            color=WHITE,
            font_size="10sp"
        )

        self.slider.bind(
            value=self._volume
        )

        self.btn_mute.bind(
            on_release=self._mute
        )

        self.btn_solo.bind(
            on_release=self._solo
        )

        self.add_widget(
            self.lbl_icon
        )

        self.add_widget(
            self.lbl_nome
        )

        self.add_widget(
            self.slider
        )

        self.add_widget(
            self.lbl_percent
        )

        self.add_widget(
            self.btn_mute
        )

        self.add_widget(
            self.btn_solo
        )

        self.refresh()


    def _volume(
        self,
        instance,
        value
    ):

        self.controller.set_volume(
            self.stem,
            value
        )


    def _mute(
        self,
        *args
    ):

        self.controller.toggle_mute(
            self.stem
        )


    def _solo(
        self,
        *args
    ):

        self.controller.toggle_solo(
            self.stem
        )


    def refresh(self):

        dados = self.controller.stems[
            self.stem
        ]

        valor = dados["volume"]

        if abs(
            self.slider.value - valor
        ) > 0.001:

            self.slider.value = valor

        self.lbl_percent.text = (
            f"{int(valor * 100)}%"
        )

        self.btn_mute.state = (
            "down"
            if dados["mute"]
            else "normal"
        )

        self.btn_solo.state = (
            "down"
            if dados["solo"]
            else "normal"
        )

        self.btn_mute.background_color = (
            PURPLE
            if dados["mute"]
            else CARD
        )

        self.btn_solo.background_color = (
            BLUE
            if dados["solo"]
            else CARD
        )


# ==========================================================
# TELA PRINCIPAL
# ==========================================================

class CrogerMixerScreen(
    ScrollView
):

    def __init__(
        self,
        controller,
        **kwargs
    ):

        super().__init__(**kwargs)

        self.controller = controller

        self.audio_engine = AndroidAudioEngine(
            on_loaded=self.controller.audio_loaded,
            on_error=self.controller.audio_error
        )

        self.controller.attach_audio_engine(
            self.audio_engine
        )

        self.do_scroll_x = False

        self.content = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(12),
            padding=dp(10)
        )

        self.content.bind(
            minimum_height=
            self.content.setter(
                "height"
            )
        )

        self.add_widget(
            self.content
        )

        self._build_header()
        self._build_player()
        self._build_mixer()
        self._build_analysis()
        self._build_rhythm_transpose()
        self._build_metronome()
        self._build_bottom()

        self.controller.on_change = (
            self.refresh_from_controller
        )

        self.refresh_from_controller()

        Clock.schedule_interval(
            self._tick,
            0.25
        )


    # ======================================================
    # CABEÇALHO
    # ======================================================

    def _build_header(self):

        header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(72),
            spacing=dp(8)
        )

        menu = MixerButton(
            text="☰",
            size_hint_x=None,
            width=dp(48),
            bg=BG,
            font_size="26sp"
        )

        logo = Image(
            source="icon.png",
            size_hint_x=None,
            width=dp(58)
        )

        textos = BoxLayout(
            orientation="vertical"
        )

        titulo = Label(
            text=(
                "[b]CROGER "
                f"[color=#{cor_hex(CYAN)}]"
                "MIXER"
                "[/color][/b]"
            ),
            markup=True,
            halign="left",
            valign="bottom",
            font_size="25sp",
            color=WHITE
        )

        subtitulo = Label(
            text=(
                "Separação, análise e "
                "transposição musical"
            ),
            halign="left",
            valign="top",
            font_size="11sp",
            color=TEXT_2
        )

        titulo.bind(
            size=lambda obj, size:
            setattr(
                obj,
                "text_size",
                size
            )
        )

        subtitulo.bind(
            size=lambda obj, size:
            setattr(
                obj,
                "text_size",
                size
            )
        )

        textos.add_widget(
            titulo
        )

        textos.add_widget(
            subtitulo
        )

        config = MixerButton(
            text="⚙",
            size_hint_x=None,
            width=dp(50),
            bg=BG,
            font_size="25sp"
        )

        header.add_widget(
            menu
        )

        header.add_widget(
            logo
        )

        header.add_widget(
            textos
        )

        header.add_widget(
            config
        )

        self.content.add_widget(
            header
        )


    # ======================================================
    # PLAYER
    # ======================================================

    def _build_player(self):

        card = Card(
            orientation="vertical",
            size_hint_y=None,
            height=dp(330),
            padding=dp(12),
            spacing=dp(6)
        )

        top = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(95),
            spacing=dp(10)
        )

        self.cover = Image(
            source="icon.png",
            size_hint_x=None,
            width=dp(92)
        )

        infos = BoxLayout(
            orientation="vertical"
        )

        self.lbl_music = Label(
            text="Nenhuma música selecionada",
            halign="left",
            valign="middle",
            font_size="20sp",
            bold=True,
            color=WHITE
        )

        self.lbl_music.bind(
            size=lambda obj, size:
            setattr(
                obj,
                "text_size",
                size
            )
        )

        self.lbl_status = Label(
            text=(
                "Selecione uma música "
                "para iniciar"
            ),
            halign="left",
            valign="top",
            font_size="12sp",
            color=TEXT_2
        )

        self.lbl_status.bind(
            size=lambda obj, size:
            setattr(
                obj,
                "text_size",
                size
            )
        )

        infos.add_widget(
            self.lbl_music
        )

        infos.add_widget(
            self.lbl_status
        )

        top.add_widget(
            self.cover
        )

        top.add_widget(
            infos
        )

        self.btn_selecionar = MixerButton(
            text="⋮",
            size_hint_x=None,
            width=dp(42),
            bg=CARD,
            font_size="26sp"
        )

        self.btn_selecionar.bind(
            on_release=lambda *_:
            self.controller.selecionar_musica()
        )

        top.add_widget(
            self.btn_selecionar
        )

        card.add_widget(
            top
        )

        chips = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            spacing=dp(8)
        )

        self.chip_tom = InfoChip(
            "Tom",
            "--"
        )

        self.chip_bpm = InfoChip(
            "BPM",
            "--",
            PURPLE
        )

        self.chip_compasso = InfoChip(
            "Compasso",
            "--"
        )

        chips.add_widget(
            self.chip_tom
        )

        chips.add_widget(
            self.chip_bpm
        )

        chips.add_widget(
            self.chip_compasso
        )

        card.add_widget(
            chips
        )

        self.slider_position = Slider(
            min=0,
            max=1,
            value=0,
            size_hint_y=None,
            height=dp(34)
        )

        self.slider_position.value_track = True
        self.slider_position.value_track_color = CYAN

        self.slider_position.bind(
            on_touch_up=
            self._seek_from_slider
        )

        card.add_widget(
            self.slider_position
        )

        tempos = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(25)
        )

        self.lbl_position = Label(
            text="00:00",
            halign="left",
            color=TEXT_2
        )

        self.lbl_duration = Label(
            text="00:00",
            halign="right",
            color=TEXT_2
        )

        tempos.add_widget(
            self.lbl_position
        )

        tempos.add_widget(
            self.lbl_duration
        )

        card.add_widget(
            tempos
        )

        controls = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(92),
            spacing=dp(8)
        )

        btn_shuffle = MixerButton(
            text="⤨",
            bg=CARD,
            font_size="23sp"
        )

        btn_back = MixerButton(
            text="|◀",
            bg=CARD,
            font_size="22sp"
        )

        self.btn_play = MixerButton(
            text="▶",
            bg=BLUE,
            font_size="32sp"
        )

        btn_next = MixerButton(
            text="▶|",
            bg=CARD,
            font_size="22sp"
        )

        btn_stop = MixerButton(
            text="■",
            bg=CARD,
            font_size="22sp"
        )

        btn_repeat = MixerButton(
            text="↻",
            bg=CARD,
            font_size="24sp"
        )

        btn_back.bind(
            on_release=lambda *_:
            self.controller.voltar(10)
        )

        self.btn_play.bind(
            on_release=lambda *_:
            self.controller.play_pause()
        )

        btn_next.bind(
            on_release=lambda *_:
            self.controller.avancar(10)
        )

        btn_stop.bind(
            on_release=lambda *_:
            self.controller.parar()
        )

        for btn in (
            btn_shuffle,
            btn_back,
            self.btn_play,
            btn_next,
            btn_stop,
            btn_repeat
        ):

            controls.add_widget(
                btn
            )

        card.add_widget(
            controls
        )

        self.content.add_widget(
            card
        )


    # ======================================================
    # MIXER
    # ======================================================

    def _build_mixer(self):

        card = Card(
            orientation="vertical",
            size_hint_y=None,
            height=dp(355),
            padding=dp(10),
            spacing=dp(6)
        )

        card.add_widget(
            SectionHeader(
                "▥",
                "MIXER DE ÁUDIO",
                (
                    "Ajuste o volume de cada "
                    "elemento da música"
                )
            )
        )

        self.stem_rows = {}

        dados = (
            (
                "voz",
                "Voz",
                "●",
                CYAN
            ),
            (
                "bateria",
                "Bateria",
                "◉",
                PURPLE
            ),
            (
                "baixo",
                "Baixo",
                "◆",
                CYAN
            ),
            (
                "outros",
                "Outros",
                "♪",
                PINK
            ),
        )

        for (
            stem,
            nome,
            icon,
            accent
        ) in dados:

            row = StemRow(
                self.controller,
                stem,
                nome,
                icon,
                accent
            )

            self.stem_rows[
                stem
            ] = row

            card.add_widget(
                row
            )

        self.content.add_widget(
            card
        )


    # ======================================================
    # ANÁLISE / ACORDES
    # ======================================================

    def _build_analysis(self):

        linha = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(190),
            spacing=dp(10)
        )

        harmonica = Card(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(5)
        )

        harmonica.add_widget(
            SectionHeader(
                "▥",
                "ANÁLISE HARMÔNICA",
                "Campo harmônico da música",
                PURPLE
            )
        )

        self.harmonic_box = BoxLayout(
            orientation="horizontal",
            spacing=dp(4)
        )

        self.harmonic_labels = []

        for _ in range(7):

            lbl = MixerButton(
                text="--",
                bg=CARD_2,
                fg=CYAN,
                font_size="12sp"
            )

            self.harmonic_labels.append(
                lbl
            )

            self.harmonic_box.add_widget(
                lbl
            )

        harmonica.add_widget(
            self.harmonic_box
        )

        acordes = Card(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(5)
        )

        acordes.add_widget(
            SectionHeader(
                "♪",
                "ACORDES EM TEMPO REAL",
                "Acorde atual e próximos",
                PURPLE
            )
        )

        linha_atual = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(46)
        )

        linha_atual.add_widget(
            Label(
                text="Acorde atual:",
                color=TEXT_2,
                font_size="12sp"
            )
        )

        self.lbl_acorde = MixerButton(
            text="--",
            bg=PURPLE,
            font_size="18sp"
        )

        linha_atual.add_widget(
            self.lbl_acorde
        )

        acordes.add_widget(
            linha_atual
        )

        self.lbl_proximos = Label(
            text="-- | -- | -- | --",
            color=WHITE,
            font_size="13sp"
        )

        acordes.add_widget(
            self.lbl_proximos
        )

        linha.add_widget(
            harmonica
        )

        linha.add_widget(
            acordes
        )

        self.content.add_widget(
            linha
        )


    # ======================================================
    # RITMO / TRANSPOSIÇÃO
    # ======================================================

    def _build_rhythm_transpose(
        self
    ):

        linha = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(190),
            spacing=dp(10)
        )

        ritmo = Card(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(5)
        )

        ritmo.add_widget(
            SectionHeader(
                "◉",
                "COMPASSO E RITMO",
                "Posição atual na música",
                CYAN
            )
        )

        stats = BoxLayout(
            orientation="horizontal",
            spacing=dp(6)
        )

        self.lbl_compasso_num = (
            MixerButton(
                text="Compasso\n0",
                bg=CARD_2,
                font_size="13sp"
            )
        )

        self.lbl_tempo_num = (
            MixerButton(
                text="Tempo\n0",
                bg=CARD_2,
                font_size="13sp"
            )
        )

        self.lbl_batidas = (
            MixerButton(
                text="○ ○ ○ ○",
                bg=CARD_2,
                fg=CYAN,
                font_size="20sp"
            )
        )

        stats.add_widget(
            self.lbl_compasso_num
        )

        stats.add_widget(
            self.lbl_tempo_num
        )

        stats.add_widget(
            self.lbl_batidas
        )

        ritmo.add_widget(
            stats
        )

        transpose = Card(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(5)
        )

        topo_trans = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(52)
        )

        topo_trans.add_widget(
            SectionHeader(
                "↕",
                "TRANSPOSIÇÃO",
                "Altere o tom da música",
                CYAN
            )
        )

        self.lbl_novo_tom = Label(
            text="Novo tom:\n--",
            color=CYAN,
            font_size="12sp",
            size_hint_x=None,
            width=dp(83)
        )

        topo_trans.add_widget(
            self.lbl_novo_tom
        )

        transpose.add_widget(
            topo_trans
        )

        self.transpose_buttons = {}

        transp_row = BoxLayout(
            orientation="horizontal",
            spacing=dp(5)
        )

        for semitons in (
            -2,
            -1,
            0,
            1,
            2
        ):

            txt = (
                f"+{semitons}"
                if semitons > 0
                else str(semitons)
            )

            btn = MixerButton(
                text=txt,
                bg=CARD_2
            )

            btn.bind(
                on_release=(
                    lambda _btn,
                    s=semitons:
                    self.controller
                    .set_transposicao(s)
                )
            )

            self.transpose_buttons[
                semitons
            ] = btn

            transp_row.add_widget(
                btn
            )

        transpose.add_widget(
            transp_row
        )

        linha.add_widget(
            ritmo
        )

        linha.add_widget(
            transpose
        )

        self.content.add_widget(
            linha
        )


    # ======================================================
    # METRÔNOMO
    # ======================================================

    def _build_metronome(self):

        card = Card(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(90),
            padding=dp(10),
            spacing=dp(8)
        )

        card.add_widget(
            Label(
                text="♩",
                color=WHITE,
                font_size="31sp",
                size_hint_x=None,
                width=dp(45)
            )
        )

        textos = BoxLayout(
            orientation="vertical"
        )

        titulo = Label(
            text="[b]METRÔNOMO[/b]",
            markup=True,
            halign="left",
            font_size="16sp",
            color=WHITE
        )

        subtitulo = Label(
            text=(
                "Mantenha o tempo "
                "durante seus estudos"
            ),
            halign="left",
            font_size="11sp",
            color=TEXT_2
        )

        titulo.bind(
            size=lambda obj, size:
            setattr(
                obj,
                "text_size",
                size
            )
        )

        subtitulo.bind(
            size=lambda obj, size:
            setattr(
                obj,
                "text_size",
                size
            )
        )

        textos.add_widget(
            titulo
        )

        textos.add_widget(
            subtitulo
        )

        card.add_widget(
            textos
        )

        self.btn_metronomo = (
            MixerButton(
                text="OFF",
                size_hint_x=None,
                width=dp(80),
                bg=CARD_2
            )
        )

        self.btn_metronomo.bind(
            on_release=lambda *_:
            self.controller
            .toggle_metronomo()
        )

        card.add_widget(
            self.btn_metronomo
        )

        self.lbl_metronomo_bpm = Label(
            text="BPM: --",
            size_hint_x=None,
            width=dp(78),
            color=CYAN,
            font_size="13sp"
        )

        card.add_widget(
            self.lbl_metronomo_bpm
        )

        self.content.add_widget(
            card
        )


    # ======================================================
    # BOTÕES FINAIS
    # ======================================================

    def _build_bottom(self):

        linha = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(96),
            spacing=dp(10)
        )

        btn_analisar = MixerButton(
            text=(
                "▥  ANALISAR E MIXAR\n"
                "Separar, analisar e processar"
            ),
            bg=PURPLE,
            font_size="15sp"
        )

        btn_salvar = MixerButton(
            text=(
                "↓  SALVAR / EXPORTAR\n"
                "Salvar projeto ou exportar áudio"
            ),
            bg=CARD,
            font_size="14sp"
        )

        btn_analisar.bind(
            on_release=lambda *_:
            self.controller
            .analisar_e_mixar()
        )

        btn_salvar.bind(
            on_release=lambda *_:
            self.controller
            .salvar_exportar()
        )

        linha.add_widget(
            btn_analisar
        )

        linha.add_widget(
            btn_salvar
        )

        self.content.add_widget(
            linha
        )

        self.content.add_widget(
            Widget(
                size_hint_y=None,
                height=dp(20)
            )
        )


    # ======================================================
    # EVENTOS
    # ======================================================

    def _seek_from_slider(
        self,
        slider,
        touch
    ):

        if not slider.collide_point(
            *touch.pos
        ):
            return

        duracao = self.controller.duration

        if duracao <= 0:
            return

        self.controller.seek(
            slider.value * duracao
        )


    def _tick(
        self,
        dt
    ):

        self.controller.sync_audio_state()

        self.refresh_from_controller()


    # ======================================================
    # ATUALIZAÇÃO
    # ======================================================

    def refresh_player_only(self):

        c = self.controller

        self.lbl_position.text = (
            tempo_texto(
                c.position
            )
        )

        self.lbl_duration.text = (
            tempo_texto(
                c.duration
            )
        )

        if c.duration > 0:

            valor = (
                c.position /
                c.duration
            )

            self.slider_position.value = (
                max(
                    0,
                    min(
                        1,
                        valor
                    )
                )
            )

        else:

            self.slider_position.value = 0


    def refresh_from_controller(
        self
    ):

        c = self.controller

        self.lbl_music.text = (
            c.music_name
        )

        if c.last_error:

            self.lbl_status.text = (
                "Erro: "
                + c.last_error
            )

        elif c.music_path:

            self.lbl_status.text = (
                "Música carregada • "
                "Pronta para análise"
            )

        else:

            self.lbl_status.text = (
                "Selecione uma música "
                "para iniciar"
            )

        self.btn_play.text = (
            "Ⅱ"
            if c.playing
            else "▶"
        )

        self.chip_tom.set_value(
            "Tom",
            c.tonalidade
        )

        self.chip_bpm.set_value(
            "BPM",
            (
                str(c.bpm)
                if c.bpm
                else "--"
            ),
            PURPLE
        )

        self.chip_compasso.set_value(
            "Compasso",
            c.compasso
        )

        self.refresh_player_only()

        for row in (
            self.stem_rows.values()
        ):
            row.refresh()

        for indice, lbl in enumerate(
            self.harmonic_labels
        ):

            if indice < len(
                c.campo_harmonico
            ):
                lbl.text = (
                    c.campo_harmonico[
                        indice
                    ]
                )
            else:
                lbl.text = "--"

        self.lbl_acorde.text = (
            c.acorde_atual
        )

        self.lbl_proximos.text = (
            "  |  ".join(
                c.proximos_acordes
            )
            if c.proximos_acordes
            else "-- | -- | -- | --"
        )

        self.lbl_compasso_num.text = (
            "Compasso\n"
            f"{c.numero_compasso}"
        )

        self.lbl_tempo_num.text = (
            "Tempo\n"
            f"{c.tempo_compasso}"
        )

        total_tempos = 4

        try:
            if "/" in c.compasso:
                total_tempos = int(
                    c.compasso.split(
                        "/"
                    )[0]
                )
        except Exception:
            total_tempos = 4

        total_tempos = max(
            1,
            min(
                total_tempos,
                12
            )
        )

        pontos = []

        for i in range(
            1,
            total_tempos + 1
        ):

            if (
                c.tempo_compasso
                and
                i <= c.tempo_compasso
            ):
                pontos.append("●")
            else:
                pontos.append("○")

        self.lbl_batidas.text = (
            " ".join(pontos)
        )

        for semitons, btn in (
            self.transpose_buttons.items()
        ):

            btn.background_color = (
                PURPLE
                if (
                    semitons ==
                    c.transposicao
                )
                else CARD_2
            )

        self.lbl_novo_tom.text = (
            "Novo tom:\n"
            f"{self._tom_transposto()}"
        )

        self.btn_metronomo.text = (
            "ON"
            if c.metronomo_ligado
            else "OFF"
        )

        self.btn_metronomo.background_color = (
            PURPLE
            if c.metronomo_ligado
            else CARD_2
        )

        self.lbl_metronomo_bpm.text = (
            "BPM: "
            + (
                str(c.bpm)
                if c.bpm
                else "--"
            )
        )


    def _tom_transposto(self):

        texto = self.controller.tonalidade

        if (
            not texto
            or texto == "--"
        ):
            return "--"

        partes = texto.split()

        nota = partes[0]

        qualidade = (
            " ".join(
                partes[1:]
            )
        )

        notas = [
            "C",
            "C#",
            "D",
            "D#",
            "E",
            "F",
            "F#",
            "G",
            "G#",
            "A",
            "A#",
            "B"
        ]

        equivalencias = {
            "Db": "C#",
            "Eb": "D#",
            "Gb": "F#",
            "Ab": "G#",
            "Bb": "A#"
        }

        base = equivalencias.get(
            nota,
            nota
        )

        if base not in notas:
            return texto

        indice = notas.index(
            base
        )

        novo = notas[
            (
                indice
                +
                self.controller
                .transposicao
            )
            % 12
        ]

        if qualidade:
            return (
                novo
                + " "
                + qualidade
            )

        return novo


# ==========================================================
# APP
# ==========================================================

class CrogerMixerApp(App):

    title = "CROGER MIXER"

    def build(self):

        self.controller = (
            MixerController()
        )

        return CrogerMixerScreen(
            self.controller
        )


    def on_stop(self):

        if hasattr(
            self,
            "controller"
        ):
            self.controller.release()


if __name__ == "__main__":

    CrogerMixerApp().run()
