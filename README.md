# What is this?
This is a simple buildbot (www.buildbot.net) configuration for use with CRYENGINE (www.cryengine.com) projects.
It assumes that the code and dependencies are hosted in git repositories.

This setup can be used to can compile the current state of a branch, alternatively, it can be used to 'try' a change.
That is, to compile a change in different configurations and report and problems encountered.
As such developers can make sure they won't break compilation before they submit their code.

By using a repository hook is used to check compilation status, developers can be required to ensure that their code
compiles before they are allowed to push their changes.
A git hook (written in Pyton) is provided for this purpose.

There is a little setup involved, as described below.


## Configuration
The file 'common_files/buildbot_config.json' lists all configurations that can be built, and those that must be built.


## Files for the client
The 'buildbot_config.json' file must be in the repository root.

In order to try a change using buildbot, commit all changes then run 'trychange.py', passing it the repository root
in the '--repopath' parameter.
Depending on individual circumstances it may be preferable to check this directory into the repository as well,
and hard-code the repopath parameter to '.'.

This trychange.py script requires that buildbot be installed on the developer machine and accessible to the version
of Python used. It would also be possible to freeze buildbot into an executable and use that, but for simplicity that
approach is not taken here.


## Files for the repository host
The 'update.py' script must be in the .git/hooks directory on the repository host (and renamed to remove the '.py'
extension). It requires the 'requests' package from PIP.

This hook also requires that the 'buildbot_config.json' file be adjacent to it in the .git/hooks directory.


## Files for the buildbot master
The buildbot master must have buildbot itself installed. This setup was tested with buildbot 0.9, and is expected
to be compatible with later updates owing to its simplicity.

After creating the master (as per the buildbot documentation) the master.cfg and cryengine.py files must be placed
in the root of the master directory.
