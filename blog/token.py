from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six


class ActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
                six.text_type(user.pk) + six.text_type(timestamp) +
                six.text_type(user.signup_confirmed)
        )


activation_token = ActivationTokenGenerator()
