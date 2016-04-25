from distutils.command import upload as orig


class upload(orig.upload):
    """
    Override default upload behavior to obtain password
    in a variety of different ways.
    """

    def finalize_options(self):
        orig.upload.finalize_options(self)
        # Attempt to obtain password. Short circuit evaluation at the first
        # sign of success.
        self.password = (
            self.password or self._load_password_from_keyring() or
            self._prompt_for_password()
        )

    def _load_password_from_keyring(self):
        """
        Attempt to load password from keyring. Suppress Exceptions.
        """
        try:
            keyring = __import__('keyring')
            password = keyring.get_password(self.repository, self.username)
        except Exception:
            password = None
        finally:
            return password

    def _prompt_for_password(self):
        """
        Prompt for a password on the tty. Suppress Exceptions.
        """
        password = None
        try:
            import getpass
            while not password:
                password = getpass.getpass()
        except (Exception, KeyboardInterrupt):
            password = None
        finally:
            return password
