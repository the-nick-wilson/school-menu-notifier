# School Menu Notifier

A Python script that automatically fetches your child's school lunch menu for the following day and sends it to you via email. The script runs on a schedule using GitHub Actions.

## Features

- 🍽️ Fetches lunch menu data from SchoolCafe API
- 📧 Sends beautifully formatted HTML emails
- ⏰ Runs automatically every weekday at 6:00 PM UTC
- 🔧 Configurable via environment variables
- 📱 Responsive email design
- ⚠️ Allergen information included
- 🧪 Manual testing capability

## How It Works

1. **Scheduled Execution**: GitHub Actions runs the script every weekday at 6:00 PM UTC
2. **API Fetch**: Retrieves tomorrow's lunch menu from SchoolCafe
3. **Data Processing**: Formats the menu items by category (Entrees, Vegetables, Fruits, Milk)
4. **Email Generation**: Creates a beautiful HTML email with all menu details
5. **Delivery**: Sends the email to your specified address

## Setup Instructions

### 1. Fork/Clone This Repository

```bash
git clone https://github.com/yourusername/school-menu-notifier.git
cd school-menu-notifier
```

### 2. Configure GitHub Secrets

Go to your repository's **Settings** → **Secrets and variables** → **Actions** and add the following secrets:

#### Required Secrets:
- `SCHOOL_ID`: Your school's unique identifier (default: `2f37947e-6d30-4bb3-a306-7f69a3b3ed62`)
- `GRADE`: Your child's grade (default: `01`)
- `SERVING_LINE`: Serving line name (default: `Main Line`)
- `MEAL_TYPE`: Meal type (default: `Lunch`)
- `SENDER_EMAIL`: Your Gmail address
- `SENDER_PASSWORD`: Your Gmail app password (see Gmail setup below)
- `RECIPIENT_EMAIL`: Where to send the menu emails

#### Optional Secrets:
- `SMTP_SERVER`: SMTP server (default: `smtp.gmail.com`)
- `SMTP_PORT`: SMTP port (default: `587`)

### 3. Gmail App Password Setup

Since Gmail requires 2FA for app passwords, you'll need to:

1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password:
   - Go to [Google Account Settings](https://myaccount.google.com/)
   - Security → 2-Step Verification → App passwords
   - Generate a password for "Mail"
   - Use this password in the `SENDER_PASSWORD` secret

### 4. Customize School Settings

If your school uses different parameters, update the secrets accordingly:

- **School ID**: Found in the SchoolCafe URL or API calls
- **Grade**: Your child's grade level (01, 02, 03, etc.)
- **Serving Line**: Usually "Main Line" but may vary
- **Meal Type**: "Lunch", "Breakfast", etc.

### 5. Test the Setup

1. Go to **Actions** tab in your repository
2. Click **School Menu Notifier** workflow
3. Click **Run workflow** → **Run workflow**
4. Monitor the execution logs

## Email Format

The generated email includes:

- **Header**: Tomorrow's date and school branding
- **Categories**: Organized by food type (Entrees, Vegetables, Fruits, Milk)
- **Menu Items**: Name, serving size, calories, and allergens
- **Allergen Warnings**: Clearly marked for safety
- **Responsive Design**: Works on desktop and mobile

## Customization

### Modify Schedule

Edit `.github/workflows/menu_notifier.yml` to change when the script runs:

```yaml
schedule:
  # Run at different times or days
  - cron: '0 18 * * 1-5'  # Weekdays at 6 PM UTC
  - cron: '0 12 * * 1-5'  # Weekdays at 12 PM UTC
```

### Add More Meal Types

Modify the script to fetch multiple meal types or add breakfast notifications.

### Custom Email Templates

Edit the `format_menu_email` method in `menu_notifier.py` to change the email appearance.

## Troubleshooting

### Common Issues

1. **Email Not Sending**: Check Gmail app password and 2FA settings
2. **No Menu Data**: Verify school ID and grade are correct
3. **API Errors**: Check if SchoolCafe API is accessible
4. **Workflow Failures**: Review GitHub Actions logs for error details

### Debug Mode

The script includes comprehensive logging. Check the GitHub Actions logs to see:
- API request details
- Menu data processing
- Email sending status

### Manual Testing

Use the workflow dispatch feature to test the script manually:
1. Go to Actions → School Menu Notifier
2. Click "Run workflow"
3. Choose whether to test with today's date

## Security Notes

- **Never commit** your email credentials to the repository
- Use GitHub Secrets for all sensitive information
- Gmail app passwords are more secure than regular passwords
- The script only reads public menu data

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter issues:
1. Check the GitHub Actions logs
2. Verify your secrets are configured correctly
3. Test with the manual workflow dispatch
4. Open an issue with detailed error information