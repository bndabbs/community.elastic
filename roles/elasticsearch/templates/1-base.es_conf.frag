{% if 'es_' in group_names | string %}
{% if es_version['major'] == 7 and es_version['minor'] >= 9 %}
node.roles:
{% for group in group_names if group.startswith('es_') %}
  - {{ group[3:] }}
{% endfor %}
{% else %}
{% for group in group_names if group.startswith('es_') %}
node.{{ group[3:] }}: true
{% endfor %}
{% endif %}
{% endif %}

{# Check if more than 1 ES node has been configured in the inventory #}
{% if groups['es_master'] | default([]) |length > 1 %}
discovery.seed_hosts:
{% for host in query('inventory_hostnames', 'es_master') | sort %}
  - {{ host }}
{% endfor %}
cluster.initial_master_nodes:
{% for host in query('inventory_hostnames', 'es_master') | sort %}
  - {{ host }}
{% endfor %}
{# If we aren't running multiple nodes we can skip all the logic #}
{# above and declare this will be a single node cluster #}
{% else %}
discovery.type: single-node
{% endif %}

path.data: {{ es_data_dirs | map(attribute='path') | list | to_json }}
path.logs: {{ es_log_dir }}

{% if es_path_repo is defined %}
path.repo: {{ es_path_repo }}
{% endif %}

network.host: {{ es_network_host }}
action.auto_create_index: {{ (es_auto_create_index | join(',') | quote) if (es_auto_create_index is iterable) else es_auto_create_index }}

{% if es_api_basic_auth_username is defined and es_api_basic_auth_password is defined %}
xpack.security.enabled: true
{% endif %}

{% if es_mail_config is defined %}
xpack.notification.email:
  account:
    {{ es_mail_config['account'] }}:
      profile: {{ es_mail_config['profile'] }}
      email_defaults:
        from: {{ es_mail_config['from'] }}
      smtp:
        auth: {{ es_mail_config['require_auth'] }}
        host: {{ es_mail_config['host'] }}
        port: {{ es_mail_config['port'] }}
        {% if es_mail_config['require_auth'] == true -%}
        user: {{ es_mail_config['user'] }}
        password: {{ es_mail_config['pass'] }}
        {%- endif %}
{% endif %}

{% for key, value in es_http.items() %}
{% if value != ''  %}
xpack.security.http.{{ key }}: {{ value }}
{% endif %}
{% endfor %}

{% for key, value in es_transport.items() if value != '' %}
xpack.security.transport.{{ key }}: {{ value }}
{% endfor %}