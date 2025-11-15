<div align="center">
  <h1 style="margin-top: 24px;">💎 Anonymous Questions Bot by @lovlydev</h1>

  <p style="font-size: 18px; margin-bottom: 24px;">
    <b>Telegram bot for receiving anonymous questions through unique links</b>
  </p>

[Report Bug](https://github.com/lovlygod/anonymous-questions/issues) · [Request Feature](https://github.com/lovlygod/anonymous-questions/issues)

</div>

---

## ✨ Features

- 🤐 **Anonymous Questions** - Users can ask questions anonymously without revealing their identity
- 🔗 **Unique Links** - Each user gets a unique link for receiving questions
- 👨‍💼 **Admin Panel** - Advanced bot management capabilities
- 📤 **Media Support** - Ability to send responses in various formats (text, photo, video, etc.)
- 📊 **Statistics** - Detailed analytics of bot usage
- 📢 **Broadcasting** - Ability to send messages to all users
- 💰 **Referral System** - Auto-generated referral links for user acquisition
- 📈 **Advertising Posts** - Support for showing promotional materials
- 📺 **Subscription Channels** - Ability to require channel subscriptions for bot usage

## 🚀 Quick Start

### 1. Installation

```bash
git clone https://github.com/lovlygod/anonymous-questions.git
cd anonymous-questions
```

### 2. Configuration

Create `.env` file based on example:

```bash
cp .env.example .env
```

Edit `.env` file with your settings:

```env
API_TOKEN=your_telegram_bot_token
MONGO_URI=mongodb://localhost:27017/anonymous_questions
REDIS_HOST=localhost
REDIS_PORT=6379
ADMIN_ID=your_telegram_id
DATABASE_NAME=anonymous_questions
```

### 3. Usage

#### Local Execution:
```bash
python bot/main.py
```

#### Docker Execution:
```bash
docker build -t anonymous-questions-bot .
docker run -d --env-file .env anonymous-questions-bot
```

#### Docker Compose Execution:
```bash
docker-compose up -d
```

## Commands

### For Users:
| Command | Description |
|---------|-------------|
| `/start` | Start the bot and get your unique link |
| `/my_link` | Get your unique question link |
| `/stats` | View your question statistics |

### For Administrators:
| Command | Description |
|---------|-------------|
| `/admin` | Access admin panel |
| `/stats` | View bot statistics |
| `/broadcast` | Send broadcast message |
| `/users` | List of users |
| `/channels` | Manage subscription channels |
| `/referrals` | Referral system management |

## Technology Stack

- Python 3.8+
- Aiogram - Asynchronous framework for Telegram Bot API
- MongoDB - Database for storing user and question information
- Redis - Caching and temporary data storage
- Docker - Application containerization
- PyMongo - MongoDB driver
- Environs - Environment variable management

## Requirements

- Python >= 3.8
- Libraries: aiogram, pymongo, redis, etc. (see requirements.txt)

## License
[MIT](LICENSE)

<div align="center">

### Made with ❤️ by [@lovly](https://t.me/lovlyswag)

**Star ⭐ this repo if you found it useful!**

</div>
