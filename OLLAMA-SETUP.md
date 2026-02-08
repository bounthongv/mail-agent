# Ollama Setup Guide for Mail Agent

Follow these steps to set up the local AI engine on your notebook for fast and reliable email summarization.

## 1. Install Ollama
1. Download the Windows installer from [ollama.com](https://ollama.com/download/windows).
2. Run the installer and complete the setup.
3. Ensure Ollama is running (look for the Llama icon in your Windows System Tray).

## 2. Download the Model
Open **PowerShell** or **Command Prompt** and run the following command to download the lightweight and fast Qwen model:
```powershell
ollama pull qwen2.5:1.5b
```
*(Size: ~900MB. This model is optimized for laptops and provides excellent summaries.)*

## 3. Configure the Mail Agent
Ensure your `config/settings.yaml` is set to use Ollama as the primary provider:

```yaml
# AI Settings
ai:
  provider: "ollama"
  model: "qwen2.5:1.5b"
  max_tokens: 300
  temperature: 0.3

# Local AI Settings
localai:
  enabled: true
  provider: "ollama"
  model: "qwen2.5:1.5b"
```

## 4. Run the Agent
1. Make sure Ollama is running in your system tray.
2. Launch `MailAgent.exe`.
3. If Ollama is available, the agent will use it immediately. If Ollama is closed, the agent will automatically try your cloud fallbacks (Gemini/OpenRouter).

## Troubleshooting
- **Model not found**: Run `ollama list` in PowerShell to verify `qwen2.5:1.5b` is installed.
- **Connection Error**: Ensure Ollama is not being blocked by a firewall and that the tray icon is visible.
