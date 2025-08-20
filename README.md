# School Menu Notifier

A Python package that automatically fetches your child's school lunch menu and sends it via email. Runs on a schedule using GitHub Actions.

## Features

- 🍽️ Fetches lunch menu data from SchoolCafe API
- 📧 Sends beautifully formatted HTML emails
- ⏰ **Daily**: Runs automatically every weekday at 5:00 PM MDT/MST
- 📅 **Weekly**: Runs automatically every Sunday at 5:00 PM MDT/MST
- 🔧 Configurable via environment variables
- 📱 Responsive email design
- ⚠️ Allergen information included
- 🧪 Manual testing capability
- 📊 Weekly overview with entrees only (simplified format)
- 👶 Pre-K menu indicators

## Project Structure

```
school-menu-notifier/
├── src/
│   └── school_menu_notifier/
│       ├── __init__.py
│       ├── daily_notifier.py      # Daily menu notifications
│       ├── weekly_notifier.py     # Weekly menu overview
│       └── common/
│           ├── __init__.py
│           ├── config.py          # Configuration management
│           └── email_sender.py    # Email sending functionality
├── tests/
│   ├── __init__.py
│   ├── test_daily_notifier.py     # Tests for daily notifier
│   └── test_weekly_notifier.py    # Tests for weekly notifier
├── scripts/
│   ├── test_api.py               # API connectivity test
│   ├── test_local.py             # Local testing script
│   └── run_tests.py              # Test runner
├── docs/
│   ├── README.md                 # Detailed documentation
│   └── QUICK_SETUP.md            # Quick setup guide
├── .github/workflows/            # GitHub Actions workflows
├── requirements.txt              # Python dependencies
├── config.example.env           # Environment config template
└── LICENSE
```

## Quick Start

1. **Fork this repository**
2. **Set up GitHub Secrets** (see [docs/QUICK_SETUP.md](docs/QUICK_SETUP.md))
3. **Test the setup** using manual workflow dispatch
4. **Enjoy automated menu notifications!**

## Documentation

- **[Complete Setup Guide](docs/README.md)** - Detailed setup instructions
- **[Quick Setup Guide](docs/QUICK_SETUP.md)** - Fast track setup
- **[Testing](tests/)** - Run tests locally

## Running Tests

```bash
# Run all tests
python scripts/run_tests.py

# Run specific test files
python -m unittest tests.test_daily_notifier
python -m unittest tests.test_weekly_notifier

# Test locally with .env file
python scripts/test_local.py
```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set PYTHONPATH for imports
export PYTHONPATH="src:$PYTHONPATH"

# Run daily notifier
python -m school_menu_notifier.daily_notifier

# Run weekly notifier
python -m school_menu_notifier.weekly_notifier
```

## How It Works

### Daily Notifications (Weekdays)
- Runs weekdays at 5:00 PM MDT/MST
- Fetches tomorrow's full menu
- Includes all categories and PreK indicators
- Sends to all configured recipients

### Weekly Notifications (Sundays)
- Runs Sundays at 5:00 PM MDT/MST  
- Fetches entire upcoming week's entrees
- Simplified format for meal planning
- Includes PreK indicators for each day

## Security

- All sensitive data stored in GitHub Secrets
- No credentials in code or logs
- SMTP over TLS encryption
- Environment variable validation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Run the test suite
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
