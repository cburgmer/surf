This is a fork of http://code.google.com/p/surfrdf. For a 1:1 git mirror of
the upstream svn go to branch surfrdf
(http://github.com/cburgmer/surf/tree/surfrdf).

Git to SVN
==========
It's not to easy to extract a patch to apply to SVN but the following should
work. Choose the commit you want to create a patch for and run::

    $ git clone git://github.com/cburgmer/surf.git
    $ cd surf
    $ git checkout -b mydiff
    $ git cherry-pick COMMIT_SHA1_ID
    $ sh git-svn-diff.sh
