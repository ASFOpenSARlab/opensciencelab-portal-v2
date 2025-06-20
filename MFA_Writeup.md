# Cognito MFA Options

Main Cognito MFA Docs: <https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-mfa.html>

TLDR: Unless we're okay with ONLY email MFA, We should have the pool set to `Optional` and build our own UI for *setting up* TOTP MFA. (We can still use cognito for logging in with TOTP.). If it's required and we do TOTP, we'd have to write a interface to reset it anyways, and you have to switch it to another type before changing it (Either email or SMS). If it's optional, you can disable it for a specific user and they'll be prompted to set it next time they sign in before they can do anything else.

## If Required

- If you create a user WITHOUT MFA in a optional pool, then switch the setting to Require MFA, the user is forced to create MFA on sign in. There's also no way to reset/disable MFA in the console, unlike if the pool setting was Optional.

- If we switch to Emailing users with SES, there's a chance to "reset MFA", we can just switch users MFA option to be Email from whatever they were using before. (We'll have to add SES to the stack, and idk how the same email in multiple accounts works yet.).
  - From [this section](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-mfa.html#user-pool-settings-mfa-prerequisites), MFA method can't be the same as password recovery. If we switch their MFA to Email, they can't get the password reset code from that. That's probably fine? They can contact us if they need to switch back or something?
  - Switch to email would allow them to get back in, but is there a way to reset the TOTP MFA after?? Maybe we just ONLY use email, no TOTP?

### To Reset TOTP (Required)

- You can't just disable it with this route. You have to switch it to either Email or SMS (the former requiring us to setup SES). If they don't already have those setup, they'll have to tell them to us so we can add them through a CLI command.
- The problem is from here, I don't see a way to nuke the existing TOTP and have cognito trigger to re-setup it. We'd probably have to write a custom interface for this, at which point, the Optional setup is a lot more clear anyways.

## If Optional

- We [must build our own UI](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-mfa.html). We only get the built-in one if it's `Required`.
- Easier to [reset users MFA](https://medium.com/@alexkhalilov/how-to-reset-aws-cognito-lost-totp-c08c36892a6c), though if we're building our own solution, this is less of a concern anyways.

- [This suggests](https://stackoverflow.com/a/72287041) you can have the pool as Optional, BUT make each user required. When I tried that though, I get an error that they don't have a valid TOTP setup yet. We can [add one with the CLI](https://repost.aws/knowledge-center/cognito-user-pool-totp-mfa), but this goes into setting up TOTP manually again.
  - BUT! If I:
        1: Make MFA on the Pool REQUIRED
        2: Create a User with MFA Enabled
        3: Switch the pool MFA's setting to OPTIONAL
    The user has a  TOTP code in the background. I can switch their MFA status back and fourth in the console now. (`Users` -> `<user>` -> `Actions` -> `Update MFA configuration`). This means all we need is a custom "Create MFA" page I believe. We can then disable each specific user's MFA as they need. (That error above is only because you tried enabling MFA for a user that doesn't have it setup.).
  - If we go this route: User looses TOTP and asks us to reset it. We just disable it. The code follows the same logic as when they first signed in, and re-directs them to TOTP setup before they can do anything else. It's definitely not a bad solution... Just extra maintenance on the "Create MFA" page.

### To Reset TOTP (Optional)

- Go to the Cognito Console, select your pool.
- Go to `Users` -> `<user>` -> `Actions` -> `Update MFA configuration`.
  - (This is also where you can reset their password if needed).
- Change MFA to disabled. They'll be forced to set it up again next time they sign in.
