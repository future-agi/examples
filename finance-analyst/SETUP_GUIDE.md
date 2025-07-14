# 🛠️ Setup Guide - AI Trading Assistant

**Complete installation and configuration guide**

## 📋 System Requirements

### Minimum Requirements
- **Operating System**: Windows 10, macOS 10.14, or Linux (Ubuntu 18.04+)
- **Python**: Version 3.8 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 1GB free space
- **Internet**: Stable broadband connection

### Recommended Requirements
- **Python**: Version 3.9 or 3.10
- **RAM**: 8GB or more
- **CPU**: Multi-core processor
- **Internet**: High-speed connection for real-time data

## 🚀 Installation Steps

### Step 1: Python Installation

**Windows:**
1. Download Python from https://python.org/downloads/
2. Run the installer and check "Add Python to PATH"
3. Verify installation: `python --version`

**macOS:**
```bash
# Using Homebrew (recommended)
brew install python

# Or download from python.org
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3 python3-pip
```

### Step 2: Extract and Navigate

```bash
# Extract the package
unzip ai-trading-assistant-final.zip

# Navigate to directory
cd ai-trading-assistant-final

# Verify contents
ls -la
```

### Step 3: Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# For virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 4: Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit configuration (optional)
nano .env  # Or use your preferred editor
```

### Step 5: Launch Application

```bash
# Start the AI Trading Assistant
python main.py
```

## 🔑 API Key Configuration

### OpenAI API Key (Optional but Recommended)

**1. Get Your API Key:**
- Visit https://platform.openai.com/api-keys
- Sign in or create an account
- Click "Create new secret key"
- Copy the generated key

**2. Add to Configuration:**
```bash
# Edit .env file
nano .env

# Add your key
OPENAI_API_KEY=sk-your-actual-api-key-here
```

**3. Verify Configuration:**
```bash
# Check if key is loaded
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('API Key loaded:', bool(os.getenv('OPENAI_API_KEY')))"
```

### Without API Key
The system works perfectly without an API key:
- Uses rule-based analysis
- All technical indicators available
- Fundamental metrics included
- Professional recommendations provided

## 🌐 Network Configuration

### Firewall Settings

**Windows Firewall:**
1. Open Windows Defender Firewall
2. Click "Allow an app through firewall"
3. Add Python to allowed apps

**macOS Firewall:**
1. System Preferences → Security & Privacy
2. Firewall tab → Firewall Options
3. Allow Python applications

**Linux (UFW):**
```bash
sudo ufw allow 7860
sudo ufw reload
```

### Port Configuration

Default port: 7860

**Change Port (if needed):**
```python
# Edit main.py, line ~595
interface.launch(
    share=True,
    server_port=8080,  # Change to desired port
    server_name="0.0.0.0",
    show_error=True
)
```

## 🔧 Advanced Configuration

### Environment Variables

Complete `.env` configuration:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.1

# Application Settings
LOG_LEVEL=INFO
DEBUG_MODE=False
SERVER_PORT=7860
SHARE_GRADIO=True

# Data Provider Settings
YAHOO_FINANCE_TIMEOUT=30
MAX_STOCKS_PER_QUERY=5
CACHE_DURATION=300

# UI Configuration
THEME=professional
ENABLE_EXAMPLES=True
SHOW_TIPS=True
```

### Logging Configuration

**Enable Debug Logging:**
```env
LOG_LEVEL=DEBUG
DEBUG_MODE=True
```

**Custom Log File:**
```python
# Add to main.py
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_assistant.log'),
        logging.StreamHandler()
    ]
)
```

## 🐳 Docker Deployment (Optional)

### Create Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 7860

CMD ["python", "main.py"]
```

### Build and Run

```bash
# Build image
docker build -t ai-trading-assistant .

# Run container
docker run -p 7860:7860 -e OPENAI_API_KEY=your_key ai-trading-assistant
```

## 🔍 Verification & Testing

### System Check

```bash
# Test Python installation
python --version

# Test package imports
python -c "import yfinance, gradio, asyncio; print('All packages imported successfully')"

# Test market data access
python -c "import yfinance as yf; ticker = yf.Ticker('AAPL'); print('Market data access:', bool(ticker.info))"
```

### Application Test

```bash
# Start application
python main.py

