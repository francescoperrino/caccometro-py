# Caccometro

Benvenuto a Caccometro, un bot Telegram open source progettato per tracciare i movimenti intestinali e sfidare gli amici a mantenere un conteggio accurato! \
Prima di iniziare a sperimentare con il codice, segui attentamente questi passaggi per configurare correttamente il tuo ambiente di sviluppo:

## Installazione

1. **Ambiente Virtuale**: È consigliato utilizzare un ambiente virtuale per isolare le dipendenze del progetto. Esegui il seguente comando per creare un ambiente virtuale:

   ```bash
   $ python3 -m venv venv
   ```

2. **Attivazione dell'Ambiente Virtuale**: Attiva l'ambiente virtuale per isolare l'installazione dei pacchetti. A seconda del sistema operativo, usa uno dei seguenti comandi:

   - Su Linux/MacOS:

     ```bash
     $ source venv/bin/activate
     ```

   - Su Windows:

     ```bash
     $ .\venv\Scripts\activate
     ```

3. **Installazione delle Dipendenze**: Installa i pacchetti necessari eseguendo il seguente comando:

   ```bash
   $ pip install -r requirements.txt
   ```

## Configurazione del Bot

Prima di poter lanciare il bot, è necessario creare un nuovo bot Telegram e configurarlo. Segui questi passaggi:

1. **Creazione di un Nuovo Bot Telegram**:

   - Avvia una chat con [@BotFather](https://t.me/botfather).
   - Utilizza il comando `/newbot` e segui le istruzioni per creare un nuovo bot.
   - Otterrai un `BOT_USERNAME` e un `BOT_TOKEN` che dovrai utilizzare per configurare il bot.

2. **Configurazione delle Variabili d'Ambiente**:

   - Crea un file denominato `.env` nella directory del progetto.
   - All'interno del file `.env`, definisci le seguenti variabili sostituendo i valori appropriati:

     ```python
     BOT_USERNAME = '@username_bot'
     BOT_TOKEN = '123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11'
     ```

## Avvio del Bot

Una volta configurato l'ambiente e il bot, puoi avviare il bot eseguendo il seguente comando:

```bash
$ python3 caccometro.py
```
