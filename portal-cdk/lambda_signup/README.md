# Lambda Signup

This is a Cognito Pre-Signup Lambda hook, to verify the username only contains safe/whitelisted characters. Without it, you could technically have a "username" that allows for XSS attacks or other issues.
