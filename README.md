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
```


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
ansible-playbook playbooks/manage_software/nginx.yaml
```
For uninstall nginx run:
``` bash
ansible-playbook playbooks/manage_software/nginx.yaml -e "{uninstall: true}"
```

You can also use ansible-vault for `secrets.yaml`.

### TODO:
- add 3x-ui config
- add headscale config
- add teldrive config
