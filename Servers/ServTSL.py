import ssl
from dotenv import load_dotenv
import os


class TLSConfig:
    """
    Builds an SSL context for the server side of a mutual TLS (mTLS) connection.

    In mTLS the server does two extra things compared to regular TLS:
      1. Loads its own certificate + private key  (proves its identity to the client)
      2. Loads the CA certificate and sets verify_mode = CERT_REQUIRED
         (verifies that the connecting client holds a cert signed by the same CA)

    Environment variables (from .env):
        SSL_CERT_PATH  -> path to server-cert.pem
        SSL_KEY_PATH   -> path to server-key.pem
        SSL_CA_PATH    -> path to ca-cert.pem  (the CA that signed client certs)
    """

    def __init__(self, certfile: str, keyfile: str, cafile: str, raw_socket):
        load_dotenv()

        # Allow env-var overrides so secrets never have to be hard-coded
        self.certfile = os.getenv("SSL_CERT_PATH", certfile)
        self.keyfile  = os.getenv("SSL_KEY_PATH",  keyfile)
        self.cafile   = os.getenv("SSL_CA_PATH",   cafile)

        self.raw_socket = raw_socket
        self.context: ssl.SSLContext | None = None  # set in create_context()

    # ------------------------------------------------------------------
    def create_context(self) -> ssl.SSLContext:
        """
        Returns an SSLContext configured for **mutual** TLS (server side).

        Key settings explained:
          • PROTOCOL_TLS_SERVER -> server-side context (auto-detects TLS version)
          • minimum_version TLSv1_3-> reject anything older (TLS 1.0/1.1/1.2
            have known vulnerabilities; TLS 1.3 is the only safe choice today)
          • load_cert_chain     -> the server's own identity (cert + private key)
          • load_verify_locations– the CA cert used to verify the client's cert
          • verify_mode CERT_REQUIRED-> refuse any client that doesn't present
            a valid certificate signed by the above CA  ← this is what makes
            it *mutual* TLS
          • No cipher override needed: TLS 1.3 has a fixed, strong cipher suite
            list and does not allow negotiation to weaker ciphers.
        """
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

        # --- Enforce TLS 1.3 only ---
        context.minimum_version = ssl.TLSVersion.TLSv1_3

        # --- Server's own certificate and private key ---
        context.load_cert_chain(
            certfile=self.certfile,
            keyfile=self.keyfile,
        )

        # --- Trust anchor: CA that signed the client certificates ---
        context.load_verify_locations(cafile=self.cafile)

        # --- Demand a client certificate (this is the mTLS part) ---
        context.verify_mode = ssl.CERT_REQUIRED

        self.context = context
        return context