1. Install ansible localy
2. Clone that project and `cd` in it
3. Export enviroments in your terminal
4. Run:
- For initial setup: `ansible-playbook -i inventory/hosts.yaml playbooks/initial_setup.yaml -v`
- For configure user: `ansible-playbook -i inventory/hosts.yaml playbooks/user_setup.yaml -v`
- For security setup or check: `ansible-playbook -i inventory/hosts.yaml playbooks/security_setup.yaml -v`

```
export ANS_VPS_HOST="127.0.0.1"

export ANS_INITIAL_PORT=22
export ANS_INITIAL_USER="root"
export ANS_INITIAL_SSH_PASS="your_secret_passwd"

export ANS_NORMAL_PORT=2220
export ANS_NORMAL_USER="your-username"
export ANS_SSH_PRIVATE_KEY="path/to/private/key"
export ANS_SSH_PUBLIC_KEY="path/to/public/key"
```

TODO:
- add docker config
- add nginx-full config with stream 
- add 3x-ui config
- add headscale config
- add teldrive config
