from dataclasses import dataclass
from typing import Optional
from ansible.plugins.connection import ConnectionBase
from ansible.plugins.loader import connection_loader
from ansible.errors import AnsibleError
import socket


DOCUMENTATION = r"""
    connection: auto_ssh
    short_description: Automatically selects between normal and initial SSH connection
    description:
      - This plugin tries to connect to the "initial" SSH port first.
      - If that fails, it attempts to connect to the "normal" SSH port.
      - It wraps the standard SSH connection plugin.
    author: "gg-master"
    options:
      ans_vps_host:
        description: The target host
        type: str
        vars:
          - name: ans_vps_host
      ans_normal_port:
        description: Normal SSH port
        type: int
        vars:
          - name: ans_normal_port
      ans_normal_user:
        description: Normal SSH user
        type: str
        vars:
          - name: ans_normal_user
      ans_initial_port:
        description: Initial SSH port
        type: int
        vars:
          - name: ans_initial_port
      ans_initial_user:
        description: Initial SSH user
        type: str
        vars:
          - name: ans_initial_user
      ans_initial_ssh_pass:
        description: Initial SSH password
        type: str
        vars:
          - name: ans_initial_ssh_pass
      ans_ssh_private_key:
        description: Path to SSH private key
        type: str
        vars:
          - name: ans_ssh_private_key
"""


@dataclass
class ConnectionConfig:
    type: str
    port: int
    remote_user: str
    password: Optional[str]
    private_key_file: Optional[str]


class Connection(ConnectionBase):
    transport = "auto_ssh"
    has_pipelining = True

    _connection_cache = {}

    def __init__(self, *args, **kwargs):
        super(Connection, self).__init__(*args, **kwargs)
        self.__wrapped = None
        self.__connected = False

    def __determine_valid_play_context(self, host: str):
        normal_port = self.get_option("ans_normal_port")
        initial_port = self.get_option("ans_initial_port")

        if not host:
            raise AnsibleError("auto_ssh: missing ans_vps_host or ansible_host")

        initial_conn = ConnectionConfig(
            "initial",
            int(initial_port),
            self.get_option("ans_initial_user"),
            self.get_option("ans_initial_ssh_pass"),
            None,
        )
        normal_conn = ConnectionConfig(
            "normal",
            int(normal_port),
            self.get_option("ans_normal_user"),
            None,
            self.get_option("ans_ssh_private_key"),
        )
        for c in [initial_conn, normal_conn]:
            if self.__test_ssh_connection(host, c):
                return

        raise AnsibleError(
            f"auto_ssh: failed all attempts of SSH connecting to {host}."
        )

    def __test_ssh_connection(self, host: str, config: ConnectionConfig) -> bool:
        self._display.vv(f"auto_ssh: {config.type} connection to {host}:{config.port}")
        try:
            with socket.create_connection((host, config.port), timeout=1) as s:
                banner = s.recv(64)
                if not banner.startswith(b"SSH-"):
                    return False
        except Exception:
            return False

        self._play_context.port = config.port
        self._play_context.remote_user = config.remote_user
        self._play_context.password = config.password
        self._play_context.private_key_file = config.private_key_file
        return True

    def _connect(self):
        host = self.get_option("ans_vps_host")
        if host in Connection._connection_cache:
            self._display.vv(f"Reusing cached connection for {host}")
            self.__wrapped = Connection._connection_cache[host]
            self.__connected = True
            return self.__wrapped

        self.__determine_valid_play_context(host)

        try:
            self._play_context.remote_addr = host
            ssh_plugin = connection_loader.get("ssh", self._play_context, None)

            if hasattr(ssh_plugin, "set_options"):
                options_override = dict(self._options) if self._options else {}
                options_override.update(
                    {
                        "remote_addr": host,
                        "ansible_host": host,
                        "ansible_port": self._play_context.port,
                        "ansible_ssh_port": self._play_context.port,
                        "ansible_user": self._play_context.remote_user,
                        "ansible_ssh_user": self._play_context.remote_user,
                    }
                )

                if self._play_context.private_key_file:
                    options_override.update(
                        {
                            "ansible_ssh_private_key_file": self._play_context.private_key_file,
                            "ansible_private_key_file": self._play_context.private_key_file,
                        }
                    )

                if self._play_context.password:
                    options_override.update(
                        {
                            "ansible_password": self._play_context.password,
                            "ansible_ssh_pass": self._play_context.password,
                        }
                    )

                ssh_plugin.set_options(var_options=options_override)

            self._display.vv("auto_ssh: establish SSH connection")
            ssh_plugin._connect()
            self.__connected = True
            self.__wrapped = ssh_plugin

            Connection._connection_cache[host] = self.__wrapped
            return self.__wrapped
        except Exception as e:
            raise AnsibleError(
                f"auto_ssh: failed to create SSH connection to {host}:{self._play_context.port} - {str(e)}"
            )

    def exec_command(self, cmd, in_data=None, sudoable=True):
        if not self.__connected or self.__wrapped is None:
            self._display.vv("auto_ssh: establishing connection for exec_command")
            self._connect()
        return self.__wrapped.exec_command(cmd, in_data, sudoable)

    def put_file(self, in_path, out_path):
        if not self.__connected or self.__wrapped is None:
            self._display.vv("auto_ssh: establishing connection for put_file")
            self._connect()
        return self.__wrapped.put_file(in_path, out_path)

    def fetch_file(self, in_path, out_path):
        if not self.__connected or self.__wrapped is None:
            self._display.vv("auto_ssh: establishing connection for fetch_file")
            self._connect()
        return self.__wrapped.fetch_file(in_path, out_path)

    def close(self):
        if self.__wrapped:
            try:
                self.__wrapped.close()
            except Exception:
                pass
        self.__wrapped = None
        self.__connected = False

        host = self.get_option("ans_vps_host")
        if host in Connection._connection_cache:
            del Connection._connection_cache[host]
