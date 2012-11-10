ec2-deploy
==========

Personal utility to set up development installation from Ubuntu server.
It creates a new instance on Amazon EC2, and then installs openvpn and nginx
there.

Don't expect too much from it, it's unlikely you find it useful for your needs.

But just in case, if you decided to try it out.

0. Open up the `source code
   <https://github.com/imankulov/ec2-deploy/blob/master/ec2_deploy.py>`_ to make
   sure it looks like what you're searching for.
1. copy :file:`config.yaml.sample` to :file:`config.yaml` and edit the file
2. install requirements

    .. code-block:: console

        pip install -r requirements.pip

3. run the main script, you get the IPython shell with help

    .. code-block:: console

        python ./ec2_deploy.py

Drop some files to :file:`nginx` and :file:`openvpn` directories to make
installation more or less useful.
