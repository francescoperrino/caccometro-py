# Caccometro

Benvenuto a Caccometro, un bot Telegram open source progettato per tracciare i movimenti intestinali e sfidare gli amici a mantenere un conteggio accurato! \
Prima di iniziare a sperimentare con il codice, segui attentamente questi passaggi per configurare correttamente il tuo ambiente di sviluppo:

## Installazione

1. **Ambiente Virtuale**: È consigliato utilizzare un ambiente virtuale per isolare le dipendenze del progetto. Esegui il seguente comando per creare un ambiente virtuale:

   ```bash
   $ python3 -m venv venv
   ```

2. **Attivazione dell'Ambiente Virtuale**: Attiva l'ambiente virtuale per garantire che le dipendenze del progetto siano installate in modo isolato. A seconda del sistema operativo, usa il comando appropriato:

   - Su Linux/MacOS:

     ```bash
     $ source venv/bin/activate
     ```

   - Su Windows:

     ```bash
     $ .\venv\Scripts\activate
     ```

3. **Installazione delle Dipendenze**: Ora installa i pacchetti necessari eseguendo il seguente comando:

   ```bash
   $ pip install -r requirements.txt
   ```

## Configurazione del Bot

Prima di poter avviare il bot, è necessario crearne uno nuovo su Telegram e configurarlo correttamente. Segui questi passaggi:

1. **Creazione di un Nuovo Bot Telegram**:

   - Avvia una chat con [@BotFather](https://t.me/botfather).
   - Utilizza il comando `/newbot` e segui le istruzioni per creare un nuovo bot.
   - Dopo aver completato la creazione, riceverai un `BOT_USERNAME` e un `BOT_TOKEN` che serviranno per configurare il bot.
   - Nella chat con [@BotFather](https://t.me/botfather), utilizza il comando `/setcommands` per configurare i comandi del bot. Puoi usare l'esempio seguente:
     ```
     start - Avvia il bot.
     classifica_mese - Classifica del mese corrente.
     classifica_anno - Classifica dell'anno corrente.
     statistiche_mese - Statistiche del mese corrente.
     statistiche_anno - Statistiche dell'anno corrente.
     conto_giorno - Conteggio per il giorno corrente.
     aggiungi - Aggiunge 1 all'utente nel giorno specificato.
     togli - Sottrae 1 all'utente nel giorno specificato.
     mese_x - Conteggio del mese specificato [mm-YYYY].
     anno_x - Conteggio dell'anno specificato [YYYY].
     statistiche_mese_x - Statistiche del mese specificato [mm-YYYY].
     statistiche_anno_x - Statistiche dell'anno specificato [YYYY].
     conto_giorno_x - Conteggio del giorno specificato [gg-mm-YYYY].
     ```

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

Ora sei pronto per iniziare a sperimentare con il codice di Caccometro! Buon divertimento!
