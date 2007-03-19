#!/usr/bin/env python

# Copyright (c) 2007 Rocco Rutte <pdmef@gmx.net>
# License: MIT <http://www.opensource.org/licenses/mit-license.php>

from mercurial import repo,hg,cmdutil,util,ui,revlog,node
import re
import os

# git branch for hg's default 'HEAD' branch
cfg_master='master'
# silly regex to see if user field has email address
user_re=re.compile('([^<]+) (<[^>]+>)$')
# silly regex to clean out user names
user_clean_re=re.compile('^["]([^"]+)["]$')

def setup_repo(url):
  myui=ui.ui(interactive=False)
  return myui,hg.repository(myui,url)

def fixup_user(user,authors):
  if authors!=None:
    # if we have an authors table, try to get mapping
    # by defaulting to the current value of 'user'
    user=authors.get(user,user)
  name,mail,m='','',user_re.match(user)
  if m==None:
    # if we don't have 'Name <mail>' syntax, use 'user
    # <devnull@localhost>' if use contains no at and
    # 'user <user>' otherwise
    name=user
    if '@' not in user:
      mail='<devnull@localhost>'
    else:
      mail='<%s>' % user
  else:
    # if we have 'Name <mail>' syntax, everything is fine :)
    name,mail=m.group(1),m.group(2)

  # remove any silly quoting from username
  m2=user_clean_re.match(name)
  if m2!=None:
    name=m2.group(1)
  return '%s %s' % (name,mail)

def get_branch(name):
  if name=='HEAD':
    name=cfg_master
  return name

def get_changeset(ui,repo,revision,authors={}):
  node=repo.lookup(revision)
  (manifest,user,(time,timezone),files,desc,extra)=repo.changelog.read(node)
  tz="%+03d%02d" % (-timezone / 3600, ((-timezone % 3600) / 60))
  branch=get_branch(extra.get('branch','master'))
  return (node,manifest,fixup_user(user,authors),(time,tz),files,desc,branch,extra)

def load_cache(filename):
  cache={}
  if not os.path.exists(filename):
    return cache
  f=open(filename,'r')
  l=0
  for line in f.readlines():
    l+=1
    fields=line.split(' ')
    if fields==None or not len(fields)==2 or fields[0][0]!=':':
      sys.stderr.write('Invalid file format in [%s], line %d\n' % (filename,l))
      continue
    # put key:value in cache, key without ^:
    cache[fields[0][1:]]=fields[1].split('\n')[0]
  f.close()
  return cache

def save_cache(filename,cache):
  f=open(filename,'w+')
  map(lambda x: f.write(':%s %s\n' % (str(x),str(cache.get(x)))),cache.keys())
  f.close()