odoo --no-http --stop-after-init -c /etc/odoo/odoo.conf --db_host=postgres -w password -r odoo  -d osh -u sh_subscription && kill -HUP 1

curl -X POST -H "Authorization: Bearer J9wJY0YdQCPBAZwV8ql3bUMkWJs5nQzYu9wkdCZYvYrT96ymLDwCaBkA8negwqQ2" -H "Content-Type: application/json" -d '{
  "name": "31-CURL",
  "server_type": "cpx31",
  "location": "sin",
  "image": "ubuntu-22.04",
  "ssh_keys": [],
  "networks": [],
  "user_data": "",
  "labels": {
    "created_by": "curl_test",
    "environment": "testing"
  },
  "start_after_create": true
}' "https://api.hetzner.cloud/v1/servers"