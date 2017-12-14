- name: create package dir on the executor
  file:
    path: "{{ zuul.executor.work_root }}/packages"
    state: directory
  delegate_to: localhost

- name: send packages to the executor
  synchronize:
    src: "{{ ansible_env.HOME }}/rpmbuild/RPMS/*.rpm"
    dest: "{{ zuul.executor.work_root }}/packages"
    mode: pull
