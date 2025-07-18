# X-Bot: Twitter/Finance News & Sentiment Bot 🤖

Bot financiero para análisis de empresas, extracción de noticias y sentimiento, y automatización de respuestas en X (Twitter).

## Características principales ✨

- **Gestión segura de credenciales** con `.env`
- **Extracción de noticias**: Google News, Yahoo Finance, X (Twitter), RSS (CNBC, Reuters, FT, etc.)
- **Análisis de sentimiento** multi-fuente
- **Respuestas automáticas** a menciones en X
- **Caché inteligente** para eficiencia de API
- **Ejecución indefinida** (modo daemon)
- **Manejo robusto de errores y límites de API**

## Instalación y configuración 🚀

### 1. Clona el repositorio
```bash
git clone <your-repo-url>
cd x-bot
```

### 2. Instala las dependencias
```bash
pip install -r requirements.txt
```

### 3. Crea el archivo `.env`
Coloca tus credenciales de X (Twitter) en `.env`:

```env
API_KEY=your_api_key_here
API_SECRET=your_api_secret_here
BEARER_TOKEN=your_bearer_token_here
ACCESS_TOKEN=your_access_token_here
ACCESS_TOKEN_SECRET=your_access_token_secret_here
```

### 4. Obtén credenciales de X (Twitter)
1. Ve a [Twitter Developer Portal](https://developer.twitter.com/)
2. Crea una app y genera las claves
3. Añádelas a tu `.env`

## Ejecución indefinida 💻

Para que el bot funcione de manera continua:

```bash
python run_bot.py
```
o
```bash
python -c "from twitter_client import TwitterClient; TwitterClient().monitor_and_respond_mentions()"
```

El bot monitoreará menciones y responderá automáticamente según la lógica programada.

## Límites de uso, caps y control de concurrencia ⚠️

### Lógica de control de uso y protección contra sobreuso

- **Rate limits de X/Twitter:** El bot respeta los límites de la API de X/Twitter (por ejemplo, 300 consultas/15min para endpoints de usuario). Si se alcanza el límite, el bot detecta el error 429 y espera automáticamente el tiempo indicado por el header `x-rate-limit-reset` antes de reintentar.
- **Caps y advertencias:** El sistema de tracking de uso (ver `x_api_usage.py`) lleva un conteo local de interacciones y emite advertencias si se supera el 90% del cupo permitido.
- **Control de concurrencia:** Se utiliza un file lock (`mention_bot.lock`) para asegurar que solo un proceso o hilo acceda a la API y registre respuestas a la vez, evitando corrupción de datos o doble uso accidental.
- **Temporizador inteligente:** El parámetro `base_sleep` ajusta la frecuencia de escaneo de menciones según si el mercado está abierto (cada 4:30 min) o cerrado (cada hora), minimizando el riesgo de sobrepasar los límites.

### ¿Cómo funciona el sistema?

1. **Escaneo periódico:** El bot revisa las menciones a intervalos definidos y responde solo a usuarios autorizados.
2. **File lock:** Antes de responder, adquiere un lock de archivo para evitar que dos instancias respondan a la vez.
3. **Rate limit avanzado:** Si la API responde con error 429, el bot espera el tiempo necesario antes de continuar.
4. **Advertencias:** Si el uso local se acerca al límite, se imprime una advertencia en consola.

> **Importante:** Si ejecutas varias instancias del bot en la misma máquina, el file lock previene conflictos. Si usas varias máquinas, considera migrar el lock a una base de datos centralizada.

Para detalles técnicos, revisa los comentarios en `twitter_client.py` y el módulo `x_api_usage.py`.

## Estructura de archivos 📁

```
x-bot/
├── bot.py                  # Lógica básica de X
├── twitter_client.py        # Lógica avanzada, caché, integración RSS
├── company_analyzer.py      # Análisis financiero y fundamental
├── news.py                  # Extracción de noticias Google/Yahoo/X
├── news_rss.py              # Extracción de noticias RSS
├── sentiment_analytics.py   # Métricas y análisis de sentimiento
├── updater_jsons.py         # Utilidades para actualizar datos
├── run_bot.py               # Arranque indefinido
├── get_creds.py             # Carga de credenciales
├── working_wjson.py         # Utilidades JSON
├── data/                    # Archivos de datos y queries
├── requirements.txt         # Dependencias
├── .env                     # Credenciales (NO subir)
```

## Fuentes de noticias integradas 📰
- Google News (pygooglenews)
- Yahoo Finance
- X (Twitter)
- RSS: CNBC, Reuters, FT, Yahoo Finance, etc.

## Actualización de datos
Utiliza `updater_jsons.py` para actualizar empresas, noticias y análisis de sentimiento.

## Seguridad �

- `.env` ignorado por Git
- Validación de credenciales antes de llamadas API
- Mensajes de error no exponen datos sensibles

## Licencia 📄

MIT License. Ver archivo LICENSE.

## Disclaimer ⚠️

Este bot es solo para fines educativos y experimentales.
- **429 Too Many Requests**: Rate limit reached
- **403 Forbidden**: Permission issues
- **401 Unauthorized**: Invalid credentials

## Security 🔒

- ✅ API keys stored in `.env` file (not in code)
- ✅ `.env` file ignored by Git (`.gitignore`)
- ✅ Credential validation before API calls
- ✅ Error messages don't expose sensitive data

## File Structure 📁

```
StockP_Ai-x-bot/
├── bot.py             # Main bot code
├── .env               # API credentials (DO NOT COMMIT)
├── .gitignore         # Git ignore rules
├── README.md          # This file
|__ get_creds          # load credentials code
   
```

## Contributing 🤝

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License 📄

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer ⚠️
\

This bot is for educational purposes.
 

