# Installation:

```
pip3 install pipenv
export PIPENV_VENV_IN_PROJECT=1
pipenv --three
pipenv install --dev
```

# Configuration:

**In console**:
```
export DEPLOY_IP={ip}
export DEPLOY_KEY={~/.ssh/private_key}
export DEPLOY_PROJECT_ALIAS={alias}
```

**Edit variables in deploy/services/project.py**.

# Deploy:

```
pipenv shell
cd deploy
fab configure{:service=service_type_name}
```

# Update already deployed:

```
pipenv shell
cd deploy
fab update_project
```