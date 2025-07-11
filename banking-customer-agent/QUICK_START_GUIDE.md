# Banking AI Agent - Quick Start Guide

## 🚀 **GET STARTED IN 5 MINUTES**

This guide will get your Banking AI Agent system up and running quickly for testing and demonstration.

---

## ⚡ **SUPER QUICK START**

### **1. Extract and Navigate**
```bash
unzip banking_ai_complete_package.zip
cd banking_ai_complete_package
```

### **2. Start Backend**
```bash
cd banking_ai_agent
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

### **3. Start Gradio Demo** (New Terminal)
```bash
cd banking_ai_agent
source venv/bin/activate
python gradio_demo.py
```

### **4. Access Demo**
- **Gradio Demo**: http://localhost:7860
- **Backend API**: http://localhost:5000

**🎉 You're ready to test the Banking AI Agent!**

---

## 🎯 **DEMO TESTING**

### **Sample Queries to Try**
1. "What's my account balance?"
2. "Transfer $500 from checking to savings"
3. "Tell me about your loan products"
4. "What are the current interest rates?"
5. "I need help with a suspicious transaction"

### **Banking Tools to Test**
- **Account Balance**: Use Customer ID `CUST001`, Account ID `CHK001`
- **System Status**: Click to see all system health metrics

---

## 🖥️ **ALL THREE INTERFACES**

### **1. Gradio Demo** (Recommended for Testing)
```bash
cd banking_ai_agent
python gradio_demo.py
# Access: http://localhost:7860
```
**Perfect for**: Stakeholder demos, user testing, quick validation

### **2. React Frontend** (Full Application)
```bash
cd banking-ai-frontend
npm install
npm run dev --host
# Access: http://localhost:5173
```
**Perfect for**: Complete banking application experience

### **3. Backend API** (Developer Access)
```bash
curl http://localhost:5000/health
```
**Perfect for**: Integration testing, API development

---

## 🔧 **CONFIGURATION**

### **Environment Setup**
The `.env` file is already configured with your OpenAI API key:
```env
OPENAI_API_KEY=xxxx
```

### **Demo Data Available**
```
Customer: CUST001
├── CHK001 (Checking): $2,500.75
└── SAV001 (Savings): $15,000.00

Customer: CUST002
└── CHK002 (Checking): $1,250.30
```

---

## 🧠 **AI CAPABILITIES VERIFICATION**

Test all 6 AI capabilities:

### **1. Planning** ✅
Ask: "I want to transfer money and check my balance"
→ AI creates multi-step execution plan

### **2. RAG** ✅
Ask: "What loan products do you offer?"
→ AI retrieves information from knowledge base

### **3. Execution** ✅
Use banking tools to perform account operations
→ AI executes planned actions

### **4. Memory** ✅
Continue conversation from previous queries
→ AI remembers context and customer history

### **5. Self-Reflection** ✅
Check confidence scores in AI responses
→ AI evaluates its own response quality

### **6. Complex Reasoning** ✅
Ask: "Help me plan my finances for a home purchase"
→ AI handles sophisticated multi-step scenarios

---

## 🏦 **BANKING FEATURES TO TEST**

### **Account Management**
- Balance inquiries
- Transaction history
- Account status checks

### **Compliance Features**
- Identity verification prompts
- KYC compliance checking
- AML monitoring alerts

### **Customer Service**
- Product information requests
- General banking questions
- Problem resolution assistance

---

## 📊 **PERFORMANCE EXPECTATIONS**

### **Response Times**
- Health checks: < 1 second
- Account operations: < 1 second
- AI chat responses: 20-30 seconds (full AI pipeline)
- System status: < 1 second

### **System Requirements**
- **RAM**: 8GB minimum (16GB recommended)
- **Disk**: 10GB free space
- **Network**: Internet access for OpenAI API
- **Browser**: Modern browser for web interfaces

---

## 🔍 **TROUBLESHOOTING**

### **Common Issues**

#### **Backend Won't Start**
```bash
# Check Python version
python --version  # Should be 3.11+

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

#### **OpenAI API Errors**
```bash
# Verify API key in .env file
cat .env | grep OPENAI_API_KEY

# Test API connectivity
curl -H "Authorization: Bearer YOUR_API_KEY" https://api.openai.com/v1/models
```

#### **Frontend Issues**
```bash
# Check Node.js version
node --version  # Should be 18+

# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

#### **Port Conflicts**
```bash
# Check what's using ports
lsof -i :5000  # Backend
lsof -i :7860  # Gradio
lsof -i :5173  # React

# Kill processes if needed
kill -9 <PID>
```

---

## 📚 **NEXT STEPS**

### **For Development**
1. Read `DEPLOYMENT_GUIDE.md` for production setup
2. Check `API_DOCUMENTATION.md` for integration details
3. Review `banking_ai_architecture.md` for system design

### **For Demonstrations**
1. Use Gradio demo for stakeholder presentations
2. Prepare sample banking scenarios
3. Review `GRADIO_DEMO_GUIDE.md` for advanced features

### **For Production**
1. Follow security hardening guidelines
2. Set up monitoring and logging
3. Configure load balancing and scaling

---

## 🎯 **SUCCESS INDICATORS**

You'll know the system is working correctly when:

✅ **Backend Health Check**: http://localhost:5000/health returns "Healthy"
✅ **Gradio Interface**: Loads at http://localhost:7860 with banking theme
✅ **AI Responses**: Chat queries return intelligent banking responses
✅ **Banking Tools**: Account balance tool returns mock account data
✅ **System Status**: Shows all modules as "Healthy" with green checkmarks

---

## 🏆 **YOU'RE READY!**

Your Banking AI Agent system is now running and ready for:

- 🎪 **Stakeholder demonstrations**
- 👥 **User testing and feedback**
- 🔬 **Development and integration**
- 🏦 **Banking scenario validation**

**Welcome to the future of banking customer service! 🚀**

---

## 📞 **SUPPORT**

For detailed information, see:
- `README.md` - Complete system documentation
- `GRADIO_DEMO_GUIDE.md` - Gradio interface guide
- `DEPLOYMENT_GUIDE.md` - Production deployment
- `API_DOCUMENTATION.md` - API reference
- `PACKAGE_CONTENTS.md` - Complete package overview

