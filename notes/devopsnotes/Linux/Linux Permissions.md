Permissions are defined as read (r), write (w), execute (x) for user, group, and others. Represented as `rwxr-xr--` or numerically as `754`. r, w, x = 4, 2, 1; +, -, = to add revoke, set permissions. Example: chmod ug+x NAME

chown to change user, chgrp: group

umask to check default permissions
umask 444 to set default permissions to read-only