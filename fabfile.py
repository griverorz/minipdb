# Imports
from fabric.api import cd, env, lcd, put, local, sudo, run
from fabric.contrib.files import exists
from wsgi.config import Prod
import os

# Config
PATH = os.path.abspath(".")
local_app_dir = os.path.join(PATH, ".")
local_config_dir = os.path.join(local_app_dir, 'config')

remote_app_dir = '/home/www'
remote_git_dir = '/home/git'
remote_flask_dir = os.path.join(remote_app_dir, 'minipdb')
remote_nginx_dir = '/etc/nginx/sites-enabled'
remote_circus_dir = '/etc/circus'

env.hosts = [Prod.APP_HOST]
env.user = 'ubuntu'
env.key_filename = Prod.APP_KEY

# Tasks


def install_requirements():
    """ Install required packages. """
    sudo('apt-get update')
    sudo('apt-get install -y nginx circus')
    sudo('apt-get install -y python3 python3-pip python3-dev python-virtualenv')
    sudo('apt-get install -y r-base unixodbc')
    sudo('apt-get install -y git')
    sudo('apt-get install -y postgresql-client postgresql-contrib')
    sudo('apt-get install -y install postgresql-server-dev-9.5')


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
            run(remote_app_dir + "/env/bin/pip3 -q install pip --upgrade")
            run(remote_app_dir + "/env/bin/pip3 -q install gunicorn")
            run(remote_app_dir + "/env/bin/pip3 -q install -r requirements.txt")
            if exists('./wsgi') is False:
                run('mkdir ' + remote_flask_dir + '/wsgi')
                put('wsgi/config.py', 'wsgi/.', use_sudo=False)


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


def configure_circus():
    """
    1. Create new circus config file
    2. Copy local config to remote config
    3. Register new command
    """
    local("pwd")
    put('minipdb.ini', remote_circus_dir, use_sudo=True)
    with cd(remote_circus_dir):
        sudo('circusd --daemon minipdb.ini')
        sudo('circusctl start')


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
        sudo('circusctl start minipdb')


def copy_code():
    """ Move the code to the remote """
    with lcd(local_app_dir):
        local('git push production master')


def deploy():
    """
    1. Copy new Flask files
    2. Restart gunicorn via circus
    """
    with lcd(local_app_dir):
        local('git push production master')
        sudo('circusctl restart minipdb')


def rollback():
    """
    1. Quick rollback in case of error
    2. Restart gunicorn via circus
    """
    with lcd(local_app_dir):
        local('git revert HEAD~1')
        local('git push production master')
        sudo('circusctl restart minipdb')


def status():
    """ Is our app live? """
    sudo('circusctl status')


def create():
    """ Do all the things! """
    install_requirements()
    install_flask()
    configure_nginx()
    configure_git()
    configure_circus()
    copy_code()
