Permissions are defined as read (r), write (w), execute (x) for user, group, and others. Represented as `rwxr-xr--` or numerically as `754`. r, w, x = 4, 2, 1; +, -, = to add revoke, set permissions. SUID sets user id, SGIG - sets group. Example: chmod ug+x NAME (SUID and SGID to add execute)

Sticky Bit is mostly a directory permission to restrict deletion to owner or root and is represented by the letter t. Example: chmod +t /path/to/dir or chmod 1777 /path/to/dir

chown to change user, chgrp: group

umask to check default permissions
umask 444 to set default permissions to read-only