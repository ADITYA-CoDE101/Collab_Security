"""
ClientTLS.py  – mTLS client-side SSL context helper.

In mutual TLS the client must do THREE things (vs. one in regular TLS):

  Regular TLS (one-way):
    1. Load CA cert → verify the server's identity

  Mutual TLS (two-way):
    1. Load CA cert         → verify the server's identity         (same as before)
    2. Load client cert     → present our identity to the server
    3. Load client key      → prove we own that cert (private key)

Environment variables (from .env):
    SSL_CA_PATH          – path to ca-cert.pem
    SSL_CLIENT_CERT_PATH – path to client-cert.pem
    SSL_CLIENT_KEY_PATH  – path to client-key.pem
"""

import ssl
import os
from dotenv import load_dotenv


class ClientTLSConfig:
    """
    Builds an SSLContext for the client side of an mTLS connection.
    """

    def __init__(
        self,
        cafile: str,
        client_certfile: str, 
        client_keyfile: str,
        server_hostname: str = "localhost",
    ):
        """
        Initialize the TLS configuration for the client side of a mutual TLS (mTLS) connection.

        Args:
            cafile (str): Path to the CA certificate file used to verify the server's certificate.
            client_certfile (str): Path to the client's certificate file.
            client_keyfile (str): Path to the client's private key file.
            server_hostname (str, optional): The hostname of the server to connect to. Defaults to "localhost".
        """
        load_dotenv()

        self.cafile          = os.getenv("SSL_CA_PATH",          cafile)
        self.client_certfile = os.getenv("SSL_CLIENT_CERT_PATH", client_certfile)
        self.client_keyfile  = os.getenv("SSL_CLIENT_KEY_PATH",  client_keyfile)
        self.server_hostname = server_hostname
        self.context: ssl.SSLContext | None = None

    # ------------------------------------------------------------------
    def create_context(self) -> ssl.SSLContext:
        """
        Returns an SSLContext configured for the client side of mTLS.

        Key settings:
          • PURPOSE SERVER_AUTH   – we are connecting TO a server
          • minimum_version TLSv1_3
          • load_verify_locations – CA that signed the SERVER's cert
          • load_cert_chain       – OUR cert + key (proves client identity)
          • verify_mode CERT_REQUIRED + check_hostname=True
            → hard-fail if server cert doesn't match server_hostname
        """
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)

        # --- Enforce TLS 1.3 only ---
        context.minimum_version = ssl.TLSVersion.TLSv1_3

        # --- Trust anchor: CA that signed the SERVER's certificate ---
        context.load_verify_locations(cafile=self.cafile)

        # --- Our own identity: client cert + private key (the mTLS part) ---
        context.load_cert_chain(
            certfile=self.client_certfile,
            keyfile=self.client_keyfile,
        )

        # --- Strict server verification ---
        context.verify_mode    = ssl.CERT_REQUIRED
        context.check_hostname = True   # CN / SAN must match server_hostname

        self.context = context
        return context

    # ------------------------------------------------------------------
    # This is optional i may use it futher on the project
    def wrap_socket(self, raw_socket) -> ssl.SSLSocket:
        """Convenience: wrap a raw socket and perform the TLS handshake."""
        ctx = self.context if self.context is not None else self.create_context()
        return ctx.wrap_socket(
            raw_socket,
            server_hostname=self.server_hostname,
        )
