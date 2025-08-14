# Quick Setup Guide

## 🚀 Get Started in 5 Minutes

### 1. Fork This Repository
- Click the "Fork" button at the top right of this page
- Clone your forked repository to your local machine

### 2. Set Up GitHub Secrets
Go to your repository → **Settings** → **Secrets and variables** → **Actions**

Add these **required** secrets:
```
SCHOOL_ID=2f37947e-6d30-4bb3-a306-7f69a3b3ed62
GRADE=01
SERVING_LINE=Main Line
MEAL_TYPE=Lunch
SENDER_EMAIL=your-gmail@gmail.com
SENDER_PASSWORD=your-gmail-app-password
RECIPIENT_EMAIL=where-to-send@example.com
```

### 3. Get Gmail App Password
1. Enable 2-Factor Authentication on your Google account
2. Go to [Google Account Settings](https://myaccount.google.com/)
3. Security → 2-Step Verification → App passwords
4. Generate password for "Mail"
5. Use this password in `SENDER_PASSWORD`

### 4. Test It
1. Go to **Actions** tab
2. Click **School Menu Notifier**
3. Click **Run workflow**
4. Watch it run!

## ⚡ What Happens Next

- **Every weekday at 5:00 PM MDT/MST**: Daily script runs automatically
- **Every Sunday at 5:00 PM MDT/MST**: Weekly script runs automatically
- **Daily**: Fetches tomorrow's lunch menu with full details
- **Weekly**: Fetches entire upcoming week with entrees only
- **Sends beautiful emails** to all recipients
- **Includes allergens** and nutritional info

## 🔧 Customize (Optional)

- **Change schedule**: Edit `.github/workflows/menu_notifier.yml`
- **Different school**: Update `SCHOOL_ID` in secrets
- **Different grade**: Update `GRADE` in secrets
- **Email template**: Edit `menu_notifier.py`

## 🧪 Test Locally (Optional)

```bash
# Install dependencies
pip install -r requirements.txt

# Copy config template
cp config.example.env .env

# Edit .env with your settings
nano .env

# Test the script
python test_local.py
```

## ❓ Need Help?

- Check the full [README.md](README.md) for detailed instructions
- Look at GitHub Actions logs for error details
- Test API connection with `python test_api.py`

## 🎯 Success Indicators

✅ **GitHub Actions run successfully**  
✅ **Email received with tomorrow's menu**  
✅ **Menu items displayed correctly**  
✅ **Allergen information included**  

---

**That's it!** Your school menu notifier is now running automatically. 🎉 