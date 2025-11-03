Target VPS OS: Ubuntu 22.04+

1. Install ansible localy
2. Clone that project and `cd` in it
3. Add your hosts in `inventory/hosts.yaml`
3. Add `secrets.yaml` file in root of project
4. Run:
- For initial setup: `ansible-playbook playbooks/server_setup.yaml`
- For configure user: `ansible-playbook playbooks/manage_users/add_user.yaml`
- For security setup or check: `ansible-playbook playbooks/manage_software/security.yaml`

example of `secrets.yaml`
``` 
host1.example.com:
  host: "127.0.0.1"
  initial_port: 22
  initial_user: root
  initial_ssh_pass: "yuorSercretPassword"
  normal_port: 2220
  normal_user: "yourUser"
  ssh_private_key: "/path/to/.ssh/privateKey"
  ssh_public_key: "/path/to/.ssh/publicKey.pub"

  domains:
    - xui_domain: yourbestdomain.example.com
```


### 3x-ui

Before installation, you need to get a domain name for convenient further configuration and use. You can get a domain for free and easily [here](https://freedomain.one/).

Also, before installing, check the panel configuration in `./inventory/configs/3x_ui.yaml`.

For install 3x-ui simply run:
```bash
ansible-playbook playbooks/manage_software/3x_ui/setup.yaml
```

For uninstall 3x-ui run:
```bash
ansible-playbook playbooks/manage_software/3x_ui/setup.yaml -e "{uninstall: true}"
```

After installation, default traffic routing will be configured `from 443 to anti_probing_port`. You need to create the first inbound on this port. If you are adding other domain names, you must also add an entry to the nginx stream.


### Docker

For install docker run:
``` bash
ansible-playbook playbooks/manage_software/docker.yaml
```

For uninstall docker run:
``` bash
ansible-playbook playbooks/manage_software/docker.yaml -e "{uninstall: true}"
```


### Nginx

For install nginx run:
``` bash
ansible-playbook playbooks/manage_software/nginx/setup.yaml
```

For uninstall nginx run:
``` bash
ansible-playbook playbooks/manage_software/nginx/setup.yaml -e "{uninstall: true}"
```

For add simple proxy nginx config run:
``` bash
ansible-playbook playbooks/manage_software/nginx/simple_proxy.yaml -e "{domain: <your_domain>, http_port: <http_port>, http_proxy_port: <http_proxy_port>}"
```

For configure SSL certs for nginx config run:
``` bash
ansible-playbook playbooks/manage_software/nginx/ssl.yaml -e "{domain: <your_domain>, https_port: <https_port>}"
```

For configure new stream record run:
``` bash
ansible-playbook playbooks/manage_software/nginx/stream.yaml -e "{domain: <your_domain>, https_port: <https_port>}"
```

You can also use ansible-vault for `secrets.yaml`.

### TODO:
- add headscale config
- add teldrive config
