#!/bin/bash
#
# git-svn-diff originally by (http://mojodna.net/2009/02/24/my-work-git-workflow.html)
# modified by mike@mikepearce.net (https://gist.github.com/582239)
# cropped for simple usecase without git-svn available by cburgmer@ira.uka.de
#
# Generate an SVN-compatible diff against the tip of the tracking branch
git diff --no-prefix origin/surfrdf |
sed -e "s/^+++ .*/&     (working copy)/" -e "s/^--- .*/&        (revision )/" \
-e "s/^diff --git [^[:space:]]*/Index:/" \
-e "s/^index.*/===================================================================/"
