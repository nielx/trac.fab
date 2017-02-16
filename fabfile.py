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

from fabric.api import env
from fabric.context_managers import prefix
from fabric.contrib.files import exists
from fabric.decorators import task
from fabric.operations import require, sudo

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


@task
def production():
    """Work on the staging environment"""
    env.environment = 'production'
    env.project_path = "/srv/trac/dev.haiku-os.org/"
    env.apache_server_name = "dev.haiku-os.org"
    env.python_path = "/srv/trac/dev-env"

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

    with prefix('source %(python_path)s/bin/activate' % env):
        sudo('pip install -U psycopg2')

@task
def install_trac(version):
    """Install/upgrade Trac on the application-specific python environment"""
    require('environment', provided_by=[staging, production])

    with prefix('source %(python_path)s/bin/activate' % env):
        sudo('pip install -U Trac==' + version)
