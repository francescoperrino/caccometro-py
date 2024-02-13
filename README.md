# Caccometro

Caccometro, il bot Telegram che terrà conto per te dei movimenti peristaltici del tuo (o dei vostri se in un gruppo) intestino.

## Installation

Per la creazione dell'ambiente di sviluppo, eseguire i seguenti step.

- Creazione dell'ambiente virtuale:

  ```bash
  $ python3 -m venv venv
  ```

- Attivare l'ambiente virtuale:

  - Su Linux/MacOS:

    ```bash
    $ source venv/bin/activate
    ```

  - Su Windows:

    ```bash
    $ .\venv\Scripts\activate
    ```

- Installazione pacchetti necessari:

  ```bash
  $ pip install -r requirements.txt
  ```

## Deployment

Prima di lanciare il bot, assicurarsi di creare il file `.env`, con dentro definiti

```python
BOT_USERNAME = '@username_bot'
BOT_TOKEN = '123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11'
```

Per lanciare il bot, lanciare il seguente comando:

```bash
$ python3 caccometro.py
```
