# -*- coding: utf-8 -*-
import glob
import os
import time
import yaml
from boto.ec2 import get_region
from boto.ec2.connection import EC2Connection

from revolver.core import env
from revolver import contextmanager as ctx
from revolver import package
from revolver.tool import nginx
from revolver.tool import openvpn

class Settings(dict):
    """
    Settings to read from config.yaml
    """

    DEFAULT_CONFIG = 'config.yaml'

    def __init__(self, filename=None):
        filename = filename or self.DEFAULT_CONFIG
        ret = yaml.load(open(filename))
        dict.__init__(self, ret)

    def __getattr__(self, item):
        return self.get(item, None)


class EC2InstanceCreator(object):

    """
    Instance creator is a class which main goal is to ensure that

    *) there is only one running instance with a given set of properties
    OR
    *) no instances with a given set of properties is running
    """

    def __init__(self, settings=None):
        self.settings_filename = None
        self.reload_settings(settings=settings)

    def reload_settings(self, settings=None):
        """
        (re)-configure instance creator. Useful if you changed your settings
        """
        self.s = settings or Settings(self.settings_filename)
        self.region = get_region(self.s.EC2_REGION)
        self.conn = EC2Connection(self.s.AWS_ACCESS_KEY_ID,
                                  self.s.AWS_SECRET_ACCESS_KEY,
                                  region=self.region)
        self.settings_filename = self.s.filename

    def ensure_instance(self, active=True):
        """
        Ensure that the instance does exist or does not exist (depending on flag)
        """
        instances = self.get_instances()
        active_instance = None
        instances_to_terminate = []

        # find active instance and instances to shut down
        for instance in instances:
            if instance.state in ('pending', 'running', 'stopping', 'stopped'):
                if active_instance is None and active:
                    active_instance = instance
                else:
                    instances_to_terminate.append(instance.id)

        # terminate unneeded instances
        if instances_to_terminate:
            self.conn.terminate_instances(instances_to_terminate)

        # start new instance, if required
        if active and not active_instance:
            self.create_instance()


    def create_instance(self, wait_interval=1):
        """
        Providing there is no active instance, create one
        """
        reservation = self.conn.run_instances(
                        self.s.EC2_AMI,
                        key_name=self.s.EC2_KEYPAIR_NAME,
                        instance_type=self.s.EC2_INSTANCE_TYPE,
                        security_groups=[self.s.EC2_SECURITY_GROUP_NAME, ])
        instance = reservation.instances[0]
        self.conn.create_tags([instance.id, ],
                              {self.s.EC2_INSTANCE_TAG: ''})

        # wait for set up
        while True:
            statuses = self.conn.get_all_instance_status([instance.id, ])
            if statuses and statuses[0].state_name == 'running':
                break
            time.sleep(wait_interval)

        # make use ip
        instance.use_ip(self.s.EC2_ELASTIC_IP)
        return instance.id


    def get_instances(self):
        """
        Return all instances referring to the application
        """
        filters = {'tag:%s' % self.s.EC2_INSTANCE_TAG: ""}
        reservations = self.conn.get_all_instances(filters=filters)
        ret = []
        for reservation in reservations:
            ret += reservation.instances
        return ret



class EC2InstanceConfigurator(object):
    """
    Providing that instance with ubuntu on board is already set up,
    configure installation.

    1) set up openvpn proxy to ease local development with external static
       IP address
    2) set up nginx with arbitrary number of sites
    """

    def __init__(self, settings=None):
        self.settings_filename = None
        self.reload_settings(settings=settings)

    def reload_settings(self, settings=None):
        """
        (re)-configure instance configurator. Useful if you changed your settings
        """
        self.s = settings or Settings(self.settings_filename)

    def configure(self):
        """
        Main method. Perform main configuration
        """
        env.update(host_string=self.s.HOSTNAME, user='ubuntu',
                   disable_known_hosts=True)
        with ctx.hide('output'):
            package.update()
            self.configure_openvpn()
            self.configure_nginx()

    def configure_openvpn(self):
        """
        Configure OpenVPN service
        """
        openvpn.ensure()
        for full_name in glob.glob('openvpn/*.conf'):
            if os.path.isfile(full_name):
                name = os.path.basename(full_name)
                openvpn.config_ensure(name, open(full_name).read())
        for full_name in glob.glob('openvpn/*.key'):
            if os.path.isfile(full_name):
                name = os.path.basename(full_name)
                openvpn.key_ensure(name, open(full_name).read())

    def configure_nginx(self):
        """
        Configure nginx sservice
        """
        nginx.ensure()
        for full_name in glob.glob('nginx/*'):
            if os.path.isfile(full_name):
                name = os.path.basename(full_name)
                nginx.site_ensure(name, open(full_name).read())


if __name__ == '__main__':
    ec2 = EC2InstanceCreator()
    cfg = EC2InstanceConfigurator()
    import IPython
    doc = """
    Welcome to ec2 deployment tool. I've just created two objects just for you.

    ec2: EC2 instance creator
    -------------------------

    # ensure there is exactly one active instance out there
    # (wait util the instance changes its state to "running")
    In [1]: ec2.ensure_instance(active=True)

    # ensure there is no instances out there
    In [1]: ec2.ensure_instance(active=False)


    cfg: Instance configurator
    --------------------------

    # configure instance from scratch
    In [1]: cfg.configure()


    If you changed your config.yaml
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    In [1]: ec2.reload_settings(); cfg.reload_settings()
    """
    IPython.embed(banner2=doc)
