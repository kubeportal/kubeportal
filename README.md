# kubeportal-integration

## how to use git subtrees:
https://github.com/git/git/blob/master/contrib/subtree/git-subtree.txt

### update changes:

```
git subtree pull --prefix kubeportal-api https://github.com/kubeportal/kubeportal.git fe-api --squash
aka:
make pull-api
```

```
git subtree push --prefix kubeportal-api https://github.com/kubeportal/kubeportal.git fe-api --squash
aka:
make push-api
```

