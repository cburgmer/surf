This is a fork of http://code.google.com/p/surfrdf. For a 1:1 git mirror of
the upstream svn go to branch surfrdf
(http://github.com/cburgmer/surf/tree/surfrdf).

Install
=======
You can install this fork with pip::

    $ pip install -e git+git://github.com/cburgmer/surf.git#egg=surf

Sadly PIP can't find "sub-packages" due to bug
http://bitbucket.org/ianb/pip/issue/2/allow-installing-packages-with-non-root.
So you need to install the plugins manually.

Git to SVN
==========
It's not too easy to extract a patch to apply to SVN but the following should
work. Choose the commit you want to create a patch for and run::

    $ git clone git://github.com/cburgmer/surf.git
    $ cd surf
    $ git checkout -b mydiff surfrdf
    $ git cherry-pick COMMIT_SHA1_ID
    $ wget https://github.com/cburgmer/surf/raw/master/git-svn-diff.sh
    $ sh git-svn-diff.sh
