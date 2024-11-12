=========
EasyCloud
=========

.. image:: https://img.shields.io/pypi/v/easycloud.svg
        :target: https://pypi.python.org/pypi/easycloud

.. image:: https://img.shields.io/travis/alaeddine-13/easycloud.svg
        :target: https://travis-ci.com/alaeddine-13/easycloud

.. image:: https://readthedocs.org/projects/easycloud/badge/?version=latest
        :target: https://easycloud.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status

Create resource on the cloud with natural language


Features
--------

* Natural language-based resource creation
* Support for AWS cloud resources (S3 buckets, EC2 instances, etc.)
* Automated handling of dependencies

Usage Examples
--------------

- Create an S3 bucket that allows public upload of images:

.. code-block:: shell

    easycloud --prompt "Create an S3 bucket named 'my-public-bucket' that allows public uploads of images"

- Launch an EC2 instance with a specified AMI and security group:

.. code-block:: shell

    easycloud --prompt "Launch an EC2 instance using the latest Amazon Linux AMI in the default VPC, with the security group 'my-security-group'"

- Create a DynamoDB table with primary key and sort key:

.. code-block:: shell

    easycloud --prompt "Create a DynamoDB table named 'my-table' with a primary key 'id' of type string and a sort key 'created_at' of type number"

- Set up an RDS instance for MySQL database:

.. code-block:: shell

    easycloud --prompt "Set up an RDS instance for MySQL database with the instance class 'db.t2.micro' and allocate 5 GB of storage"
