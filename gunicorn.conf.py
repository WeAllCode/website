# gunicorn settings that ship with every release.
#
# gunicorn reads ./gunicorn.conf.py from its working directory, which on the
# VM is the release dir (WorkingDirectory=/srv/wac/<target>/current), so this
# file is tested on staging before prod. Flags in infra/vm/wac-*.service only
# install from prod releases.

# gunicorn 25.1+ opens a control socket by default under $XDG_RUNTIME_DIR or
# $HOME/.gunicorn. The services run with HOME=/nonexistent, ProtectHome=true
# and ProtectSystem=full, so that path is not writable. We don't use it.
control_socket_disable = True
