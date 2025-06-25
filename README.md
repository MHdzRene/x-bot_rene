# Twitter Bot 🤖

just a  Twitter bot. 

## Features ✨

- **Secure API Key Management**: Uses `.env` file to store credentials safely
- **Tweet Creation**: Posts updates about anithing
- **Tweet Search**: Searches for recent tweets about anithing
- **Error Handling**: Robust error handling for API limits and authentication issues
- **Rate Limit Management**: Handles Twitter API rate limits gracefully

## Setup 🚀

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd x-bot
```

### 2. Install dependencies
```bash
pip install tweepy
```

### 3. Create environment file
Create a `.env` file in the root directory with your Twitter API credentials:

```env

API_KEY=your_api_key_here
API_SECRET=your_api_secret_here
BEARER_TOKEN=your_bearer_token_here
ACCESS_TOKEN=your_access_token_here
ACCESS_TOKEN_SECRET=your_access_token_secret_here

```

### 4. Get Twitter API Credentials
1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Create a new app
3. Generate your API keys and tokens
4. Add them to your `.env` file

## Usage 💻

Run the bot:
```bash
python bot.py
```

The bot will:
1. Load credentials securely from `.env` file
2. Post a status tweet
3. Search for recent tweets about anithing you want


## Error Handling 🛡️

The bot handles various Twitter API errors:
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

This bot is for educational purposes. Make sure to comply with Twitter's Terms of Service and API usage guidelines.
bot that analyzes X trends related to S&amp;P 500 companies and posts real-time updates. 
