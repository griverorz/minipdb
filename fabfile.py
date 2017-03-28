# Imports
from fabric.api import cd, env, lcd, put, local, sudo, run
from fabric.contrib.files import exists
from config import Prod
import os

# Config
PATH = os.path.abspath(".")
local_app_dir = os.path.join(PATH, ".")
local_config_dir = os.path.join(local_app_dir, 'config')

remote_app_dir = '/home/www'
remote_git_dir = '/home/git'
remote_flask_dir = os.path.join(remote_app_dir, 'minipdb')
remote_nginx_dir = '/etc/nginx/sites-enabled'
remote_supervisor_dir = '/etc/supervisor/conf.d'

env.hosts = [Prod.APP_HOST]
env.user = 'ubuntu'
env.key_filename = Prod.APP_KEY

# Tasks


def install_requirements():
    """ Install required packages. """
    sudo('apt-get update')
    sudo('apt-get install -y nginx supervisor')
    sudo('apt-get install -y python3 python3-pip python3-dev python-virtualenv')
    sudo('apt-get install -y git')
    sudo('apt-get install -y postgresql-client postgresql-contrib')


def install_flask():
    """
    1. Create project directories
    2. Create and activate a virtualenv
    3. Copy Flask files to remote host
    """
    if exists(remote_app_dir) is False:
        sudo('mkdir ' + remote_app_dir)
        sudo('chown -R {}:{} {}'.format(env.user, env.user, remote_app_dir))
    if exists(remote_flask_dir) is False:
        run('mkdir ' + remote_flask_dir)
    with lcd(local_app_dir):
        with cd(remote_app_dir):
            run('virtualenv -p python3 env')
            run('source env/bin/activate')
        with cd(remote_flask_dir):
            put('requirements.txt', '.', use_sudo=False)
            put('credentials.json', '.', use_sudo=False)
            run(remote_app_dir + "/env/bin/pip3 -q install pip --upgrade")
            run(remote_app_dir + "/env/bin/pip3 -q install gunicorn")
            run(remote_app_dir + "/env/bin/pip3 -q install -r requirements.txt")


def configure_nginx():
    """
    1. Remove default nginx config file
    2. Create new config file
    3. Setup new symbolic link
    4. Copy local config to remote config
    5. Restart nginx
    """
    sudo('/etc/init.d/nginx start')
    if exists('/etc/nginx/sites-enabled/default'):
        sudo('rm /etc/nginx/sites-enabled/default')
    if exists('/etc/nginx/sites-enabled/minipdb') is False:
        sudo('touch /etc/nginx/sites-available/minipdb')
        sudo('ln -s /etc/nginx/sites-available/minipdb' +
             ' /etc/nginx/sites-enabled/minipdb')
    with lcd(local_config_dir):
        with cd(remote_nginx_dir):
            put('./minipdb', './', use_sudo=True)
    sudo('/etc/init.d/nginx restart')


def configure_supervisor():
    """
    1. Create new supervisor config file
    2. Copy local config to remote config
    3. Register new command
    """
    if exists('/etc/supervisor/conf.d/minipdb.conf') is False:
        with lcd(local_config_dir):
            with cd(remote_supervisor_dir):
                put('./minipdb.conf', './', use_sudo=True)
                sudo('supervisorctl reread')
                sudo('supervisorctl update')


def configure_git():
    """
    1. Setup bare Git repo
    2. Create post-receive hook
    """
    if exists(remote_git_dir) is False:
        sudo('mkdir ' + remote_git_dir)
        with cd(remote_git_dir):
            sudo('mkdir minipdb.git')
            with cd('minipdb.git'):
                sudo('git init --bare')
                with lcd(local_config_dir):
                    with cd('hooks'):
                        put('./post-receive', './', use_sudo=True)
                        sudo('chmod +x post-receive')
        with cd(remote_git_dir):
            sudo('chown -R {} minipdb.git'.format(env.user))
        with lcd(local_app_dir):
            gitr = remote_git_dir + "/minipdb.git"
            local("git remote set-url production production:{}".format(gitr))


def run_app():
    """ Run the app! """
    with cd(remote_flask_dir):
        sudo('supervisorctl start minipdb')


def copy_code():
    """ Move the code to the remote """
    with lcd(local_app_dir):
        local('git push production master')


def deploy():
    """
    1. Copy new Flask files
    2. Restart gunicorn via supervisor
    """
    with lcd(local_app_dir):
        local('git push production master')
        sudo('supervisorctl restart minipdb')


def rollback():
    """
    1. Quick rollback in case of error
    2. Restart gunicorn via supervisor
    """
    with lcd(local_app_dir):
        local('git revert HEAD~1')
        local('git push production master')
        sudo('supervisorctl restart minipdb')


def status():
    """ Is our app live? """
    sudo('supervisorctl status')


def create():
    """ Do all the things! """
    install_requirements()
    install_flask()
    configure_nginx()
    configure_git()
    configure_supervisor()
    copy_code()
