# MAVROS plugin config (optional)

`mavros_pixhawk.launch.py` starts MAVROS with its default plugin set, which
is enough for RC passthrough, state, battery, and GPS topics used by this
project.

If you later want to trim which plugins load (lower CPU on the Pi, or to
silence plugins for hardware you don't have), drop a `px4_pluginlists.yaml`
in this directory and pass it as an extra parameter file to the `mavros_node`
in `mavros_pixhawk.launch.py`. See the MAVROS docs for the allowlist/denylist
format: https://github.com/mavlink/mavros
