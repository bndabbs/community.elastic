#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2021, Bradford Dabbs (@bndabbs) <brad@dabbs.io>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: elasticsearch_keystore

short_description: Manage entries in the Elasticsearch keystore

author:
    - Bradford Dabbs (@bndabbs)
version_added: "0.0.1"

description:
  - Add and remove entries in the Elasticsearch keystore.
    Existing entries will not be decrypted, so the module
    will only compares based on the name.

options:
    name:
        description: Keystore value to add or remove.
        required: yes
        type: str
    value:
        description: Data to be stored inside the entry. Required if state=present.
        required: no
        type: str
    state:
        required: no
        default: "present"
        type: str
        choices:
          - present
          - absent
        description: "Whether the entry should exist or not, taking action if the state is different from what is stated."
    force:
        required: no
        default: "no"
        type: bool
        description: "When used with state=present, existing entries with the same name will be replaced."
    create_keystore:
        required: no
        default: "yes"
        type: bool
        description: "Whether to create the keystore if one doesn't already exist."
'''

EXAMPLES = r'''
# Add a new key
- name: Add a key
  community.elastic.elasticsearch_keystore:
    name: es_pass
    value: "{{ vaulted_es_pass }}"

# Add a new key or replace existing key
- name: Add or overwrite key
  community.elastic.elasticsearch_keystore:
    name: es_pass
    value: "{{ vaulted_es_pass }}"
    force: yes

# Delete a key
- name: Delete key
  community.elastic.elasticsearch_keystore:
    name: es_pass
    state: absent

# Don't create keystore
- name: Add a key
  community.elastic.elasticsearch_keystore:
    name: es_pass
    value: "{{ vaulted_es_pass }}"
    create_keystore: no
'''

RETURN = r'''
key:
    description: The original name param that was passed in.
    type: str
    returned: always
    sample: 'es_pass'
message:
    description: Summary of keystore action.
    type: str
    returned: always
    sample: 'Added es_pass to keystore'
'''

from ansible.module_utils.basic import AnsibleModule


def parse_keys(data):
    keys = []
    for line in data.splitlines():
        keys.append({
            'name': line,
        })
    return keys


def run_module():
    module_args = dict(
        name=dict(type='str', required=True),
        value=dict(type='str', required=False, no_log=True),
        state=dict(type='str', default='present', choices=['absent', 'present']),
        force=dict(type='bool', required=False, default=False),
        create_keystore=dict(type='bool', required=False, default=True)
    )

    result = dict(
        changed=False,
        key='',
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ['state', 'present', ['value']]
        ],
    )

    name = module.params['name']
    state = module.params['state']
    force = module.params['force']
    msg = ''
    changed = result['changed']
    value = module.params['value']
    create = module.params['create_keystore']

    try:
        keystore_cmd = module.get_bin_path('elasticsearch-keystore', required=True, opt_dirs=['/usr/share/elasticsearch/bin'])
        rc, current_keys, err = module.run_command("%s list" % (keystore_cmd))
        if rc == 65:
            if create:
                if module.check_mode:
                    changed = True
                else:
                    module.run_command("%s create" % (keystore_cmd), check_rc=True)
            else:
                raise OSError(
                    msg="Failed executing elasticsearch-keystore command.", rc=rc, err=err)
        elif rc != 0:
            raise OSError(rc, err)

        keys = parse_keys(current_keys)
        key_exists = [key for key in keys if key['name'] == name]

        if module.check_mode:
            if key_exists:
                if state == 'present':
                    if not force:
                        msg = "Key %s is already present. Not overwriting as force=no." % (
                            name)
                        changed = False
                if state == 'absent':
                    changed = True
                    msg = "Removed %s from keystore" % (name)
            else:
                if state == 'present':
                    changed = True
                    msg = "Added %s to keystore" % (name)
                if state == 'absent':
                    changed = False
                    msg = "Nothing to do."

            result['key'] = name
            result['message'] = msg
            result['changed'] = changed

            module.exit_json(**result)

        if state == 'present':
            if key_exists:
                if not force:
                    msg = "Key %s is already present. Not overwriting as force=no." % (name)
                    changed = False
                else:
                    module.run_command(
                        "%s add -f -s -x %s" % (keystore_cmd, name), data=value, check_rc=True)
                    changed = True
                    msg = "Added %s to keystore" % (name)
            else:
                module.run_command(
                    "%s add -x %s" % (keystore_cmd, name), data=value, check_rc=True)
                changed = True
                msg = "Added %s to keystore" % (name)

        if state == 'absent':
            if key_exists:
                module.run_command(
                    "%s remove %s" % (keystore_cmd, name), check_rc=True)
                changed = True
                msg = "Removed %s from keystore" % (name)
            else:
                changed = False
                msg = "Nothing to do."

        result['key'] = name
        result['message'] = msg
        result['changed'] = changed

        module.exit_json(**result)
    except OSError as cmd_err:
        module.fail_json(msg='OS Error: %s' % (cmd_err))
    except Exception as excep:
        module.fail_json(msg="Failed with: %s" % (excep))


def main():
    run_module()


if __name__ == '__main__':
    main()
