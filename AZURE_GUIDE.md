# Azure Deployment Instructions

Follow these steps to deploy your backend and bot for free using the **Azure for Students** credits.

## 1. Prerequisites
- Claim your credits at [azure.microsoft.com/free/students/](https://azure.microsoft.com/free/students/)
- Install [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) (optional, you can use the portal).

## 2. Deploy via Azure Container Apps (Recommended)
This fits your Docker setup perfectly.

1. **Create a Resource Group**: Name it `CounsellingBotGroup`.
2. **Create a Container Registry (ACR)**: To host your images for free.
3. **Build and Push Images**:
   ```bash
   # Login to Azure
   az login
   az acr login --name yourregistryname

   # Build and push
   docker build -t yourregistryname.azurecr.io/backend:v1 .
   docker push yourregistryname.azurecr.io/backend:v1
   ```
4. **Create a Container App**:
   - Use the image you just pushed.
   - Set Environment Variables:
     - `SECRET_KEY`: A random long string.
     - `DEBUG`: `False`
     - `ALLOWED_HOSTS`: `your-app-name.azurewebsites.net`
     - `DATABASE_NAME`, `DATABASE_USER`, etc. (Point to Azure Postgres).
     - `TELEGRAM_BOT_TOKEN`: Your bot token.
     - `CSRF_TRUSTED_ORIGINS`: `https://yourusername.github.io` (Your GitHub Pages URL).

## 3. Database
- Create an **Azure Database for PostgreSQL (Flexible Server)**.
- Choose the "Burstable" tier (B1ms) which is often covered by the free credits.

## 4. Bot
- You can deploy the bot as a second **Container App** using the same image but with a different start command: `python bot/telegram_bot.py`.
- Ensure it has the `BACKEND_URL` environment variable pointing to your Backend Container App URL.
