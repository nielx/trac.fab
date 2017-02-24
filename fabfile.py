#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012 Zuza Software Foundation
#
# NOTE: this file is heavily modified fabfile from Pootle for use on Haiku
# servers
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.
import time
from fabric.api import env
from fabric.colors import red
from fabric.context_managers import prefix, cd
from fabric.contrib.console import confirm
from fabric.contrib.files import exists, upload_template
from fabric.decorators import task
from fabric.operations import require, sudo, run, put

#
# Settings
#

env.hosts = ['vmdev.haiku-os.org']
env.python = '/usr/bin/python2.7'

#
# Set up the environment
#
@task
def staging():
    """Work on the staging environment"""
    env.environment = 'staging'
    env.project_path = "/srv/trac/dev-next.haiku-os.org/"
    env.apache_server_name = "dev-next.haiku-os.org"
    env.python_path = "/srv/trac/dev-next-env"
    env.database = "trac-test"


@task
def production():
    """Work on the staging environment"""
    env.environment = 'production'
    env.project_path = "/srv/trac/dev.haiku-os.org/"
    env.apache_server_name = "dev.haiku-os.org"
    env.python_path = "/srv/trac/dev-env"
    env.database = "trac"

@task
def bootstrap_python():
    """Set up a fresh instance ready to be further deployed and activated"""
    require('environment', provided_by=[staging, production])

    if (exists('%(python_path)s' % env)):
        print ('The staging environment already exists at %(python_path)s. Please clean it up manually and try again.'
            % env)
        return

    # Set up directory
    sudo('mkdir %(python_path)s' % env)

    # Set up python virtual env
    sudo('virtualenv -p %(python)s --no-site-packages %(python_path)s' % env)

@task
def install_trac(version):
    """Install/upgrade Trac on the application-specific python environment"""
    require('environment', provided_by=[staging, production])

    try:
        put('requirements/' + version, "/tmp/requirements.txt")
    except:
        print(red("There is no support for this version of Trac. Please provide a requirements file"))
        return

    with prefix('source %(python_path)s/bin/activate' % env):
        sudo('pip install -r /tmp/requirements.txt')

@task
def deploy():
    with prefix('source %(python_path)s/bin/activate' % env):
        sudo('trac-admin %(project_path)s upgrade' % env)
        sudo('trac-admin %(project_path)s wiki upgrade' % env)
        sudo('trac-admin %(project_path)s deploy %(project_path)s/htdocs-static' % env)

    sudo('/sbin/service apache2 reload')

@task
def backup():
    """Make a backup of the project dir and the database in the home dir"""
    require('environment', provided_by=[staging, production])

    env.timestring = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    with prefix('source %(python_path)s/bin/activate' % env):
        sudo('trac-admin %(project_path)s hotcopy ~/%(timestring)s' % env)
        with cd("~"):
            sudo('tar -cvjf %(apache_server_name)s-backup-%(timestring)s.tar.bz2 %(timestring)s' % env)
            sudo('rm -rf %(timestring)s' % env)

@task
def copy_production_to_environment():
    """Copy the production data to the staging environment"""
    require('environment', provided_by=[staging, production])

    if env.environment == "production":
        print(red("You cannot run this command on the production environment"))
        return

    if not exists('~/.pgpass'):
        print(
        "In order to perform these operations, you will need to store the password of the database in a .pgpass file")
        print("See: http://www.postgresql.org/docs/current/static/libpq-pgpass.html")
        print("You will need it for the trac and the baron account")
        return

    confirm("This will destroy all data of the $(environment)s environment. Do you want to continue?" % env,
            default=False)

    # set up env for staging
    print(red("Deleting current data in %(environment)s" % env))
    run("dropdb -U trac %(database)s" % env, warn_only=True)
    sudo("rm -rf %(project_path)s" % env)

    # start a hotcopy
    with prefix('source %(python_path)s/bin/activate' % env):
        sudo('trac-admin /srv/trac/dev.haiku-os.org/ hotcopy %(project_path)s' % env)

    # we do not use the dump that is created by trac hotcopy, since it tries to restore in the original database
    run("createdb -U baron -O trac %(database)s" % env)
    run("pg_dump -U trac trac | psql -U trac %(database)s" % env)

    # update the wsgi file
    upload_template('trac.wsgi',
                    '%(project_path)s/apache' % env,
                    context=env, use_sudo=True)

    # change the database in trac.ini
    with cd("%(project_path)s/conf" % env):
        sudo("sed - i 's/\(^database.*\/\)\(trac\)/\1%(database)/g' trac.ini" % env)

    # set up proper permissions
    with cd(env.project_path):
        sudo("chown -R wwwrun:www conf")
        sudo("chown -R wwwrun:www db")
        sudo("chown -R wwwrun:www log")


@task
def enable_environment():
    """Enable an environment"""
    require('environment', provided_by=[staging, production])

    # Update the configuration files
    upload_template('virtualhost.conf',
                    '/etc/apache2/vhosts.d/%(apache_server_name)s-ssl.conf' % env,
                    context=env, use_sudo=True)

    sudo('/sbin/service apache2 reload')


@task
def disable_environment(destination_domain):
    """Disable an environment and redirect to a URL"""
    require('environment', provided_by=[staging, production])

    env.destination_domain = destination_domain

    # Update the configuration files
    upload_template('virtualhost-disabled.conf',
                    '/etc/apache2/vhosts.d/%(apache_server_name)-ssl.conf' % env,
                    context=env, use_sudo=True)

    sudo('/sbin/service apache2 reload')