# Expected output:
# 🚀 Starting AI Trading Assistant
# ============================================================
# ✅ Real-time market data integration
# ✅ Live stock analysis with technical indicators
# ✅ AI-powered insights and recommendations
# ✅ Professional trading education
# ✅ Clean, responsive web interface
# ============================================================
# Running on local URL:  http://127.0.0.1:7860
# Running on public URL: https://[random-id].gradio.live
```

### Interface Test

1. **Open Browser**: Navigate to http://localhost:7860
2. **Test Query**: Type "Analyze AAPL stock"
3. **Verify Response**: Should receive detailed analysis with:
   - Current price and change
   - Technical indicators (RSI, moving averages)
   - Fundamental metrics (P/E ratio, market cap)
   - Professional recommendation

## 🚨 Troubleshooting

### Common Installation Issues

**1. Python Not Found**
```bash
# Windows: Add Python to PATH
# macOS/Linux: Use full path
/usr/bin/python3 main.py
```

**2. Permission Denied**
```bash
# Linux/macOS: Fix permissions
chmod +x main.py
sudo chown -R $USER:$USER .
```

**3. Package Installation Fails**
```bash
# Upgrade pip
pip install --upgrade pip

# Install with user flag
pip install --user -r requirements.txt

# Use conda instead
conda install --file requirements.txt
```

**4. Port Already in Use**
```bash
# Find process using port
lsof -i :7860

# Kill process
kill -9 <PID>

# Or use different port
python main.py --port 8080
```

### Runtime Issues

**1. Market Data Not Loading**
- Check internet connection
- Verify stock symbols are valid
- Try different stocks (AAPL, MSFT, GOOGL)

**2. OpenAI API Errors**
- Verify API key is correct
- Check API usage limits
- Ensure sufficient credits

**3. Interface Not Loading**
- Clear browser cache
- Try different browser
- Check firewall settings
- Verify port is not blocked

### Performance Issues

**1. Slow Response Times**
- Check internet speed
- Reduce number of stocks analyzed
- Use local analysis mode

**2. High Memory Usage**
- Restart application periodically
- Close unused browser tabs
- Increase system RAM if possible

## 📱 Mobile Access

### Local Network Access

1. **Find Your IP Address:**
```bash
# Windows
ipconfig

# macOS/Linux
ifconfig
```

2. **Update Launch Configuration:**
```python
# In main.py
interface.launch(
    share=True,
    server_port=7860,
    server_name="0.0.0.0",  # Allows external access
    show_error=True
)
```

3. **Access from Mobile:**
- URL: `http://YOUR_IP_ADDRESS:7860`
- Example: `http://192.168.1.100:7860`

### Public Access

The application automatically generates a public Gradio link:
- Shareable with anyone
- Works on any device
- Temporary (expires after inactivity)

## 🔄 Updates & Maintenance

### Keeping Updated

```bash
# Update Python packages
pip install --upgrade -r requirements.txt

# Update specific packages
pip install --upgrade yfinance gradio openai
```

### Backup Configuration

```bash
# Backup your .env file
cp .env .env.backup

# Backup any custom modifications
tar -czf backup.tar.gz .env main.py
```

### Performance Monitoring

```bash
# Monitor system resources
top
htop

# Monitor network usage
netstat -an | grep 7860

# Check application logs
tail -f trading_assistant.log
```

## 🎯 Production Deployment

### Server Deployment

**1. Prepare Server:**
```bash
# Update system
sudo apt update && sudo apt upgrade

# Install Python and dependencies
sudo apt install python3 python3-pip nginx

# Create application user
sudo useradd -m -s /bin/bash trading-app
```

**2. Deploy Application:**
```bash
# Copy files to server
scp -r ai-trading-assistant-final/ user@server:/home/trading-app/

# Set permissions
sudo chown -R trading-app:trading-app /home/trading-app/
```

**3. Configure Service:**
```bash
# Create systemd service
sudo nano /etc/systemd/system/trading-assistant.service

[Unit]
Description=AI Trading Assistant
After=network.target

[Service]
Type=simple
User=trading-app
WorkingDirectory=/home/trading-app/ai-trading-assistant-final
ExecStart=/usr/bin/python3 main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

**4. Start Service:**
```bash
sudo systemctl enable trading-assistant
sudo systemctl start trading-assistant
sudo systemctl status trading-assistant
```

### Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:7860;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## ✅ Final Checklist

Before going live, verify:

- [ ] Python 3.8+ installed
- [ ] All dependencies installed successfully
- [ ] .env file configured (API key optional)
- [ ] Application starts without errors
- [ ] Web interface loads correctly
- [ ] Stock analysis works (test with AAPL)
- [ ] Network access configured
- [ ] Firewall rules set (if needed)
- [ ] Backup configuration saved

## 🎉 Success!

Your AI Trading Assistant is now ready to use! 

**Next Steps:**
1. Test with various stock symbols
2. Explore educational features
3. Try different types of queries
4. Share the public link with others
5. Monitor performance and usage

**Remember**: This is for educational purposes only. Always do your own research before making investment decisions.

---

**Need Help?** Review the troubleshooting section or check the main README.md for additional information.

