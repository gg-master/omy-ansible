from ansible.plugins.connection import ConnectionBase
from ansible.plugins.loader import connection_loader
from ansible.errors import AnsibleError
import socket


DOCUMENTATION = r"""
    connection: auto_ssh
    short_description: Automatically selects between normal and initial SSH connection
    description:
      - This plugin tries to connect to the "normal" SSH port first.
      - If that fails, it attempts to connect to the "initial" SSH port instead.
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


class Connection(ConnectionBase):
    transport = "auto_ssh"
    has_pipelining = True

    def __init__(self, *args, **kwargs):
        super(Connection, self).__init__(*args, **kwargs)
        self.__connected = False
        self.__wrapped = None

    def __try_connect(self, host: str, port: int | str) -> bool:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        try:
            s.connect((host, int(port)))
            return True
        except Exception:
            return False
        finally:
            s.close()

    def __determine_valid_play_context(self, host: str):
        normal_port = self.get_option("ans_normal_port")
        initial_port = self.get_option("ans_initial_port")

        self._display.vvv(
            f"auto_ssh: attempting connection to {host}, normal_port={normal_port}, initial_port={initial_port}"
        )

        if not host:
            raise AnsibleError("auto_ssh: missing ans_vps_host or ansible_host")

        if initial_port and self.__try_connect(host, initial_port):
            chosen = "initial"
            self._display.vvv(f"auto_ssh: initial port {initial_port} is accessible")
            self._play_context.port = int(initial_port)
            self._play_context.remote_user = self.get_option("ans_initial_user")
            self._play_context.password = self.get_option("ans_initial_ssh_pass")
            self._play_context.private_key_file = None
        elif normal_port and self.__try_connect(host, normal_port):
            chosen = "normal"
            self._display.vvv(f"auto_ssh: normal port {normal_port} is accessible")
            self._play_context.port = int(normal_port)
            self._play_context.remote_user = self.get_option("ans_normal_user")
            self._play_context.password = None
            self._play_context.private_key_file = self.get_option("ans_ssh_private_key")
        else:
            raise AnsibleError(
                f"auto_ssh: cannot connect to {host} on ports {normal_port} or {initial_port}"
            )

        self._display.vvv(
            f"🔐 auto_ssh selected '{chosen}' profile for {host}:{self._play_context.port}"
        )

    def _connect(self):
        return self.connect()

    def connect(self):
        if self.__connected:
            self._display.vvv(
                f"auto_ssh: already connected, returning existing connection"
            )
            return self.__wrapped

        host = self.get_option("ans_vps_host")
        self.__determine_valid_play_context(host)

        try:
            self._play_context.remote_addr = host

            self._display.vvv(
                f"auto_ssh: remote_addr set to: {self._play_context.remote_addr}"
            )
            self._display.vvv(f"auto_ssh: port set to: {self._play_context.port}")
            self._display.vvv(
                f"auto_ssh: remote_user set to: {self._play_context.remote_user}"
            )

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

            # Call _connect instead of connect to avoid potential issues
            if hasattr(ssh_plugin, "_connect"):
                ssh_plugin._connect()
            elif hasattr(ssh_plugin, "connect"):
                ssh_plugin.connect()
            else:
                raise AnsibleError("SSH plugin does not have connect method")

            self.__wrapped = ssh_plugin
            self.__connected = True
            return self.__wrapped
        except Exception as e:
            raise AnsibleError(
                f"auto_ssh: failed to create SSH connection to {host}:{self._play_context.port} - {str(e)}"
            )

    def exec_command(self, cmd, in_data=None, sudoable=True):
        if not self.__connected or self.__wrapped is None:
            self._display.vvv("auto_ssh: establishing connection for exec_command")
            self.connect()
        return self.__wrapped.exec_command(cmd, in_data, sudoable)

    def put_file(self, in_path, out_path):
        if not self.__connected or self.__wrapped is None:
            self._display.vvv("auto_ssh: establishing connection for put_file")
            self.connect()
        return self.__wrapped.put_file(in_path, out_path)

    def fetch_file(self, in_path, out_path):
        if not self.__connected or self.__wrapped is None:
            self._display.vvv("auto_ssh: establishing connection for fetch_file")
            self.connect()
        return self.__wrapped.fetch_file(in_path, out_path)

    def close(self):
        if self.__wrapped:
            try:
                self.__wrapped.close()
            except Exception:
                pass
        self.__wrapped = None
        self.__connected = False
