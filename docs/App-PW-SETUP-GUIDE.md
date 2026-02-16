# Setup Guide: Credentials & API Keys

This guide explains how to obtain the necessary credentials to configure the Mail Agent.

## 1. How to get a Gmail App Password
Gmail requires an **App Password** if you have 2-Step Verification enabled (which is mandatory for third-party apps).

1. Go to your [Google Account](https://myaccount.google.com/).
2. Select **Security** on the left navigation panel.
3. Under "How you sign in to Google," make sure **2-Step Verification** is turned **On**.
4. Click on **2-Step Verification**.
5. Scroll to the bottom of the page and select **App passwords**.
6. Enter a name for the app (e.g., "Mail Agent").
7. Click **Create**.
8. Copy the 16-character password displayed in the yellow bar. **This is your IMAP password.**

---

## 2. How to get a Yandex Mail App Password
Yandex also requires an application-specific password.

1. Log in to your Yandex account and go to [Account Management](https://passport.yandex.com/profile).
2. Go to **Passwords and authorization**.
3. Select **App passwords**.
4. Click **Enable app passwords** if you haven't already.
5. Click **Create a new password**.
6. Select the app type **Mail**.
7. Give it a name (e.g., "Mail Agent") and click **Create**.
8. Copy the generated password. **This is your IMAP password.**

---

## 3. How to get Telegram Bot Token and Chat ID

### Get the Bot Token
1. Open Telegram and search for [@BotFather](https://t.me/botfather).
2. Start a chat and send the command `/newbot`.
3. Follow the instructions to name your bot and give it a username.
4. Once created, BotFather will give you an **API Token**. Copy this for your `bot_token`.

### Get your Chat ID
1. Open Telegram and search for [@userinfobot](https://t.me/userinfobot).
2. Start the bot.
3. It will immediately reply with your **Id**. This is your `chat_id`.
   - *Note: If you want the bot to send messages to a group, add the bot to the group and use a bot like `@get_id_bot` inside the group.*
