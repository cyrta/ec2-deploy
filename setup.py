# -*- coding: utf-8 -*-
from distutils.core import setup

setup(
    name='ec2-deploy',
    version='0.1',
    py_modules=['ec2_deploy', ],
    url='http://github.com/imankulov/ec2-deploy',
    license='BSD',
    author='Roman Imankulov',
    author_email='roman.imankulov@gmail.com',
    description='My own ec2 deployment utility. Used for fast setup of '
                'semi-persistent development installation',
)
