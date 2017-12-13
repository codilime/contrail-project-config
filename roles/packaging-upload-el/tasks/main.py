- name: create package dir on the executor
  file:
    path: "{{ executor_package_dir }}"
    state: directory
  delegate_to: localhost

- name: send packages to the executor
  synchronize:
    src: "{{ worker_package_dir }}/*.rpm"
    dest: "{{ executor_package_dir }}"
    mode: pull
