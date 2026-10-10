import json
import http.client
import urllib.error
import urllib.request
from pathlib import Path


class CrogerMotorClient:

    def __init__(
        self,
        host="127.0.0.1",
        port=8765,
        timeout=10
    ):

        self.host = host
        self.port = int(port)
        self.timeout = timeout

        self.base_url = (
            f"http://{self.host}:{self.port}"
        )


    # ======================================================
    # HTTP JSON
    # ======================================================

    def _get_json(
        self,
        caminho,
        timeout=None
    ):

        url = (
            self.base_url
            + caminho
        )

        with urllib.request.urlopen(
            url,
            timeout=(
                timeout
                or self.timeout
            )
        ) as resposta:

            return json.loads(
                resposta.read()
                .decode("utf-8")
            )


    def _post_json(
        self,
        caminho,
        dados,
        timeout=None
    ):

        corpo = json.dumps(
            dados,
            ensure_ascii=False
        ).encode("utf-8")

        requisicao = (
            urllib.request.Request(
                self.base_url + caminho,
                data=corpo,
                headers={
                    "Content-Type":
                    "application/json"
                },
                method="POST"
            )
        )

        with urllib.request.urlopen(
            requisicao,
            timeout=(
                timeout
                or self.timeout
            )
        ) as resposta:

            return json.loads(
                resposta.read()
                .decode("utf-8")
            )


    # ======================================================
    # MOTOR
    # ======================================================

    def health(self):

        return self._get_json(
            "/health"
        )


    def state(self):

        return self._get_json(
            "/state"
        )


    def job(
        self,
        job_id
    ):

        return self._get_json(
            f"/job/{job_id}"
        )


    def iniciar_separacao_por_nome(
        self,
        filename
    ):

        return self._post_json(
            "/separate",
            {
                "filename": filename
            }
        )


    # ======================================================
    # UPLOAD
    # ======================================================

    def upload_file(
        self,
        caminho,
        filename=None,
        progresso=None
    ):

        caminho = Path(
            caminho
        )

        if not caminho.exists():
            raise FileNotFoundError(
                str(caminho)
            )

        tamanho = (
            caminho.stat().st_size
        )

        nome = (
            filename
            or caminho.name
        )

        conexao = (
            http.client.HTTPConnection(
                self.host,
                self.port,
                timeout=120
            )
        )

        enviado = 0

        try:

            conexao.putrequest(
                "POST",
                "/upload"
            )

            conexao.putheader(
                "Content-Length",
                str(tamanho)
            )

            conexao.putheader(
                "Content-Type",
                "application/octet-stream"
            )

            conexao.putheader(
                "X-Filename",
                nome
            )

            conexao.endheaders()

            with caminho.open(
                "rb"
            ) as arq:

                while True:

                    bloco = arq.read(
                        256 * 1024
                    )

                    if not bloco:
                        break

                    conexao.send(
                        bloco
                    )

                    enviado += len(
                        bloco
                    )

                    if callable(
                        progresso
                    ):
                        progresso(
                            enviado,
                            tamanho
                        )

            resposta = (
                conexao.getresponse()
            )

            corpo = (
                resposta.read()
                .decode("utf-8")
            )

            if resposta.status >= 400:

                raise RuntimeError(
                    corpo
                )

            return json.loads(
                corpo
            )

        finally:

            conexao.close()


    # ======================================================
    # STEMS
    # ======================================================

    def stem_url(
        self,
        job_id,
        stem
    ):

        nomes = {
            "voz",
            "bateria",
            "baixo",
            "outros",
        }

        if stem not in nomes:

            raise ValueError(
                f"Stem inválido: {stem}"
            )

        return (
            f"{self.base_url}"
            f"/stem/{job_id}/{stem}"
        )


    def baixar_stem(
        self,
        job_id,
        stem,
        destino
    ):

        destino = Path(
            destino
        )

        destino.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        url = self.stem_url(
            job_id,
            stem
        )

        temporario = (
            destino
            .with_suffix(
                destino.suffix + ".part"
            )
        )

        with urllib.request.urlopen(
            url,
            timeout=60
        ) as resposta:

            with temporario.open(
                "wb"
            ) as saida:

                while True:

                    bloco = resposta.read(
                        1024 * 256
                    )

                    if not bloco:
                        break

                    saida.write(
                        bloco
                    )

        temporario.replace(
            destino
        )

        return str(
            destino
        )


    def baixar_stems(
        self,
        job_id,
        pasta_destino,
        progresso=None
    ):

        pasta = Path(
            pasta_destino
        )

        pasta.mkdir(
            parents=True,
            exist_ok=True
        )

        arquivos = {
            "voz": "vocals.mp3",
            "bateria": "drums.mp3",
            "baixo": "bass.mp3",
            "outros": "other.mp3",
        }

        resultado = {}

        total = len(
            arquivos
        )

        for indice, (
            stem,
            nome
        ) in enumerate(
            arquivos.items(),
            start=1
        ):

            if callable(
                progresso
            ):

                progresso(
                    stem,
                    indice,
                    total
                )

            destino = (
                pasta /
                nome
            )

            resultado[stem] = (
                self.baixar_stem(
                    job_id,
                    stem,
                    destino
                )
            )

        return resultado
